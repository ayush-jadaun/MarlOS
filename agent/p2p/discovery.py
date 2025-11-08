"""
Advanced Peer Discovery
Implements multiple discovery mechanisms for robust peer finding
"""
import asyncio
import socket
import struct
import json
from typing import Set, Dict
import time


class PeerDiscovery:
    """
    Multi-mechanism peer discovery:
    1. mDNS-like multicast
    2. DHT (Distributed Hash Table)
    3. Bootstrap nodes
    4. Peer exchange
    """
    
    def __init__(self, node_id: str, port: int):
        self.node_id = node_id
        self.port = port
        
        # Discovered peers
        self.discovered_peers: Dict[str, dict] = {}
        
        # Multicast config
        self.multicast_group = '239.255.255.250'
        self.multicast_port = 5353
        
        # Bootstrap nodes (hardcoded fallbacks)
        self.bootstrap_nodes = [
            'marlos-bootstrap-1.example.com:5555',
            'marlos-bootstrap-2.example.com:5555'
        ]
        
        self.running = False
    
    async def start(self):
        """Start all discovery mechanisms"""
        self.running = True
        
        # Start discovery methods
        asyncio.create_task(self._multicast_discovery())
        asyncio.create_task(self._bootstrap_discovery())
        asyncio.create_task(self._peer_exchange())
        
        print("[DISCOVERY] Peer discovery started")
    
    async def stop(self):
        """Stop discovery"""
        self.running = False
    
    async def _multicast_discovery(self):
        """
        mDNS-like multicast discovery
        Broadcasts presence on local network
        """
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Enable multicast
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_TTL,
            struct.pack('b', 1)
        )
        
        while self.running:
            try:
                # Broadcast announcement
                announcement = {
                    'type': 'peer_announce',
                    'node_id': self.node_id,
                    'port': self.port,
                    'timestamp': time.time()
                }
                
                message = json.dumps(announcement).encode()
                sock.sendto(message, (self.multicast_group, self.multicast_port))
                
                await asyncio.sleep(5)
            
            except Exception as e:
                print(f"[DISCOVERY] Multicast error: {e}")
                await asyncio.sleep(10)
        
        sock.close()
    
    async def _bootstrap_discovery(self):
        """
        Connect to bootstrap nodes
        """
        for bootstrap in self.bootstrap_nodes:
            try:
                host, port = bootstrap.split(':')
                
                # Try to connect
                reader, writer = await asyncio.open_connection(host, int(port))
                
                # Request peer list
                request = {'type': 'get_peers', 'node_id': self.node_id}
                writer.write(json.dumps(request).encode() + b'\n')
                await writer.drain()
                
                # Receive peers
                data = await reader.read(4096)
                response = json.loads(data.decode())
                
                peers = response.get('peers', [])
                for peer in peers:
                    self.discovered_peers[peer['node_id']] = peer
                
                writer.close()
                await writer.wait_closed()
                
                print(f"[DISCOVERY] Bootstrap: discovered {len(peers)} peers from {bootstrap}")
            
            except Exception as e:
                print(f"[DISCOVERY] Bootstrap {bootstrap} failed: {e}")
        
        await asyncio.sleep(60)  # Retry every minute
    
    async def _peer_exchange(self):
        """
        Peer exchange protocol
        Ask known peers for their peer lists (PEX protocol)
        """
        while self.running:
            await asyncio.sleep(30)

            # Ask each known peer for their peers
            for peer_id, peer_info in list(self.discovered_peers.items()):
                try:
                    # Get peer address
                    peer_host = peer_info.get('host')
                    peer_port = peer_info.get('port', self.port)

                    if not peer_host:
                        continue

                    # Connect to peer
                    try:
                        reader, writer = await asyncio.wait_for(
                            asyncio.open_connection(peer_host, peer_port),
                            timeout=5.0
                        )
                    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                        # Peer not responding
                        continue

                    # Request peer list
                    request = {
                        'type': 'peer_exchange',
                        'node_id': self.node_id,
                        'timestamp': time.time()
                    }

                    writer.write(json.dumps(request).encode() + b'\n')
                    await writer.drain()

                    # Receive peer list (with timeout)
                    try:
                        data = await asyncio.wait_for(reader.read(8192), timeout=5.0)
                        if data:
                            response = json.loads(data.decode())

                            # Extract peers
                            peers = response.get('peers', [])

                            for peer in peers:
                                # Don't add ourselves
                                if peer['node_id'] == self.node_id:
                                    continue

                                # Add to discovered peers
                                if peer['node_id'] not in self.discovered_peers:
                                    self.discovered_peers[peer['node_id']] = {
                                        'host': peer.get('host'),
                                        'port': peer.get('port', self.port),
                                        'discovered_at': time.time(),
                                        'discovered_via': 'pex',
                                        'referred_by': peer_id
                                    }
                                    print(f"[DISCOVERY] PEX: Discovered {peer['node_id']} via {peer_id}")

                    except (asyncio.TimeoutError, json.JSONDecodeError):
                        pass

                    writer.close()
                    await writer.wait_closed()

                except Exception as e:
                    print(f"[DISCOVERY] Peer exchange with {peer_id} failed: {e}")
    
    def get_discovered_peers(self) -> Dict[str, dict]:
        """Get all discovered peers"""
        return self.discovered_peers.copy()
    
    def add_peer(self, peer_id: str, peer_info: dict):
        """Manually add peer"""
        self.discovered_peers[peer_id] = peer_info