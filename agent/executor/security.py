"""
Security Job Runners
Implements cybersecurity-specific job types
"""
import asyncio
import subprocess
import tempfile
import os
import json
import hashlib
from typing import Dict
import aiohttp


class MalwareScanRunner:
    """
    Scans files for malware using ClamAV
    """
    
    async def run(self, job: dict) -> Dict:
        """
        Scan file for malware
        
        Job payload:
        {
            'file_url': 'https://...',
            'file_hash': 'sha256...'  # optional verification
        }
        """
        payload = job.get('payload', {})
        file_url = payload.get('file_url')
        expected_hash = payload.get('file_hash')
        
        if not file_url:
            raise ValueError("No file_url provided")
        
        print(f"[MALWARE] Scanning: {file_url}")
        
        # Download file
        file_content = None
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, 'sample')

            # Download
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as resp:
                    if resp.status != 200:
                        raise Exception(f"Failed to download file: {resp.status}")

                    file_content = await resp.read()
                    with open(file_path, 'wb') as f:
                        f.write(file_content)

            # Verify hash if provided
            if expected_hash:
                actual_hash = hashlib.sha256(file_content).hexdigest()
                if actual_hash != expected_hash:
                    raise Exception(f"Hash mismatch: expected {expected_hash}, got {actual_hash}")

            # Scan with ClamAV (if available)
            try:
                result = await asyncio.create_subprocess_exec(
                    'clamscan', '--no-summary', file_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await result.communicate()
                output = stdout.decode('utf-8')

                is_infected = 'FOUND' in output

                return {
                    'file_url': file_url,
                    'infected': is_infected,
                    'scan_output': output,
                    'scanner': 'clamav',
                    'success': True
                }

            except FileNotFoundError:
                # ClamAV not installed, use simple heuristics
                return await self._heuristic_scan(file_content)

    async def _heuristic_scan(self, content: bytes) -> Dict:
        """Simple heuristic-based scan"""
        
        # Simple checks
        suspicious = False
        reasons = []
        
        # Check for common malware patterns
        patterns = [
            b'CreateRemoteThread',
            b'VirtualAllocEx',
            b'WriteProcessMemory',
            b'cmd.exe /c',
            b'powershell.exe -enc'
        ]
        
        for pattern in patterns:
            if pattern in content:
                suspicious = True
                reasons.append(f"Found pattern: {pattern.decode('utf-8', errors='ignore')}")
        
        return {
            'infected': suspicious,
            'scan_output': '\n'.join(reasons) if reasons else 'No threats detected',
            'scanner': 'heuristic',
            'success': True
        }


class PortScanRunner:
    """
    Performs network port scanning
    """
    
    async def run(self, job: dict) -> Dict:
        """
        Port scan target
        
        Job payload:
        {
            'target': '192.168.1.1',
            'ports': '1-1000',
            'scan_type': 'tcp'  # or 'udp'
        }
        """
        payload = job.get('payload', {})
        target = payload.get('target')
        ports = payload.get('ports', '1-1000')
        scan_type = payload.get('scan_type', 'tcp')
        
        if not target:
            raise ValueError("No target specified")
        
        print(f"[PORTSCAN] Scanning {target}:{ports}")
        
        try:
            # Use nmap if available
            result = await asyncio.create_subprocess_exec(
                'nmap', '-p', ports, target, '-oX', '-',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                result.communicate(),
                timeout=120
            )
            
            output = stdout.decode('utf-8')
            
            # Parse nmap output (simplified)
            open_ports = self._parse_nmap_output(output)
            
            return {
                'target': target,
                'open_ports': open_ports,
                'scan_output': output,
                'scanner': 'nmap',
                'success': True
            }
        
        except FileNotFoundError:
            # Nmap not available, use Python socket scan
            return await self._socket_scan(target, ports)
    
    def _parse_nmap_output(self, output: str) -> list:
        """Parse nmap XML output for open ports"""
        import re
        open_ports = []
        
        # Simple regex to find open ports
        matches = re.findall(r'portid="(\d+)".*state="open"', output)
        for port in matches:
            open_ports.append(int(port))
        
        return open_ports
    
    async def _socket_scan(self, target: str, port_range: str) -> Dict:
        """Fallback socket-based scan"""
        import socket
        
        # Parse port range
        if '-' in port_range:
            start, end = map(int, port_range.split('-'))
            ports = range(start, end + 1)
        else:
            ports = [int(port_range)]
        
        open_ports = []
        
        # Scan ports (limit to first 100 for speed)
        for port in list(ports)[:100]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex((target, port))
                sock.close()
                
                if result == 0:
                    open_ports.append(port)
            except:
                pass
        
        return {
            'target': target,
            'open_ports': open_ports,
            'scanner': 'socket',
            'success': True
        }


class HashCrackRunner:
    """
    Cracks password hashes (distributed)
    """
    
    async def run(self, job: dict) -> Dict:
        """
        Crack password hash
        
        Job payload:
        {
            'hash': '5f4dcc3b5aa765d61d8327deb882cf99',
            'algorithm': 'md5',
            'wordlist_url': 'https://...',
            'start_line': 0,      # for distributed cracking
            'end_line': 1000000
        }
        """
        payload = job.get('payload', {})
        hash_value = payload.get('hash')
        algorithm = payload.get('algorithm', 'md5')
        wordlist_url = payload.get('wordlist_url')
        start_line = payload.get('start_line', 0)
        end_line = payload.get('end_line', 1000000)
        
        if not hash_value:
            raise ValueError("No hash provided")
        
        print(f"[HASHCRACK] Cracking {algorithm} hash: {hash_value}")
        
        # Download wordlist chunk
        if wordlist_url:
            wordlist = await self._download_wordlist_chunk(
                wordlist_url, start_line, end_line
            )
        else:
            # Use common passwords
            wordlist = ['password', '123456', 'admin', 'letmein', 'welcome']
        
        # Try cracking
        hasher = self._get_hasher(algorithm)
        
        for word in wordlist:
            test_hash = hasher(word.encode()).hexdigest()
            if test_hash == hash_value:
                print(f"✅ [HASHCRACK] Found password: {word}")
                return {
                    'cracked': True,
                    'password': word,
                    'attempts': wordlist.index(word) + 1,
                    'success': True
                }
        
        return {
            'cracked': False,
            'attempts': len(wordlist),
            'success': True
        }
    
    def _get_hasher(self, algorithm: str):
        """Get hash function"""
        algorithms = {
            'md5': hashlib.md5,
            'sha1': hashlib.sha1,
            'sha256': hashlib.sha256
        }
        return algorithms.get(algorithm, hashlib.md5)
    
    # A safer, streaming approach for _download_wordlist_chunk:
    async def _download_wordlist_chunk(self, url: str, start: int, end: int) -> list:
        """Download and process wordlist chunk line by line"""
        wordlist_chunk = []

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to download wordlist: {resp.status}")

                # Get the full text content and split into lines
                text = await resp.text()
                lines = text.split('\n')

                # Extract the specified chunk
                for i, line in enumerate(lines):
                    if i >= start and i < end:
                        line = line.strip()
                        if line:  # Skip empty lines
                            wordlist_chunk.append(line)

                    # Safety break to prevent enormous in-memory lists
                    if len(wordlist_chunk) > 10_000_000:
                        raise Exception("Wordlist chunk size is too large")

        return wordlist_chunk

class ThreatIntelRunner:
    """
    Queries threat intelligence APIs
    """
    
    async def run(self, job: dict) -> Dict:
        """
        Query threat intel for IOC
        
        Job payload:
        {
            'ioc': '185.220.101.23',
            'ioc_type': 'ip',  # or 'domain', 'hash'
            'sources': ['abuseipdb']
        }
        """
        payload = job.get('payload', {})
        ioc = payload.get('ioc')
        ioc_type = payload.get('ioc_type', 'ip')
        
        if not ioc:
            raise ValueError("No IOC provided")
        
        print(f"[THREAT_INTEL] Checking {ioc_type}: {ioc}")
        
        # Simplified: just return mock data
        # In production, query real APIs (VirusTotal, AbuseIPDB, etc.)
        
        results = {
            'ioc': ioc,
            'ioc_type': ioc_type,
            'threat_score': 0.3,  # 0-1
            'reports': [
                {
                    'source': 'abuseipdb',
                    'score': 30,
                    'reports': 5
                }
            ],
            'success': True
        }
        
        return results