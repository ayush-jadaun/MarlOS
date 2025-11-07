import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# Assuming your runner is in: agent.executor.shell
from agent.executor.shell import ShellRunner

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
def runner():
    """Provides a default, sandboxed ShellRunner."""
    return ShellRunner(sandbox=True, whitelist_enabled=True)

@pytest_asyncio.fixture
def mock_subprocess():
    """Mocks asyncio.create_subprocess_exec."""
    
    # 1. Create a mockpytest process object
    mock_process = AsyncMock()
    mock_process.communicate = AsyncMock(return_value=(b'hello world', b''))
    mock_process.returncode = 0
    mock_process.kill = MagicMock() # For timeout test

    # 2. Patch the subprocess creation function
    with patch('asyncio.create_subprocess_exec', return_value=mock_process) as mock_create:
        yield mock_create, mock_process

async def test_shell_runner_success(runner, mock_subprocess):
    """Test a valid, whitelisted command."""
    mock_create, mock_process = mock_subprocess
    job = {'payload': {'command': 'ls -la /tmp'}}
    
    result = await runner.run(job)
    
    mock_create.assert_called_once_with(
        'ls', '-la', '/tmp', # Note: shlex.split correctly parses this
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=None,
        env=None
    )
    assert result['success'] is True
    assert result['stdout'] == 'hello world'
    assert result['returncode'] == 0

async def test_shell_runner_blacklisted(runner):
    """Test that a blacklisted command is rejected."""
    job = {'payload': {'command': 'rm -rf /'}}
    
    with pytest.raises(ValueError, match="Command 'rm' is blacklisted"):
        await runner.run(job)

async def test_shell_runner_not_whitelisted(runner):
    """Test that a non-whitelisted command is rejected."""
    job = {'payload': {'command': 'my_custom_script'}}
    
    with pytest.raises(ValueError, match="Command 'my_custom_script' not in whitelist"):
        await runner.run(job)

async def test_shell_runner_unsafe_mode_skips_whitelist(runner, mock_subprocess):
    """Test that 'allow_unsafe' skips the whitelist but NOT the blacklist."""
    mock_create, mock_process = mock_subprocess
    
    # This command is not whitelisted
    job = {'payload': {
        'command': 'my_custom_script --arg',
        'allow_unsafe': True
    }}
    
    # 1. Disable sandbox to allow 'allow_unsafe' to work
    runner.sandbox = False
    result = await runner.run(job)
    
    # It should have run successfully
    assert result['success'] is True
    mock_create.assert_called_with('my_custom_script', '--arg', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=None, env=None)
    
    # 2. Test that blacklist is STILL enforced
    job_blacklisted = {'payload': {
        'command': 'rm -rf /',
        'allow_unsafe': True
    }}
    with pytest.raises(ValueError, match="Command 'rm' is blacklisted"):
        await runner.run(job_blacklisted)

async def test_shell_runner_dangerous_pattern(runner):
    """Tests the original code's dangerous pattern check."""
    # NOTE: This test assumes you have *not* yet removed the dangerous_patterns check
    # as recommended in the previous review.
    job = {'payload': {'command': 'echo "hello ; world"'}}
    
    with pytest.raises(ValueError, match="potentially dangerous pattern ';'"):
        await runner.run(job)

async def test_shell_runner_timeout(runner, mock_subprocess):
    """Test that the runner correctly handles a command timeout."""
    mock_create, mock_process = mock_subprocess
    
    # Configure the mock process to simulate a timeout
    mock_process.communicate.side_effect = asyncio.TimeoutError
    
    job = {'payload': {'command': 'sleep 10', 'timeout': 0.1}}
    
    # We must patch asyncio.wait_for since it's called *inside* runner.run
    with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError):
        with pytest.raises(Exception, match="Command timeout after 0.1s"):
            await runner.run(job)
    
    # Check that the process was killed
    mock_process.kill.assert_called_once()