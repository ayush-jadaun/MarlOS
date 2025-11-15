"""
DHT Manager for Public Mode
Handles automatic peer discovery using Kademlia DHT
"""
import asyncio
import json
import time
from typing import List, Dict, Optional, Callable

try:
    from kademlia.network import Server
    KADEMLIA_AVAILABLE = True
except ImportError:
    KADEMLIA_AVAILABLE = False
    print("[DHT] Warning: kademlia not installed. Run: pip install kademlia")


class DHTManager:
    """
    Manages DHT for public mode peer discovery

    Uses Kademlia DHT (same as BitTorrent) for decentralized peer discovery.
    Peers announce themselves and can discover other peers automatically.
    """

    def __init__(self, node_id: str, port: int = 5559, bootstrap_nodes: List[tuple] = None):
        self.node_id = node_id
        self.port = port
        self.running = False

        # DHT Server
        if KADEMLIA_AVAILABLE:
            self.server = Server()
        else:
            self.server = None
            print("[DHT] DHT disabled - kademlia not available")

        # Bootstrap nodes (well-known nodes to help join the network)
        if bootstrap_nodes:
            self.bootstrap_nodes = bootstrap_nodes
        else:
            # Default bootstrap nodes (these would need to be set up)
            # For now, use placeholder - in production, deploy these on VPS
            self.bootstrap_nodes = [
                # Example: ("dht1.marlos.network", 5559),
                # Example: ("dht2.marlos.network", 5559),
            ]

        # Discovered peers
        self.discovered_peers: Dict[str, dict] = {}

        # Callbacks
        self.on_peer_discovered: Optional[Callable] = None

        # Statistics
        self.announce_count = 0
        self.discovery_count = 0

    async def start(self, my_ip: str, my_port: int, capabilities: List[str] = None):
        """
        Start DHT and announce this node

        Args:
            my_ip: This node's IP address
            my_port: This node's P2P port
            capabilities: List of job types this node can handle
        """
        if not KADEMLIA_AVAILABLE or not self.server:
            print("[DHT] Cannot start - kademlia not available")
            print("[DHT] Install with: pip install kademlia")
            return False

        print(f"[DHT] Starting DHT node on port {self.port}")

        try:
            # Start listening
            await self.server.listen(self.port)

            # Bootstrap to network
            if self.bootstrap_nodes:
                print(f"[DHT] Bootstrapping to {len(self.bootstrap_nodes)} nodes...")
                await self.server.bootstrap(self.bootstrap_nodes)
                print("[DHT] ✓ Connected to global MarlOS network")
            else:
                print("[DHT] Warning: No bootstrap nodes configured")
                print("[DHT] Running in standalone mode")

            self.running = True

            # Announce ourselves
            await self.announce(my_ip, my_port, capabilities or [])

            # Start background tasks
            asyncio.create_task(self._periodic_announce(my_ip, my_port, capabilities or []))
            asyncio.create_task(self._periodic_discovery())

            print("[DHT] ✓ DHT started successfully")
            return True

        except Exception as e:
            print(f"[DHT] Error starting DHT: {e}")
            return False

    async def announce(self, my_ip: str, my_port: int, capabilities: List[str]):
        """Announce this node to the DHT"""
        if not self.running or not self.server:
            return

        try:
            # Create announcement
            announcement = {
                "node_id": self.node_id,
                "ip": my_ip,
                "port": my_port,
                "capabilities": capabilities,
                "timestamp": time.time()
            }

            # Store in DHT
            key = f"marlos_peer_{self.node_id}"
            value = json.dumps(announcement)

            await self.server.set(key, value)

            self.announce_count += 1
            print(f"[DHT] Announced to network (#{self.announce_count})")

        except Exception as e:
            print(f"[DHT] Error announcing: {e}")

    async def _periodic_announce(self, my_ip: str, my_port: int, capabilities: List[str]):
        """Re-announce periodically (every 5 minutes)"""
        while self.running:
            await asyncio.sleep(300)  # 5 minutes
            await self.announce(my_ip, my_port, capabilities)

    async def _periodic_discovery(self):
        """Continuously discover new peers"""
        while self.running:
            try:
                # Sleep first to allow network to stabilize
                await asyncio.sleep(60)  # Check every minute

                # Discover peers
                # Note: This is a simplified version
                # Real implementation would crawl the DHT more thoroughly

                # For now, we rely on direct DHT lookups
                # In future, implement iterative DHT crawling

            except Exception as e:
                print(f"[DHT] Discovery error: {e}")
                await asyncio.sleep(60)

    async def discover_peers(self, max_peers: int = 20) -> List[dict]:
        """
        Discover peers from the DHT

        Args:
            max_peers: Maximum number of peers to return

        Returns:
            List of peer info dicts
        """
        if not self.running or not self.server:
            return []

        discovered = []

        try:
            # Note: Kademlia doesn't have a built-in way to iterate all keys
            # We'd need to implement key enumeration or use a known prefix

            # For now, this is a placeholder
            # Real implementation would:
            # 1. Use DHT crawling to find keys with prefix "marlos_peer_"
            # 2. Or maintain a separate "peer list" key that all peers update

            # Alternative approach: Use a well-known key for peer list
            peer_list_key = "marlos_global_peers"

            result = await self.server.get(peer_list_key)

            if result:
                peer_list = json.loads(result)
                discovered = peer_list.get('peers', [])[:max_peers]

                self.discovery_count += len(discovered)
                print(f"[DHT] Discovered {len(discovered)} peers")

                # Notify callback
                if self.on_peer_discovered:
                    for peer in discovered:
                        if peer['node_id'] != self.node_id:
                            await self.on_peer_discovered(peer)

        except Exception as e:
            print(f"[DHT] Error discovering peers: {e}")

        return discovered

    async def find_peer(self, node_id: str) -> Optional[dict]:
        """
        Find a specific peer by node ID

        Args:
            node_id: The node ID to search for

        Returns:
            Peer info dict or None
        """
        if not self.running or not self.server:
            return None

        try:
            key = f"marlos_peer_{node_id}"
            result = await self.server.get(key)

            if result:
                peer_info = json.loads(result)
                print(f"[DHT] Found peer: {node_id}")
                return peer_info

        except Exception as e:
            print(f"[DHT] Error finding peer {node_id}: {e}")

        return None

    async def find_peers_by_capability(self, capability: str, max_peers: int = 10) -> List[dict]:
        """
        Find peers that support a specific capability

        Args:
            capability: Job type capability (e.g., "docker", "shell")
            max_peers: Maximum peers to return

        Returns:
            List of matching peers
        """
        if not self.running or not self.server:
            return []

        # Get all peers
        all_peers = await self.discover_peers(max_peers * 2)

        # Filter by capability
        matching = [
            peer for peer in all_peers
            if capability in peer.get('capabilities', [])
        ]

        return matching[:max_peers]

    async def update_peer_list(self, peer_list: List[dict]):
        """
        Update the global peer list (collaborative)

        Each node contributes to a shared peer list in the DHT.
        This helps with peer discovery.
        """
        if not self.running or not self.server:
            return

        try:
            peer_list_key = "marlos_global_peers"

            # Get current list
            current = await self.server.get(peer_list_key)

            if current:
                existing = json.loads(current)
                existing_peers = {p['node_id']: p for p in existing.get('peers', [])}
            else:
                existing_peers = {}

            # Add/update peers
            for peer in peer_list:
                existing_peers[peer['node_id']] = peer

            # Keep only recent peers (last 1 hour)
            now = time.time()
            recent_peers = [
                p for p in existing_peers.values()
                if now - p.get('timestamp', 0) < 3600
            ]

            # Save updated list (limit to 100 peers)
            updated = {
                'updated_at': now,
                'peers': recent_peers[:100]
            }

            await self.server.set(peer_list_key, json.dumps(updated))

        except Exception as e:
            print(f"[DHT] Error updating peer list: {e}")

    def get_stats(self) -> dict:
        """Get DHT statistics"""
        return {
            'running': self.running,
            'announces': self.announce_count,
            'discovered': self.discovery_count,
            'bootstrap_nodes': len(self.bootstrap_nodes),
            'has_kademlia': KADEMLIA_AVAILABLE
        }

    async def stop(self):
        """Stop DHT"""
        print("[DHT] Stopping DHT...")
        self.running = False

        if self.server:
            self.server.stop()

        print("[DHT] ✓ DHT stopped")


# Fallback stub if kademlia not available
class DHTManagerStub:
    """Stub implementation when kademlia is not available"""

    def __init__(self, *args, **kwargs):
        print("[DHT] DHT Manager stub - install kademlia for full functionality")

    async def start(self, *args, **kwargs):
        print("[DHT] DHT disabled - install kademlia: pip install kademlia")
        return False

    async def announce(self, *args, **kwargs):
        pass

    async def discover_peers(self, *args, **kwargs):
        return []

    async def find_peer(self, *args, **kwargs):
        return None

    async def find_peers_by_capability(self, *args, **kwargs):
        return []

    def get_stats(self):
        return {'running': False, 'has_kademlia': False}

    async def stop(self):
        pass


# Export the right class based on availability
if not KADEMLIA_AVAILABLE:
    DHTManager = DHTManagerStub
