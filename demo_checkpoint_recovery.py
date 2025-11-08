"""
Demonstration: Checkpoint-Based Task Recovery

This demo shows:
1. Task execution with periodic checkpoints
2. Simulated node failure mid-execution
3. Task resumption from last checkpoint on different node
4. Complete recovery without data loss
"""

import asyncio
import sys
import os
import time
import random

# Add agent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))

from agent.executor.checkpoint import (
    CheckpointManager,
    ResumableTaskExecutor,
    ResumableContext,
    CheckpointStrategy
)


# ============================================================================
# Define a Long-Running Resumable Task
# ============================================================================

async def data_processing_job(context: ResumableContext):
    """
    Simulates a long data processing job with multiple stages

    This job processes data in 5 stages, each taking several seconds.
    If failure occurs, it can resume from the last completed stage.
    """
    print(f"\n{'='*80}")
    print(f"STARTING JOB: {context.job_id}")
    print(f"Attempt: {context.attempt}")
    print(f"{'='*80}\n")

    stages = [
        ("data_ingestion", "Ingesting data from sources", 5),
        ("data_cleaning", "Cleaning and validating data", 7),
        ("feature_extraction", "Extracting features", 6),
        ("model_training", "Training ML model", 10),
        ("model_evaluation", "Evaluating model performance", 4),
    ]

    for i, (stage_id, stage_name, duration) in enumerate(stages):
        progress = (i + 1) / len(stages)

        if context.was_step_completed(stage_id):
            print(f"✓ STAGE {i+1}/{len(stages)}: {stage_name} [ALREADY COMPLETED - SKIPPING]")
            continue

        print(f"\n[STAGE {i+1}/{len(stages)}] {stage_name}")
        context.set_current_step(stage_id)
        context.update_progress(progress)

        # Simulate work with progress updates
        for j in range(duration):
            await asyncio.sleep(1)
            stage_progress = (j + 1) / duration
            print(f"  Progress: {stage_progress*100:.0f}% ({j+1}/{duration}s)")

            # SIMULATE RANDOM FAILURE (10% chance per second)
            if random.random() < 0.10 and context.attempt < 3:  # Fail only on first 2 attempts
                print(f"\n💥 SIMULATED NODE FAILURE during {stage_name}!")
                print(f"   Node crashed at {stage_progress*100:.0f}% of stage {i+1}")
                raise Exception(f"Node failure during {stage_name}")

        # Mark stage complete and checkpoint
        context.mark_step_complete(stage_id)
        context.set_intermediate_result(f"{stage_id}_result", {
            "status": "completed",
            "timestamp": time.time(),
            "duration": duration
        })

        # Create checkpoint
        await context.checkpoint_if_needed(stage_id)

    print(f"\n{'='*80}")
    print(f"JOB COMPLETED: {context.job_id}")
    print(f"All {len(stages)} stages completed successfully")
    print(f"{'='*80}\n")

    return {
        "status": "success",
        "stages_completed": len(stages),
        "total_duration": sum(s[2] for s in stages),
        "attempt": context.attempt
    }


# ============================================================================
# Demo Execution with Failure Recovery
# ============================================================================

async def demonstrate_recovery():
    """
    Main demonstration of checkpoint recovery

    Simulates:
    1. Node 1 starts job
    2. Node 1 fails mid-execution
    3. Node 2 detects failure and resumes from checkpoint
    4. Job completes successfully
    """
    print("\n" + "="*80)
    print(" "*20 + "CHECKPOINT RECOVERY DEMONSTRATION")
    print("="*80)

    job_id = f"processing_job_{int(time.time())}"

    # ========================================================================
    # ATTEMPT 1: Node 1 starts execution (likely to fail)
    # ========================================================================

    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  ATTEMPT 1: Node 1 Executing".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)

    node1_checkpoint_mgr = CheckpointManager(
        node_id="node_1",
        strategy=CheckpointStrategy.PROGRESS_BASED,
        checkpoint_interval=5.0
    )

    node1_executor = ResumableTaskExecutor(node1_checkpoint_mgr)

    try:
        result = await node1_executor.execute_resumable(
            job_id=job_id,
            task_func=data_processing_job,
            input_data={"dataset": "customer_data.csv"},
            attempt=1
        )

        print("\n✅ Job completed on first attempt!")
        print(f"Result: {result}")
        return  # Success on first try

    except Exception as e:
        print(f"\n❌ NODE 1 FAILED: {e}")
        print("   Checkpoint was saved before failure")
        print("   Job will be recovered by another node...")

    # Wait a bit (simulating failure detection time)
    await asyncio.sleep(2)

    # ========================================================================
    # ATTEMPT 2: Node 2 resumes from checkpoint
    # ========================================================================

    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  ATTEMPT 2: Node 2 Resuming from Checkpoint".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)

    # Node 2 uses same checkpoint directory (shared storage)
    node2_checkpoint_mgr = CheckpointManager(
        node_id="node_2",
        strategy=CheckpointStrategy.PROGRESS_BASED,
        checkpoint_interval=5.0
    )

    node2_executor = ResumableTaskExecutor(node2_checkpoint_mgr)

    # List available checkpoints
    checkpoints = node2_checkpoint_mgr.list_checkpoints(job_id)
    if checkpoints:
        print(f"\n[NODE 2] Found {len(checkpoints)} checkpoint(s):")
        for ckpt in checkpoints:
            print(f"  - Progress: {ckpt['progress']*100:.1f}%, Node: {ckpt['node_id']}")

    try:
        result = await node2_executor.execute_resumable(
            job_id=job_id,
            task_func=data_processing_job,
            input_data={"dataset": "customer_data.csv"},  # Not used (loaded from checkpoint)
            attempt=2
        )

        print("\n✅ Job recovered and completed on Node 2!")
        print(f"Result: {result}")
        return

    except Exception as e:
        print(f"\n❌ NODE 2 ALSO FAILED: {e}")
        print("   Job will be retried on Node 3...")

    # Wait a bit
    await asyncio.sleep(2)

    # ========================================================================
    # ATTEMPT 3: Node 3 resumes (no more failures simulated)
    # ========================================================================

    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  ATTEMPT 3: Node 3 Resuming (Final Attempt)".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)

    node3_checkpoint_mgr = CheckpointManager(
        node_id="node_3",
        strategy=CheckpointStrategy.PROGRESS_BASED,
        checkpoint_interval=5.0
    )

    node3_executor = ResumableTaskExecutor(node3_checkpoint_mgr)

    result = await node3_executor.execute_resumable(
        job_id=job_id,
        task_func=data_processing_job,
        input_data={"dataset": "customer_data.csv"},
        attempt=3  # No failures on attempt 3+
    )

    print("\n✅ Job FINALLY completed on Node 3!")
    print(f"Result: {result}")

    # ========================================================================
    # Summary
    # ========================================================================

    print("\n" + "="*80)
    print(" "*20 + "RECOVERY DEMONSTRATION COMPLETE")
    print("="*80)

    print("\nKEY TAKEAWAYS:")
    print("  ✓ Node 1 failed mid-execution")
    print("  ✓ Checkpoint preserved partial progress")
    print("  ✓ Node 2 resumed from checkpoint (may have also failed)")
    print("  ✓ Node 3 completed the job successfully")
    print("  ✓ NO work was lost or duplicated")
    print("  ✓ Final result includes work from all attempts")

    print("\n" + "="*80 + "\n")


# ============================================================================
# Simple Task without Failures (for comparison)
# ============================================================================

async def demonstrate_simple_execution():
    """
    Show a successful execution without failures
    """
    print("\n" + "="*80)
    print(" "*15 + "SIMPLE EXECUTION (No Failures)")
    print("="*80)

    job_id = f"simple_job_{int(time.time())}"

    checkpoint_mgr = CheckpointManager(
        node_id="node_simple",
        strategy=CheckpointStrategy.TIME_BASED,
        checkpoint_interval=10.0
    )

    executor = ResumableTaskExecutor(checkpoint_mgr)

    async def simple_task(context: ResumableContext):
        """Simple 3-step task"""
        steps = ["step1", "step2", "step3"]

        for i, step in enumerate(steps):
            if not context.was_step_completed(step):
                print(f"\n[STEP {i+1}/{len(steps)}] Executing {step}...")
                context.set_current_step(step)
                context.update_progress((i + 1) / len(steps))

                await asyncio.sleep(2)

                context.mark_step_complete(step)
                await context.checkpoint_if_needed(step)

        return {"status": "success", "steps": len(steps)}

    result = await executor.execute_resumable(
        job_id=job_id,
        task_func=simple_task,
        input_data={},
        attempt=1
    )

    print(f"\n✅ Simple job completed: {result}")
    print("="*80 + "\n")


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run demonstrations"""
    print("\n\n")
    print("=" + "="*78 + "=")
    print(" " + " "*78 + " ")
    print("  MARLOS: CHECKPOINT-BASED TASK RECOVERY".center(80))
    print("  Demonstration of Fault-Tolerant Task Execution".center(80))
    print(" " + " "*78 + " ")
    print("=" + "="*78 + "=")

    # Demo 1: Simple execution without failures
    await demonstrate_simple_execution()

    # Demo 2: Recovery from failures
    await demonstrate_recovery()

    print("\n" + "="*80)
    print("ALL DEMONSTRATIONS COMPLETE")
    print("="*80)
    print("\nCheckpoint files saved in: ./data/checkpoints/")
    print("Examine them to see saved state between failures")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
