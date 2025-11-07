import asyncio
import pytest
import pytest_asyncio
import hashlib
import socket
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# Assuming runners are in: agent.executor.security
from agent.executor.security import (
    MalwareScanRunner, 
    PortScanRunner, 
    HashCrackRunner, 
    ThreatIntelRunner
)

pytestmark = pytest.mark.asyncio

# --- Mocks for aiohttp ---

@pytest_asyncio.fixture
def mock_aiohttp_session():
    """
    Mocks aiohttp.ClientSession and its nested session.get() context manager.
    """
    
    # 1. This is the final object (the 'resp')
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.read = AsyncMock(return_value=b'file content')
    mock_response.text = AsyncMock(return_value="password\n123456\nadmin\n")
    
    # 2. This is the object returned by session.get()
    # It needs to be an async context manager
    mock_response_manager = AsyncMock()
    mock_response_manager.__aenter__.return_value = mock_response  # This becomes 'resp'

    # 3. This is the session object
    mock_session = AsyncMock()
    
    # ===== THIS IS THE FIX =====
    # .get should be a *regular* function (MagicMock) that *returns*
    # the async context manager, not an async function itself.
    mock_session.get = MagicMock(return_value=mock_response_manager)
    # ===== END OF FIX =====

    # 4. This is the top-level ClientSession()
    # It also needs to be an async context manager
    mock_session_manager = AsyncMock()
    mock_session_manager.__aenter__.return_value = mock_session  # This becomes 'session'

    # 5. Patch 'aiohttp.ClientSession' to return the top-level manager
    with patch('aiohttp.ClientSession', return_value=mock_session_manager) as mock_patch:
        # Pass back the mock_patch and the final mock_response
        # so the test can modify the response if needed.
        yield mock_patch, mock_response

# --- MalwareScanRunner Tests ---

@pytest_asyncio.fixture
def mock_subprocess():
    """Mocks asyncio.create_subprocess_exec."""
    
    # 1. Create a mock process object
    mock_process = AsyncMock()
    mock_process.communicate = AsyncMock(return_value=(b'mock output', b'mock error'))
    mock_process.returncode = 0
    mock_process.kill = MagicMock() # For timeout test

    # 2. Patch the subprocess creation function
    with patch('asyncio.create_subprocess_exec', return_value=mock_process) as mock_create:
        yield mock_create, mock_process

@pytest_asyncio.fixture
def mock_malware_deps(mock_aiohttp_session):
    """Mocks dependencies for MalwareScanRunner."""
    
    # 1. Mock subprocess for ClamAV
    mock_process = AsyncMock()
    mock_process.communicate = AsyncMock(return_value=(b'sample: OK', b''))
    mock_create_exec = patch('asyncio.create_subprocess_exec', return_value=mock_process)

    # 2. Mock file operations
    mock_temp_dir = patch('tempfile.TemporaryDirectory', return_value=MagicMock(__enter__=MagicMock(return_value='/tmp/mockdir')))
    mock_file_open = patch('builtins.open', mock_open(read_data=b'file content'))
    
    # 3. Mock hashlib
    mock_hash = MagicMock()
    mock_hash.hexdigest.return_value = 'mocked_hash'
    mock_hashlib = patch('hashlib.sha256', return_value=mock_hash)

    with mock_create_exec as mock_exec, \
         mock_temp_dir, \
         mock_file_open, \
         mock_hashlib:
        
        yield mock_exec, mock_process

async def test_malware_scan_clean(mock_malware_deps, mock_aiohttp_session):
    """Test a clean file scan with ClamAV."""
    mock_exec, mock_process = mock_malware_deps
    job = {'payload': {'file_url': 'http://example.com/clean.zip'}}
    
    runner = MalwareScanRunner()
    result = await runner.run(job)
    
    assert result['success'] is True
    assert result['infected'] is False
    assert result['scanner'] == 'clamav'

async def test_malware_scan_infected(mock_malware_deps, mock_aiohttp_session):
    """Test an infected file scan with ClamAV."""
    mock_exec, mock_process = mock_malware_deps
    
    # Override the communicate mock to return an infected result
    mock_process.communicate.return_value = (b'sample: Win.EICAR.Test-FOUND', b'')
    job = {'payload': {'file_url': 'http://example.com/infected.exe'}}
    
    runner = MalwareScanRunner()
    result = await runner.run(job)
    
    assert result['success'] is True
    assert result['infected'] is True

async def test_malware_scan_hash_mismatch(mock_malware_deps, mock_aiohttp_session):
    """Test file download with a hash mismatch."""
    job = {
        'payload': {
            'file_url': 'http://example.com/file.zip',
            'file_hash': 'different_hash' # Our mock returns 'mocked_hash'
        }
    }
    
    runner = MalwareScanRunner()
    with pytest.raises(Exception, match="Hash mismatch"):
        await runner.run(job)

async def test_malware_scan_heuristic_fallback(mock_malware_deps, mock_aiohttp_session):
    """Test heuristic scan when ClamAV is not found."""
    mock_exec, mock_process = mock_malware_deps
    mock_aiohttp_session_obj, mock_response = mock_aiohttp_session
    
    # 1. Simulate ClamAV not being installed
    mock_exec.side_effect = FileNotFoundError
    
    # 2. Simulate a file with a suspicious string
    mock_response.read.return_value = b'file with powershell.exe -enc content'
    
    job = {'payload': {'file_url': 'http://example.com/suspicious.ps1'}}
    
    runner = MalwareScanRunner()
    result = await runner.run(job)
    
    assert result['success'] is True
    assert result['infected'] is True
    assert result['scanner'] == 'heuristic'
    assert 'powershell.exe -enc' in result['scan_output']

# --- PortScanRunner Tests ---

async def test_port_scan_nmap(mock_subprocess):
    """Test port scan using nmap."""
    mock_create, mock_process = mock_subprocess
    
    # Mock nmap XML output
    nmap_output = b"""
    <nmaprun>
    <host><ports>
    <port protocol="tcp" portid="80"><state state="open" .../></port>
    <port protocol="tcp" portid="443"><state state="open" .../></port>
    </ports></host>
    </nmaprun>
    """
    mock_process.communicate.return_value = (nmap_output, b'')
    
    job = {'payload': {'target': '1.1.1.1', 'ports': '80,443'}}
    runner = PortScanRunner()
    result = await runner.run(job)
    
    assert result['success'] is True
    assert result['scanner'] == 'nmap'
    assert result['open_ports'] == [80, 443]

async def test_port_scan_socket_fallback(mock_subprocess):
    """Test port scan using socket fallback when nmap is missing."""
    mock_create, mock_process = mock_subprocess
    
    # 1. Simulate nmap not found
    mock_create.side_effect = FileNotFoundError
    
    # 2. Mock socket.socket
    mock_sock_instance = MagicMock()
    # Simulate port 80 open (returns 0) and 81 closed (returns 1)
    mock_sock_instance.connect_ex.side_effect = [0, 1] 
    mock_sock_class = MagicMock(return_value=mock_sock_instance)

    with patch('socket.socket', mock_sock_class):
        job = {'payload': {'target': '1.1.1.1', 'ports': '80-81'}}
        runner = PortScanRunner()
        result = await runner.run(job)
        
        assert result['success'] is True
        assert result['scanner'] == 'socket'
        assert result['open_ports'] == [80]

# --- HashCrackRunner Tests ---

async def test_hash_crack_success(mock_aiohttp_session):
    """Test a successful hash crack."""
    # Our mock wordlist is "password\n123456\nadmin\n"
    # MD5('password') = 5f4dcc3b5aa765d61d8327deb882cf99
    job = {
        'payload': {
            'hash': '5f4dcc3b5aa765d61d8327deb882cf99',
            'algorithm': 'md5',
            'wordlist_url': 'http://example.com/wordlist.txt',
            'start_line': 0,
            'end_line': 10
        }
    }
    
    runner = HashCrackRunner()
    result = await runner.run(job)
    
    assert result['success'] is True
    assert result['cracked'] is True
    assert result['password'] == 'password'

async def test_hash_crack_fail(mock_aiohttp_session):
    """Test a failed hash crack."""
    job = {
        'payload': {
            'hash': 'non_existent_hash', # Not in our mock wordlist
            'algorithm': 'md5',
            'wordlist_url': 'http://example.com/wordlist.txt',
            'start_line': 0,
            'end_line': 10
        }
    }
    
    runner = HashCrackRunner()
    result = await runner.run(job)
    
    assert result['success'] is True
    assert result['cracked'] is False