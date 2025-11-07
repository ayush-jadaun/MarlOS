"""
Job Recovery and Migration
Handles job failure recovery and migration between nodes
"""
import asyncio
import time
from typing import Optional, Dict
from ..schema.schema import JobBackup


class RecoveryManager:
    """
    Manages job recovery and migration
    """
    
    def __init__(self, node_id: str, check_interval: float = 5.0):
        self.node_id = node_id

        # Jobs we're backing up (job_id -> JobBackup)
        self.backup_jobs: Dict[str, JobBackup] = {}

        # Heartbeat monitoring
        self.heartbeat_timeout = 15  # seconds
        self.check_interval = check_interval  # seconds between checks
        self.running = False
    
    async def start(self):
        """Start recovery monitoring"""
        self.running = True
        asyncio.create_task(self._monitor_loop())
        print("[RECOVERY] Started job recovery monitoring")
    
    async def stop(self):
        """Stop recovery monitoring"""
        self.running = False
    
    def register_backup(self, job_id: str, job: dict, primary_node: str):
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
                    print(f"⚠️  [RECOVERY] Primary node timeout for job {job_id}")
                    print(f"[RECOVERY] Taking over job execution...")
                    
                    # Trigger takeover
                    await self._takeover_job(backup)
    
    def set_executor_callback(self, executor_callback):
        """Set callback to executor for job takeover"""
        self.executor_callback = executor_callback

    async def _takeover_job(self, backup: JobBackup):
        """Take over job from failed primary"""
        job_id = backup.job_id
        job = backup.job

        print(f"🔄 [RECOVERY] Taking over job {job_id} from {backup.primary_node}")

        # Remove from backup list
        self.backup_jobs.pop(job_id, None)

        # Trigger job execution via callback
        if hasattr(self, 'executor_callback') and self.executor_callback:
            try:
                # Execute the job as backup node
                result = await self.executor_callback(job)
                print(f"✅ [RECOVERY] Takeover successful - job {job_id} completed")
                return result
            except Exception as e:
                print(f"❌ [RECOVERY] Takeover failed for job {job_id}: {e}")
                return None
        else:
            print(f"⚠️  [RECOVERY] No executor callback set - cannot execute job {job_id}")
            print(f"[RECOVERY] Job {job_id} requires manual intervention")
    
    def get_backup_count(self) -> int:
        """Get number of jobs we're backing up"""
        return len(self.backup_jobs)