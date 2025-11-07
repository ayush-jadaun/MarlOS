import asyncio
import time
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# Assuming your engine is in: agent.executor.engine
# And your schema is in: agent.schema.schema
from agent.executor.engine import ExecutionEngine
from agent.schema.schema import JobStatus, JobResult, JobBackup
from agent.config import ExecutorConfig # You'll need to import your config class

# Use pytest-asyncio for all tests
pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
def test_config():
    """Provides a basic ExecutorConfig."""
    # Mock or create a real config object as needed
    class MockExecutorConfig:
        max_concurrent_jobs = 5
    return MockExecutorConfig()

@pytest_asyncio.fixture
def engine(test_config):
    """Provides a fresh ExecutionEngine for each test."""
    # Use min_timeout=0.01 for tests to allow short timeouts
    return ExecutionEngine(node_id="test_node", config=test_config, min_timeout=0.01)

@pytest_asyncio.fixture
def mock_job():
    """Provides a sample job dictionary."""
    return {
        'job_id': 'job-123',
        'job_type': 'test_runner',
        'payload': {'data': 'test'},
        'deadline': time.time() + 300 # 5 min deadline
    }

async def test_engine_register_and_get_capabilities(engine):
    """Test that runners can be registered and capabilities are returned."""
    mock_runner = AsyncMock()
    engine.register_runner("shell", mock_runner)
    engine.register_runner("docker", mock_runner)
    
    caps = engine.get_capabilities()
    assert "shell" in caps
    assert "docker" in caps
    assert len(caps) == 2

async def test_engine_execute_job_success(engine, mock_job):
    """Test a successful job execution from start to finish."""

    # 1. Create mock runner and callbacks
    mock_runner_output = {'stdout': 'success', 'success': True}
    runner_called = []  # Track calls

    # Create a real async function that takes some time
    async def mock_runner_func(job):
        runner_called.append(job)
        await asyncio.sleep(0.02)  # Small delay to ensure non-zero duration
        return mock_runner_output

    mock_result_cb = AsyncMock()
    mock_heartbeat_cb = AsyncMock()

    # 2. Register components (use the real async function, not wrapped in AsyncMock)
    engine.register_runner("test_runner", mock_runner_func)
    engine.set_result_callback(mock_result_cb)
    engine.add_heartbeat_callback(mock_heartbeat_cb)

    # 3. Execute job
    result = await engine.execute_job(mock_job)

    # 4. Assertions
    assert result.status == JobStatus.SUCCESS
    assert result.output == mock_runner_output
    assert result.error is None
    assert result.duration > 0, f"Expected duration > 0, got {result.duration}"
    assert engine.get_active_job_count() == 0

    # Check that runner and callbacks were called
    assert len(runner_called) == 1
    assert runner_called[0] == mock_job
    mock_result_cb.assert_called_once_with(result)

    # Heartbeat runs in a separate task, we check it was *at least*
    # not erroring. A full test is in test_recovery_manager
    # In this fast test, it likely didn't have time to fire.
    assert mock_heartbeat_cb.call_count == 0

async def test_engine_job_failure(engine, mock_job):
    """Test when the job runner itself raises an exception."""
    
    # 1. Create failing runner
    error_message = "This job failed!"
    mock_runner = AsyncMock(side_effect=Exception(error_message))
    mock_result_cb = AsyncMock()
    
    # 2. Register
    engine.register_runner("test_runner", mock_runner)
    engine.set_result_callback(mock_result_cb)
    
    # 3. Execute
    result = await engine.execute_job(mock_job)
    
    # 4. Assertions
    assert result.status == JobStatus.FAILURE
    assert result.error == str(Exception(error_message))
    assert engine.get_active_job_count() == 0
    mock_result_cb.assert_called_once_with(result)

async def test_engine_job_timeout(engine, mock_job):
    """Test when a job exceeds its deadline."""

    # 1. Create a job with a very short timeout
    short_job = mock_job.copy()
    short_job['deadline'] = time.time() + 0.05  # 50ms

    # 2. Create a runner that sleeps for longer than the timeout
    async def slow_runner_func(job):
        await asyncio.sleep(0.3)  # Sleep longer than timeout
        return {}

    mock_result_cb = AsyncMock()

    # 3. Register (use real async function)
    engine.register_runner("test_runner", slow_runner_func)
    engine.set_result_callback(mock_result_cb)

    # 4. Execute
    result = await engine.execute_job(short_job)

    # 5. Assertions
    assert result.status == JobStatus.TIMEOUT, f"Expected TIMEOUT, got {result.status}"
    assert "Job execution timeout" in result.error
    assert engine.get_active_job_count() == 0
    mock_result_cb.assert_called_once_with(result)

async def test_engine_job_type_not_found(engine, mock_job):
    """Test executing a job with no registered runner."""
    
    # Note: No runner is registered
    result = await engine.execute_job(mock_job)
    
    assert result.status == JobStatus.FAILURE
    assert "No runner for job type: test_runner" in result.error

async def test_engine_concurrency_limit(engine, mock_job):
    """Test that the engine correctly limits concurrent jobs."""

    # 1. Set config to 1 job
    engine.config.max_concurrent_jobs = 1

    # 2. Create a slow runner
    async def slow_runner_func(job):
        await asyncio.sleep(0.3)
        return {'success': True}

    engine.register_runner("test_runner", slow_runner_func)

    # 3. Start the first job in the background
    job1 = mock_job.copy()
    job1_task = asyncio.create_task(engine.execute_job(job1))

    # Give the first job time to start
    await asyncio.sleep(0.05)
    assert engine.get_active_job_count() == 1

    # 4. Try to start a second job
    job2 = mock_job.copy()
    job2['job_id'] = 'job-456'
    result2 = await engine.execute_job(job2)

    # 5. Assert second job was rejected
    assert result2.status == JobStatus.FAILURE
    assert "Max concurrent jobs reached" in result2.error

    # 6. Wait for first job to finish
    result1 = await job1_task
    assert result1.status == JobStatus.SUCCESS  # It was a slow runner, not a timeout
    assert engine.get_active_job_count() == 0