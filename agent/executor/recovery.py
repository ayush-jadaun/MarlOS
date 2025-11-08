"""
Job Recovery and Migration
Handles job failure recovery and migration between nodes
"""
import asyncio
import time
from typing import Optional, Dict, Callable, Any
from ..schema.schema import JobBackup
from .checkpoint import CheckpointManager, ResumableTaskExecutor


class RecoveryManager:
    """
    Manages job recovery and migration
    """

    def __init__(self, node_id: str, checkpoint_manager: CheckpointManager = None, check_interval: float = 5.0):
        self.node_id = node_id

        # Jobs we're backing up (job_id -> JobBackup)
        self.backup_jobs: Dict[str, JobBackup] = {}

        # Heartbeat monitoring
        self.heartbeat_timeout = 15  # seconds
        self.check_interval = check_interval  # seconds between checks
        self.running = False

        # Checkpoint integration
        self.checkpoint_manager = checkpoint_manager or CheckpointManager(
            node_id=node_id,
            checkpoint_dir="./data/checkpoints"
        )
        self.resumable_executor = ResumableTaskExecutor(self.checkpoint_manager)

        # Task function registry (job_id -> task_func)
        self.task_registry: Dict[str, Callable] = {}
    
    async def start(self):
        """Start recovery monitoring"""
        self.running = True
        asyncio.create_task(self._monitor_loop())
        print("[RECOVERY] Started job recovery monitoring")
    
    async def stop(self):
        """Stop recovery monitoring"""
        self.running = False
    
    def register_task_function(self, job_id: str, task_func: Callable):
        """Register a task function for resumable execution"""
        self.task_registry[job_id] = task_func
        print(f"[RECOVERY] Registered task function for job {job_id}")

    def register_backup(self, job_id: str, job: dict, primary_node: str, task_func: Callable = None):
        """Register as backup for a job"""
        backup = JobBackup(
            job_id=job_id,
            job=job,
            primary_node=primary_node,
            backup_node=self.node_id,
            last_heartbeat=time.time(),
            progress=0.0
        )

        self.backup_jobs[job_id] = backup

        # Register task function if provided
        if task_func:
            self.register_task_function(job_id, task_func)

        print(f"[RECOVERY] Registered as backup for job {job_id} (primary: {primary_node})")
    
    def update_heartbeat(self, job_id: str, progress: float):
        """Update heartbeat from primary node"""
        if job_id in self.backup_jobs:
            self.backup_jobs[job_id].last_heartbeat = time.time()
            self.backup_jobs[job_id].progress = progress
    
    def remove_backup(self, job_id: str):
        """Remove backup (job completed)"""
        self.backup_jobs.pop(job_id, None)
    
    async def _monitor_loop(self):
        """Monitor backup jobs for failures"""
        while self.running:
            await asyncio.sleep(self.check_interval)

            current_time = time.time()
            
            # Check for heartbeat timeouts
            for job_id, backup in list(self.backup_jobs.items()):
                time_since_heartbeat = current_time - backup.last_heartbeat
                
                if time_since_heartbeat > self.heartbeat_timeout:
                    print(f"[WARNING] [RECOVERY] Primary node timeout for job {job_id}")
                    print(f"[RECOVERY] Taking over job execution...")
                    
                    # Trigger takeover
                    await self._takeover_job(backup)
    
    def set_executor_callback(self, executor_callback):
        """Set callback to executor for job takeover"""
        self.executor_callback = executor_callback

    async def _takeover_job(self, backup: JobBackup):
        """Take over job from failed primary and resume from checkpoint"""
        job_id = backup.job_id
        job = backup.job

        print(f"[TAKEOVER] [RECOVERY] Taking over job {job_id} from {backup.primary_node}")

        # Remove from backup list
        self.backup_jobs.pop(job_id, None)

        # Check if we have a checkpoint to resume from
        checkpoint = self.checkpoint_manager.get_latest_checkpoint(job_id)

        if checkpoint:
            print(f"[RECOVERY] Found checkpoint at {checkpoint.progress*100:.1f}% progress")
            print(f"[RECOVERY] Resuming from step: {checkpoint.current_step}")
        else:
            print(f"[RECOVERY] No checkpoint found - starting from beginning")

        # Try to use ResumableTaskExecutor if task function is registered
        if job_id in self.task_registry:
            task_func = self.task_registry[job_id]
            input_data = job.get('input_data', {})
            current_attempt = job.get('attempt', 1) + 1  # Increment attempt number

            try:
                print(f"[RECOVERY] Using ResumableTaskExecutor for job {job_id}")
                result = await self.resumable_executor.execute_resumable(
                    job_id=job_id,
                    task_func=task_func,
                    input_data=input_data,
                    attempt=current_attempt
                )
                print(f"[SUCCESS] [RECOVERY] Takeover successful - job {job_id} completed")
                return result
            except Exception as e:
                print(f"[FAILED] [RECOVERY] Takeover failed for job {job_id}: {e}")
                raise

        # Fallback to legacy executor callback
        elif hasattr(self, 'executor_callback') and self.executor_callback:
            try:
                print(f"[RECOVERY] Using legacy executor callback for job {job_id}")
                result = await self.executor_callback(job)
                print(f"[SUCCESS] [RECOVERY] Takeover successful - job {job_id} completed")
                return result
            except Exception as e:
                print(f"[FAILED] [RECOVERY] Takeover failed for job {job_id}: {e}")
                return None
        else:
            print(f"[WARNING] [RECOVERY] No task function registered and no executor callback set")
            print(f"[RECOVERY] Cannot execute job {job_id} - requires manual intervention")
            return None
    
    def get_backup_count(self) -> int:
        """Get number of jobs we're backing up"""
        return len(self.backup_jobs)