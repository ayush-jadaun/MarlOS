import pytest
import pytest_asyncio
import docker
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# Assuming runners are in: agent.executor.docker
from agent.executor.docker import DockerRunner, DockerBuildRunner

pytestmark = pytest.mark.asyncio

# Try to connect to Docker. If it fails, skip all tests in this file.
try:
    docker.from_env()
    docker_available = True
except Exception:
    docker_available = False

# Skip all tests in this module if Docker is not available
pytestmark = pytest.mark.skipif(not docker_available, reason="Docker is not running or not installed")

@pytest_asyncio.fixture
def mock_docker_client():
    """Mocks the docker client and its methods."""
    mock_client = MagicMock()
    
    # Mock for DockerRunner
    mock_container_logs = b'hello from container'
    mock_client.containers.run = MagicMock(return_value=mock_container_logs)
    
    # Mock for DockerBuildRunner
    mock_image = MagicMock()
    mock_image.id = 'img-123'
    build_logs = [{'stream': 'Step 1/2 : FROM ubuntu'}, {'stream': 'Step 2/2 : CMD echo'}]
    mock_client.images.build = MagicMock(return_value=(mock_image, build_logs))
    
    # Mock image.get for pull check
    mock_client.images.get = MagicMock()
    
    with patch('docker.from_env', return_value=mock_client) as mock_patch:
        yield mock_client

async def test_docker_runner_success(mock_docker_client):
    """Test a successful Docker run."""
    runner = DockerRunner()
    assert runner.available is True
    
    job = {
        'payload': {
            'image': 'ubuntu:latest',
            'command': 'echo "hello from container"'
        }
    }
    
    # Mock .get to simulate image already exists
    mock_docker_client.images.get.return_value = MagicMock()
    
    result = await runner.run(job)
    
    assert result['success'] is True
    assert result['output'] == 'hello from container'
    mock_docker_client.containers.run.assert_called_once()
    
async def test_docker_runner_pulls_image(mock_docker_client):
    """Test that the runner pulls an image if it's not found."""
    runner = DockerRunner()
    
    job = {'payload': {'image': 'alpine', 'command': 'ls'}}
    
    # Mock .get to raise ImageNotFound, triggering a pull
    mock_docker_client.images.get.side_effect = docker.errors.ImageNotFound("not found")
    mock_docker_client.images.pull = AsyncMock() # Mock the pull method
    
    # We patch to_thread as it's used for blocking calls
    with patch('asyncio.to_thread', new=AsyncMock(side_effect=lambda func, *args, **kwargs: func(*args, **kwargs))) as mock_to_thread:
        await runner.run(job)

    # Check that .get was called, then .pull, then .run
    assert mock_docker_client.images.get.called
    assert mock_docker_client.images.pull.called
    assert mock_docker_client.containers.run.called

async def test_docker_build_runner_success(mock_docker_client):
    """Test a successful Docker build."""
    runner = DockerBuildRunner()
    assert runner.available is True
    
    job = {
        'job_id': 'job-build-1',
        'payload': {
            'dockerfile': 'FROM ubuntu\nCMD echo "hello"',
            'tag': 'my-test-image'
        }
    }
    
    # Mock tempfile and file open
    mock_temp = patch('tempfile.TemporaryDirectory', return_value=MagicMock(__enter__=MagicMock(return_value='/tmp/mockbuild')))
    mock_file = patch('builtins.open', mock_open())
    
    with mock_temp, mock_file:
        with patch('asyncio.to_thread', new=AsyncMock(side_effect=lambda func, *args, **kwargs: func(*args, **kwargs))):
            result = await runner.run(job)
    
    assert result['success'] is True
    assert result['image_id'] == 'img-123'
    assert 'Step 1/2' in result['logs']