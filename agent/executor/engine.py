"""
Job Execution Engine
Main coordinator for job execution with sandboxing and monitoring
"""
import asyncio
import time
import uuid
from typing import Dict, Optional, Callable
from ..config import ExecutorConfig
from ..schema.schema import JobStatus, JobResult

class ExecutionEngine:
    """
    Main job execution engine
    Coordinates different job runners and manages execution lifecycle
    """
    
    def __init__(self, node_id: str, config: ExecutorConfig, min_timeout: float = 10.0):
        self.node_id = node_id
        self.config = config
        self.min_timeout = min_timeout  # Minimum timeout in seconds

        # Active jobs (job_id -> task)
        self.active_jobs: Dict[str, asyncio.Task] = {}
        self.job_metadata: Dict[str, dict] = {}

        # Job runners (will be registered)
        self.runners: Dict[str, Callable] = {}

        # Heartbeat callbacks
        self.heartbeat_callbacks: list = []

        # Results callback
        self.result_callback: Optional[Callable] = None
    
    def register_runner(self, job_type: str, runner: Callable):
        """Register a job runner for a specific job type"""
        self.runners[job_type] = runner
        print(f"[EXECUTOR] Registered runner for: {job_type}")
    
    def set_result_callback(self, callback: Callable):
        """Set callback for job results"""
        self.result_callback = callback
    
    def add_heartbeat_callback(self, callback: Callable):
        """Add callback for heartbeat updates"""
        self.heartbeat_callbacks.append(callback)
    
    async def execute_job(self, job: dict) -> JobResult:
        """
        Execute a job asynchronously
        Returns job result
        """
        job_id = job['job_id']
        job_type = job['job_type']
        
        print(f"[EXECUTOR] Starting job {job_id} ({job_type})")
        
        # Check if runner exists
        if job_type not in self.runners:
            return JobResult(
                job_id=job_id,
                status=JobStatus.FAILURE,
                output={},
                error=f"No runner for job type: {job_type}",
                start_time=time.time(),
                end_time=time.time(),
                duration=0.0
            )
        
        # Check concurrent job limit
        if len(self.active_jobs) >= self.config.max_concurrent_jobs:
            return JobResult(
                job_id=job_id,
                status=JobStatus.FAILURE,
                output={},
                error="Max concurrent jobs reached",
                start_time=time.time(),
                end_time=time.time(),
                duration=0.0
            )
        
        # Create execution task
        task = asyncio.create_task(self._execute_job_internal(job))
        self.active_jobs[job_id] = task
        self.job_metadata[job_id] = {
            'job': job,
            'start_time': time.time()
        }
        
        # Wait for completion
        try:
            result = await task
            return result
        finally:
            # Cleanup
            self.active_jobs.pop(job_id, None)
            self.job_metadata.pop(job_id, None)
    
    async def _execute_job_internal(self, job: dict) -> JobResult:
        """Internal job execution with timeout and monitoring"""
        job_id = job['job_id']
        job_type = job['job_type']
        timeout = job.get('deadline', time.time() + 300) - time.time()
        
        start_time = time.time()
        
        # Start heartbeat
        heartbeat_task = asyncio.create_task(self._heartbeat_loop(job_id))
        
        try:
            # Get runner
            runner = self.runners[job_type]
            
            # Execute with timeout
            output = await asyncio.wait_for(
                runner(job),
                timeout=max(self.min_timeout, timeout)
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            result = JobResult(
                job_id=job_id,
                status=JobStatus.SUCCESS,
                output=output,
                error=None,
                start_time=start_time,
                end_time=end_time,
                duration=duration
            )
            
            print(f"✅ [EXECUTOR] Job {job_id} completed in {duration:.2f}s")
            
        except asyncio.TimeoutError:
            end_time = time.time()
            duration = end_time - start_time
            
            result = JobResult(
                job_id=job_id,
                status=JobStatus.TIMEOUT,
                output={},
                error="Job execution timeout",
                start_time=start_time,
                end_time=end_time,
                duration=duration
            )
            
            print(f"⏱️  [EXECUTOR] Job {job_id} timeout after {duration:.2f}s")
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            result = JobResult(
                job_id=job_id,
                status=JobStatus.FAILURE,
                output={},
                error=str(e),
                start_time=start_time,
                end_time=end_time,
                duration=duration
            )
            
            print(f"❌ [EXECUTOR] Job {job_id} failed: {e}")
        
        finally:
            # Stop heartbeat
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Call result callback
        if self.result_callback:
            try:
                await self.result_callback(result)
            except Exception as e:
                print(f"[EXECUTOR] Error in result callback: {e}")
        
        return result
    
    async def _heartbeat_loop(self, job_id: str):
        """Send periodic heartbeats during job execution"""
        try:
            while True:
                await asyncio.sleep(5)  # Every 5 seconds
                
                # Calculate progress (rough estimate)
                metadata = self.job_metadata.get(job_id, {})
                start_time = metadata.get('start_time', time.time())
                elapsed = time.time() - start_time
                
                # Simple progress estimation (TODO: improve)
                progress = min(0.95, elapsed / 60.0)  # Assume 60s jobs
                
                # Call heartbeat callbacks
                for callback in self.heartbeat_callbacks:
                    try:
                        await callback(job_id, progress)
                    except Exception as e:
                        print(f"[EXECUTOR] Heartbeat callback error: {e}")
        
        except asyncio.CancelledError:
            pass
    
    def get_active_job_count(self) -> int:
        """Get number of active jobs"""
        return len(self.active_jobs)
    
    def is_job_running(self, job_id: str) -> bool:
        """Check if job is running"""
        return job_id in self.active_jobs
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        if job_id in self.active_jobs:
            task = self.active_jobs[job_id]
            task.cancel()
            print(f"[EXECUTOR] Cancelled job {job_id}")
            return True
        return False
    
    def get_capabilities(self) -> list:
        """Get list of supported job types"""
        return list(self.runners.keys())
    

    # Add to ExecutionEngine class in agent/executor/engine.py

    def get_job_type_capabilities(self) -> dict:
        """
        Get detailed capabilities for each job type
        Returns metadata about what each runner can do
        """
        return {
            'shell': {
                'description': 'Execute shell commands',
                'requirements': [],
                'avg_duration': 10,
                'risk_level': 'medium'
            },
            'docker': {
                'description': 'Run jobs in Docker containers',
                'requirements': ['docker'],
                'avg_duration': 60,
                'risk_level': 'low'
            },
            'docker_build': {
                'description': 'Build Docker images',
                'requirements': ['docker'],
                'avg_duration': 120,
                'risk_level': 'low'
            },
            'malware_scan': {
                'description': 'Scan files for malware',
                'requirements': ['clamav'],
                'avg_duration': 30,
                'risk_level': 'high'
            },
            'port_scan': {
                'description': 'Network port scanning',
                'requirements': ['nmap'],
                'avg_duration': 60,
                'risk_level': 'medium'
            },
            'hash_crack': {
                'description': 'Password hash cracking',
                'requirements': ['hashcat'],
                'avg_duration': 180,
                'risk_level': 'medium'
            },
            'threat_intel': {
                'description': 'Query threat intelligence feeds',
                'requirements': ['network'],
                'avg_duration': 15,
                'risk_level': 'low'
            }
        }