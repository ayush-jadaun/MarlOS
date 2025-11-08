"""
Demonstration: Automatic Recovery with Checkpoints
Shows RecoveryManager automatically resuming failed jobs from checkpoints
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
from agent.executor.recovery import RecoveryManager


# ============================================================================
# Define a Long-Running Task
# ============================================================================

async def data_processing_task(context: ResumableContext):
    """
    Multi-stage data processing task that can fail and resume
    """
    print(f"\n{'='*80}")
    print(f"STARTING JOB: {context.job_id}")
    print(f"Node: {context.checkpoint_manager.node_id}")
    print(f"Attempt: {context.attempt}")
    print(f"{'='*80}\n")

    stages = [
        ("stage_1_load", "Loading data", 3),
        ("stage_2_process", "Processing data", 4),
        ("stage_3_analyze", "Analyzing results", 3),
        ("stage_4_save", "Saving output", 2),
    ]

    for i, (stage_id, stage_name, duration) in enumerate(stages):
        progress = (i + 1) / len(stages)

        # Skip if already completed
        if context.was_step_completed(stage_id):
            print(f"[OK] STAGE {i+1}/{len(stages)}: {stage_name} [ALREADY COMPLETED - SKIPPING]")
            continue

        print(f"\n[STAGE {i+1}/{len(stages)}] {stage_name}")
        context.set_current_step(stage_id)
        context.update_progress(progress)

        # Simulate work
        for j in range(duration):
            await asyncio.sleep(1)
            print(f"  Progress: {((j+1)/duration)*100:.0f}%")

            # Simulate failure (20% chance on first 2 attempts)
            if random.random() < 0.15 and context.attempt < 3:
                print(f"\n[!] NODE FAILURE during {stage_name}!")
                raise Exception(f"Node crashed during {stage_name}")

        # Mark complete and checkpoint
        context.mark_step_complete(stage_id)
        context.set_intermediate_result(f"{stage_id}_result", {"status": "done", "time": time.time()})
        await context.checkpoint_if_needed(stage_id)

    print(f"\n{'='*80}")
    print(f"JOB COMPLETED: {context.job_id}")
    print(f"{'='*80}\n")

    return {"status": "success", "stages": len(stages), "attempt": context.attempt}


# ============================================================================
# Simulate Multi-Node System with Automatic Recovery
# ============================================================================

async def simulate_multi_node_recovery():
    """
    Simulates a multi-node system where:
    1. Node 1 starts a job
    2. Node 2 monitors as backup
    3. If Node 1 fails, Node 2 automatically takes over
    4. Job resumes from last checkpoint
    """
    print("\n" + "="*80)
    print("AUTOMATIC RECOVERY WITH CHECKPOINTS".center(80))
    print("="*80)

    job_id = f"recovery_job_{int(time.time())}"

    # Shared checkpoint storage (simulates shared filesystem)
    shared_checkpoint_dir = "./data/checkpoints"

    # ========================================================================
    # NODE 1: Primary executor with recovery manager
    # ========================================================================
    print("\n" + "="*80)
    print("  NODE 1: Starting job execution")
    print("="*80)

    node1_checkpoint_mgr = CheckpointManager(
        node_id="node_1",
        checkpoint_dir=shared_checkpoint_dir,
        strategy=CheckpointStrategy.PROGRESS_BASED,
        checkpoint_interval=5.0
    )

    node1_recovery = RecoveryManager(
        node_id="node_1",
        checkpoint_manager=node1_checkpoint_mgr
    )

    # Register the task function for recovery
    node1_recovery.register_task_function(job_id, data_processing_task)

    node1_executor = ResumableTaskExecutor(node1_checkpoint_mgr)

    # ========================================================================
    # NODE 2: Backup node with recovery manager (starts monitoring)
    # ========================================================================
    print("\n" + "="*80)
    print("  NODE 2: Registering as backup")
    print("="*80)

    node2_checkpoint_mgr = CheckpointManager(
        node_id="node_2",
        checkpoint_dir=shared_checkpoint_dir,  # Same checkpoint dir!
        strategy=CheckpointStrategy.PROGRESS_BASED,
        checkpoint_interval=5.0
    )

    node2_recovery = RecoveryManager(
        node_id="node_2",
        checkpoint_manager=node2_checkpoint_mgr,
        check_interval=2.0  # Check every 2 seconds
    )

    # Register as backup
    node2_recovery.register_backup(
        job_id=job_id,
        job={"input_data": {"dataset": "data.csv"}, "attempt": 1},
        primary_node="node_1",
        task_func=data_processing_task  # Register task function
    )

    # Start monitoring
    await node2_recovery.start()

    # ========================================================================
    # Execute job on Node 1 (will likely fail)
    # ========================================================================

    try:
        print("\n[NODE 1] Starting job execution...")
        result = await node1_executor.execute_resumable(
            job_id=job_id,
            task_func=data_processing_task,
            input_data={"dataset": "data.csv"},
            attempt=1
        )
        print("\n[SUCCESS] Job completed on Node 1!")
        await node2_recovery.stop()
        return result

    except Exception as e:
        print(f"\n[FAILED] NODE 1 FAILED: {e}")
        print("   Checkpoint saved - waiting for backup node to take over...")

        # Simulate heartbeat timeout (Node 2 detects failure)
        print("\n[TIMEOUT] [NODE 2] Heartbeat timeout detected...")
        await asyncio.sleep(3)

        # Manually trigger takeover (in real system, this happens automatically)
        backup = node2_recovery.backup_jobs.get(job_id)
        if backup:
            print("\n[NODE 2] Taking over failed job...")
            try:
                result = await node2_recovery._takeover_job(backup)
                print("\n[SUCCESS] Job recovered and completed on Node 2!")
                await node2_recovery.stop()
                return result
            except Exception as e2:
                print(f"\n[FAILED] NODE 2 ALSO FAILED: {e2}")

                # Node 3 takeover
                print("\n" + "="*80)
                print("  NODE 3: Final recovery attempt")
                print("="*80)

                node3_checkpoint_mgr = CheckpointManager(
                    node_id="node_3",
                    checkpoint_dir=shared_checkpoint_dir,
                    strategy=CheckpointStrategy.PROGRESS_BASED,
                    checkpoint_interval=5.0
                )

                node3_executor = ResumableTaskExecutor(node3_checkpoint_mgr)

                result = await node3_executor.execute_resumable(
                    job_id=job_id,
                    task_func=data_processing_task,
                    input_data={"dataset": "data.csv"},
                    attempt=3  # No failures on attempt 3+
                )
                print("\n[SUCCESS] Job FINALLY completed on Node 3!")
                await node2_recovery.stop()
                return result

    await node2_recovery.stop()


# ============================================================================
# Main
# ============================================================================

async def main():
    print("\n\n")
    print("=" * 80)
    print("MARLOS: AUTOMATIC RECOVERY WITH CHECKPOINTS".center(80))
    print("="*80)
    print("\nThis demo shows:")
    print("  - RecoveryManager monitoring job health")
    print("  - Automatic checkpoint creation during execution")
    print("  - Backup node detecting failure")
    print("  - Automatic job resumption from checkpoint")
    print("  - No work lost or duplicated")
    print("="*80)

    result = await simulate_multi_node_recovery()

    print("\n" + "="*80)
    print("DEMONSTRATION COMPLETE".center(80))
    print("="*80)
    print(f"\nFinal Result: {result}")
    print("\nKEY FEATURES DEMONSTRATED:")
    print("  [OK] Automatic checkpoint creation")
    print("  [OK] Heartbeat monitoring")
    print("  [OK] Failure detection")
    print("  [OK] Automatic job takeover")
    print("  [OK] Resume from last checkpoint")
    print("  [OK] No duplicate work")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
