import asyncio
import time
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# Assuming your manager is in: agent.executor.recovery
from agent.executor.recovery import RecoveryManager
from agent.schema.schema import JobBackup # You'll need this schema

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
async def manager():
    """Provides a RecoveryManager. We stop it after the test."""
    # Use a short check interval for tests (0.05 seconds)
    m = RecoveryManager(node_id="test-backup-node", check_interval=0.05)
    yield m
    # Cleanup: ensure the monitor loop is stopped
    await m.stop()

@pytest_asyncio.fixture
def mock_job_backup():
    """Provides a sample JobBackup object."""
    job = {'job_id': 'job-failover', 'payload': {}}
    return JobBackup(
        job_id='job-failover',
        job=job,
        primary_node='primary-node',
        backup_node='test-backup-node',
        last_heartbeat=time.time(),
        progress=0.0
    )

async def test_recovery_manager_register(manager, mock_job_backup):
    """Test that a job can be registered for backup."""
    job = mock_job_backup.job
    job_id = mock_job_backup.job_id

    assert manager.get_backup_count() == 0
    manager.register_backup(job_id, job, 'primary-node')

    assert manager.get_backup_count() == 1
    assert job_id in manager.backup_jobs
    assert manager.backup_jobs[job_id].primary_node == 'primary-node'

async def test_recovery_manager_heartbeat_update(manager, mock_job_backup):
    """Test that heartbeats update the last_heartbeat time."""
    job_id = mock_job_backup.job_id
    manager.backup_jobs[job_id] = mock_job_backup
    
    original_time = manager.backup_jobs[job_id].last_heartbeat
    
    await asyncio.sleep(0.05)
    manager.update_heartbeat(job_id, 0.5)
    
    assert manager.backup_jobs[job_id].last_heartbeat > original_time
    assert manager.backup_jobs[job_id].progress == 0.5

async def test_recovery_manager_takeover_on_timeout(manager, mock_job_backup):
    """Test the core functionality: job takeover after a timeout."""
    
    # 1. Set a very short timeout for the test
    manager.heartbeat_timeout = 0.1  # 100ms
    
    # 2. Set the mock executor callback
    mock_executor_cb = AsyncMock(return_value="JobResultMock")
    manager.set_executor_callback(mock_executor_cb)
    
    # 3. Register the job
    job_id = mock_job_backup.job_id
    manager.backup_jobs[job_id] = mock_job_backup
    
    # 4. Start the monitoring loop
    await manager.start()
    
    # 5. Wait for *longer* than the timeout
    await asyncio.sleep(0.2)
    
    # 6. Assertions
    # Check that the executor was called to take over the job
    mock_executor_cb.assert_called_once_with(mock_job_backup.job)
    # Check that the job was removed from the backup list
    assert manager.get_backup_count() == 0

async def test_recovery_manager_no_takeover_with_heartbeats(manager, mock_job_backup):
    """Test that jobs are NOT taken over if heartbeats are received."""
    
    # 1. Set a short timeout
    manager.heartbeat_timeout = 0.2  # 200ms
    
    # 2. Set mock callback
    mock_executor_cb = AsyncMock()
    manager.set_executor_callback(mock_executor_cb)
    
    # 3. Register job
    job_id = mock_job_backup.job_id
    manager.backup_jobs[job_id] = mock_job_backup
    
    # 4. Start monitoring
    await manager.start()
    
    # 5. Send a heartbeat *before* the timeout
    await asyncio.sleep(0.1)
    manager.update_heartbeat(job_id, 0.5)
    
    # 6. Wait past the *original* timeout
    await asyncio.sleep(0.2)
    
    # 7. Assertions
    # The executor should NOT have been called
    mock_executor_cb.assert_not_called()
    # The job should still be in the backup list
    assert manager.get_backup_count() == 1