"""
Checkpoint-Based Task Resumption System

Enables tasks to:
1. Save intermediate state (checkpoints)
2. Resume from last checkpoint on failure
3. Migrate to different nodes with state preservation
"""

import os
import json
import pickle
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum


class CheckpointStrategy(str, Enum):
    """Checkpoint strategies"""
    NONE = "none"           # No checkpointing
    TIME_BASED = "time"     # Checkpoint every N seconds
    PROGRESS_BASED = "progress"  # Checkpoint at specific % milestones
    MANUAL = "manual"       # Job explicitly requests checkpoint
    AUTOMATIC = "automatic" # Smart checkpointing based on job type


@dataclass
class Checkpoint:
    """
    Checkpoint data structure

    Contains all state needed to resume a task
    """
    job_id: str
    checkpoint_id: str  # Unique checkpoint identifier
    timestamp: float
    progress: float  # 0.0 to 1.0

    # Execution state
    state: Dict[str, Any]  # Arbitrary state data
    completed_steps: list  # List of completed step IDs
    current_step: str      # Current step being executed

    # Metadata
    node_id: str           # Node that created checkpoint
    attempt: int           # Attempt number (for retry tracking)

    # Data references
    input_data: Dict[str, Any]   # Original input
    intermediate_results: Dict[str, Any]  # Partial results

    # Versioning
    checkpoint_version: str = "1.0"


class CheckpointManager:
    """
    Manages checkpoints for task resumption

    Features:
    - Periodic checkpointing
    - Progress-based checkpointing
    - Checkpoint storage and retrieval
    - Cross-node checkpoint migration
    """

    def __init__(self,
                 node_id: str,
                 checkpoint_dir: str = "./data/checkpoints",
                 strategy: CheckpointStrategy = CheckpointStrategy.TIME_BASED,
                 checkpoint_interval: float = 30.0):  # 30 seconds

        self.node_id = node_id
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.strategy = strategy
        self.checkpoint_interval = checkpoint_interval

        # Active checkpoints (job_id -> Checkpoint)
        self.checkpoints: Dict[str, Checkpoint] = {}

        # Last checkpoint time per job
        self.last_checkpoint_time: Dict[str, float] = {}

        print(f"[CHECKPOINT] Initialized ({strategy}, interval={checkpoint_interval}s)")

    def should_checkpoint(self, job_id: str, progress: float) -> bool:
        """
        Determine if checkpoint should be created

        Args:
            job_id: Job identifier
            progress: Current progress (0.0 to 1.0)

        Returns:
            True if checkpoint should be created
        """
        if self.strategy == CheckpointStrategy.NONE:
            return False

        if self.strategy == CheckpointStrategy.MANUAL:
            # Only checkpoint when explicitly requested
            return False

        if self.strategy == CheckpointStrategy.TIME_BASED:
            # Checkpoint every N seconds
            last_time = self.last_checkpoint_time.get(job_id, 0)
            if time.time() - last_time >= self.checkpoint_interval:
                return True

        if self.strategy == CheckpointStrategy.PROGRESS_BASED:
            # Checkpoint at 25%, 50%, 75% milestones
            milestones = [0.25, 0.50, 0.75]
            for milestone in milestones:
                if abs(progress - milestone) < 0.05:  # Within 5% of milestone
                    # Check if we've already checkpointed near this milestone
                    if job_id in self.checkpoints:
                        last_progress = self.checkpoints[job_id].progress
                        if abs(last_progress - milestone) > 0.1:
                            return True
                    else:
                        return True

        if self.strategy == CheckpointStrategy.AUTOMATIC:
            # Smart checkpointing: combine time and progress
            last_time = self.last_checkpoint_time.get(job_id, 0)
            time_elapsed = time.time() - last_time

            # More frequent checkpointing early on
            if progress < 0.3 and time_elapsed >= 15:  # Every 15s early
                return True
            elif progress < 0.7 and time_elapsed >= 30:  # Every 30s mid
                return True
            elif time_elapsed >= 60:  # Every 60s late
                return True

        return False

    def create_checkpoint(self,
                         job_id: str,
                         progress: float,
                         state: Dict[str, Any],
                         completed_steps: list,
                         current_step: str,
                         intermediate_results: Dict[str, Any] = None,
                         input_data: Dict[str, Any] = None,
                         attempt: int = 1) -> Checkpoint:
        """
        Create a checkpoint

        Args:
            job_id: Job identifier
            progress: Current progress (0.0 to 1.0)
            state: Current execution state
            completed_steps: List of completed steps
            current_step: Current step being executed
            intermediate_results: Partial results
            input_data: Original input data
            attempt: Attempt number

        Returns:
            Created checkpoint
        """
        checkpoint_id = self._generate_checkpoint_id(job_id, progress)

        checkpoint = Checkpoint(
            job_id=job_id,
            checkpoint_id=checkpoint_id,
            timestamp=time.time(),
            progress=progress,
            state=state or {},
            completed_steps=completed_steps or [],
            current_step=current_step,
            node_id=self.node_id,
            attempt=attempt,
            input_data=input_data or {},
            intermediate_results=intermediate_results or {}
        )

        # Save to memory
        self.checkpoints[job_id] = checkpoint
        self.last_checkpoint_time[job_id] = time.time()

        # Persist to disk
        self._save_checkpoint(checkpoint)

        print(f"[CHECKPOINT] Created checkpoint for {job_id} at {progress*100:.1f}% progress")

        return checkpoint

    def get_latest_checkpoint(self, job_id: str) -> Optional[Checkpoint]:
        """
        Get latest checkpoint for a job

        Args:
            job_id: Job identifier

        Returns:
            Latest checkpoint or None
        """
        # Check memory first
        if job_id in self.checkpoints:
            return self.checkpoints[job_id]

        # Check disk
        return self._load_latest_checkpoint(job_id)

    def delete_checkpoint(self, job_id: str):
        """
        Delete checkpoint for completed job

        Args:
            job_id: Job identifier
        """
        # Remove from memory
        self.checkpoints.pop(job_id, None)
        self.last_checkpoint_time.pop(job_id, None)

        # Remove from disk
        checkpoint_files = list(self.checkpoint_dir.glob(f"{job_id}_*.ckpt"))
        for file in checkpoint_files:
            file.unlink()
            print(f"[CHECKPOINT] Deleted checkpoint: {file.name}")

    def _generate_checkpoint_id(self, job_id: str, progress: float) -> str:
        """Generate unique checkpoint identifier"""
        data = f"{job_id}_{progress}_{time.time()}_{self.node_id}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _save_checkpoint(self, checkpoint: Checkpoint):
        """Persist checkpoint to disk"""
        filename = f"{checkpoint.job_id}_{checkpoint.checkpoint_id}.ckpt"
        filepath = self.checkpoint_dir / filename

        try:
            # Serialize checkpoint
            with open(filepath, 'wb') as f:
                pickle.dump(checkpoint, f)

            print(f"[CHECKPOINT] Saved to disk: {filename}")
        except Exception as e:
            print(f"[CHECKPOINT] Error saving: {e}")

    def _load_latest_checkpoint(self, job_id: str) -> Optional[Checkpoint]:
        """Load latest checkpoint from disk"""
        checkpoint_files = list(self.checkpoint_dir.glob(f"{job_id}_*.ckpt"))

        if not checkpoint_files:
            return None

        # Get most recent checkpoint
        latest_file = max(checkpoint_files, key=lambda f: f.stat().st_mtime)

        try:
            with open(latest_file, 'rb') as f:
                checkpoint = pickle.load(f)

            print(f"[CHECKPOINT] Loaded from disk: {latest_file.name}")
            return checkpoint
        except Exception as e:
            print(f"[CHECKPOINT] Error loading: {e}")
            return None

    def list_checkpoints(self, job_id: str = None) -> list:
        """
        List all checkpoints

        Args:
            job_id: Optional job filter

        Returns:
            List of checkpoint info
        """
        pattern = f"{job_id}_*.ckpt" if job_id else "*.ckpt"
        checkpoint_files = list(self.checkpoint_dir.glob(pattern))

        checkpoints = []
        for file in checkpoint_files:
            try:
                with open(file, 'rb') as f:
                    ckpt = pickle.load(f)
                checkpoints.append({
                    'job_id': ckpt.job_id,
                    'checkpoint_id': ckpt.checkpoint_id,
                    'progress': ckpt.progress,
                    'timestamp': ckpt.timestamp,
                    'node_id': ckpt.node_id,
                    'file': file.name
                })
            except:
                pass

        return sorted(checkpoints, key=lambda x: x['timestamp'], reverse=True)


class ResumableTaskExecutor:
    """
    Executor that supports checkpoint-based task resumption

    Usage:
        executor = ResumableTaskExecutor(checkpoint_manager)

        # Define resumable task
        async def my_task(context):
            # Step 1
            await context.checkpoint_if_needed("step1_complete")

            # Step 2
            await context.checkpoint_if_needed("step2_complete")

            # Step 3
            return result

        # Execute (will resume from checkpoint if exists)
        result = await executor.execute_resumable(job_id, my_task, input_data)
    """

    def __init__(self, checkpoint_manager: CheckpointManager):
        self.checkpoint_manager = checkpoint_manager

    async def execute_resumable(self,
                                job_id: str,
                                task_func: Callable,
                                input_data: Dict[str, Any],
                                attempt: int = 1) -> Any:
        """
        Execute task with checkpoint support

        Args:
            job_id: Job identifier
            task_func: Async function to execute
            input_data: Input data for task
            attempt: Attempt number (for retry tracking)

        Returns:
            Task result
        """
        # Check for existing checkpoint
        checkpoint = self.checkpoint_manager.get_latest_checkpoint(job_id)

        if checkpoint:
            print(f"[RESUME] Found checkpoint for {job_id} at {checkpoint.progress*100:.1f}%")
            print(f"[RESUME] Resuming from step: {checkpoint.current_step}")

            # Create context with restored state
            context = ResumableContext(
                job_id=job_id,
                checkpoint_manager=self.checkpoint_manager,
                initial_state=checkpoint.state,
                completed_steps=checkpoint.completed_steps,
                current_step=checkpoint.current_step,
                progress=checkpoint.progress,
                input_data=checkpoint.input_data,
                intermediate_results=checkpoint.intermediate_results,
                attempt=attempt
            )
        else:
            print(f"[EXECUTE] Starting fresh execution for {job_id}")

            # Create fresh context
            context = ResumableContext(
                job_id=job_id,
                checkpoint_manager=self.checkpoint_manager,
                input_data=input_data,
                attempt=attempt
            )

        try:
            # Execute task with context
            result = await task_func(context)

            # Clean up checkpoint on success
            self.checkpoint_manager.delete_checkpoint(job_id)

            print(f"[EXECUTE] Completed {job_id}")
            return result

        except Exception as e:
            print(f"[EXECUTE] Error in {job_id}: {e}")
            # Checkpoint is preserved for retry
            raise


class ResumableContext:
    """
    Context provided to resumable tasks

    Provides checkpoint and state management APIs
    """

    def __init__(self,
                 job_id: str,
                 checkpoint_manager: CheckpointManager,
                 initial_state: Dict[str, Any] = None,
                 completed_steps: list = None,
                 current_step: str = None,
                 progress: float = 0.0,
                 input_data: Dict[str, Any] = None,
                 intermediate_results: Dict[str, Any] = None,
                 attempt: int = 1):

        self.job_id = job_id
        self.checkpoint_manager = checkpoint_manager
        self.state = initial_state or {}
        self.completed_steps = completed_steps or []
        self.current_step = current_step or "init"
        self.progress = progress
        self.input_data = input_data or {}
        self.intermediate_results = intermediate_results or {}
        self.attempt = attempt

    def was_step_completed(self, step_id: str) -> bool:
        """Check if step was already completed (for resume)"""
        return step_id in self.completed_steps

    def mark_step_complete(self, step_id: str):
        """Mark step as completed"""
        if step_id not in self.completed_steps:
            self.completed_steps.append(step_id)
            print(f"[CONTEXT] Step completed: {step_id}")

    def set_current_step(self, step_id: str):
        """Set current executing step"""
        self.current_step = step_id
        print(f"[CONTEXT] Current step: {step_id}")

    def update_progress(self, progress: float):
        """Update progress (0.0 to 1.0)"""
        self.progress = progress

    async def checkpoint_if_needed(self, step_id: str = None):
        """
        Create checkpoint if strategy indicates it's time

        Args:
            step_id: Optional step identifier
        """
        if step_id:
            self.mark_step_complete(step_id)

        if self.checkpoint_manager.should_checkpoint(self.job_id, self.progress):
            self.checkpoint()

    def checkpoint(self):
        """Force create checkpoint"""
        self.checkpoint_manager.create_checkpoint(
            job_id=self.job_id,
            progress=self.progress,
            state=self.state,
            completed_steps=self.completed_steps,
            current_step=self.current_step,
            intermediate_results=self.intermediate_results,
            input_data=self.input_data,
            attempt=self.attempt
        )

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get state value"""
        return self.state.get(key, default)

    def set_state(self, key: str, value: Any):
        """Set state value"""
        self.state[key] = value

    def get_intermediate_result(self, key: str) -> Any:
        """Get intermediate result"""
        return self.intermediate_results.get(key)

    def set_intermediate_result(self, key: str, value: Any):
        """Store intermediate result"""
        self.intermediate_results[key] = value


# Example resumable task
async def example_long_running_task(context: ResumableContext):
    """
    Example of a resumable task with checkpoints

    Simulates a long-running job with multiple steps
    """
    import asyncio

    print(f"[TASK] Starting job {context.job_id}")

    # Step 1: Data preprocessing
    if not context.was_step_completed("preprocess"):
        context.set_current_step("preprocess")
        print("[TASK] Step 1: Preprocessing data...")
        await asyncio.sleep(2)  # Simulate work

        context.set_state("preprocessed_data", {"status": "ready"})
        context.update_progress(0.33)
        await context.checkpoint_if_needed("preprocess")
    else:
        print("[TASK] Step 1: Skipping (already completed)")

    # Step 2: Main processing
    if not context.was_step_completed("process"):
        context.set_current_step("process")
        print("[TASK] Step 2: Processing...")
        await asyncio.sleep(3)  # Simulate work

        context.set_intermediate_result("processed_count", 1000)
        context.update_progress(0.66)
        await context.checkpoint_if_needed("process")
    else:
        print("[TASK] Step 2: Skipping (already completed)")

    # Step 3: Finalization
    if not context.was_step_completed("finalize"):
        context.set_current_step("finalize")
        print("[TASK] Step 3: Finalizing...")
        await asyncio.sleep(2)  # Simulate work

        context.update_progress(1.0)
        await context.checkpoint_if_needed("finalize")
    else:
        print("[TASK] Step 3: Skipping (already completed)")

    print(f"[TASK] Job {context.job_id} completed!")

    return {
        "status": "success",
        "processed_count": context.get_intermediate_result("processed_count"),
        "attempts": context.attempt
    }
