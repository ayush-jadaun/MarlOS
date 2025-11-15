"""
Peer Manager for Private Mode
Handles saving, loading, and managing known peers for personal networks
"""
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class SavedPeer:
    """A saved peer configuration"""
    name: str
    address: str  # tcp://ip:port or tcp://domain:port
    public_key: str = ""
    notes: str = ""
    last_seen: float = 0.0
    auto_connect: bool = True
    added_at: float = 0.0

    def __post_init__(self):
        if self.added_at == 0.0:
            self.added_at = time.time()


class PeerManager:
    """
    Manages known peers for private mode

    Features:
    - Save/load peer list
    - Auto-connect to saved peers
    - Track last seen times
    - Support for dynamic DNS
    """

    def __init__(self, peers_file: str = "~/.marlos/peers.json"):
        self.peers_file = Path(peers_file).expanduser()
        self.peers: Dict[str, SavedPeer] = {}  # address -> SavedPeer
        self.load_peers()

    def load_peers(self):
        """Load peers from file"""
        if not self.peers_file.exists():
            self.peers_file.parent.mkdir(parents=True, exist_ok=True)
            self.save_peers()
            print("[PEER_MANAGER] Created new peers file")
            return

        try:
            with open(self.peers_file, 'r') as f:
                data = json.load(f)
                for peer_data in data.get('peers', []):
                    peer = SavedPeer(**peer_data)
                    self.peers[peer.address] = peer

            print(f"[PEER_MANAGER] Loaded {len(self.peers)} saved peers")

        except json.JSONDecodeError as e:
            print(f"[PEER_MANAGER] Error parsing peers file: {e}")
            print("[PEER_MANAGER] Creating backup and starting fresh")

            # Backup corrupted file
            backup_path = self.peers_file.with_suffix('.json.bak')
            self.peers_file.rename(backup_path)
            self.save_peers()

        except Exception as e:
            print(f"[PEER_MANAGER] Error loading peers: {e}")

    def save_peers(self):
        """Save peers to file"""
        try:
            data = {
                'version': '1.0',
                'updated_at': time.time(),
                'peers': [asdict(p) for p in self.peers.values()]
            }

            # Write atomically (write to temp, then rename)
            temp_file = self.peers_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)

            temp_file.replace(self.peers_file)

        except Exception as e:
            print(f"[PEER_MANAGER] Error saving peers: {e}")

    def add_peer(self, name: str, address: str, public_key: str = "",
                 notes: str = "", auto_connect: bool = True) -> bool:
        """
        Add a new peer

        Returns:
            bool: True if added successfully, False if already exists
        """
        # Normalize address
        if not address.startswith('tcp://'):
            address = f'tcp://{address}'

        if address in self.peers:
            print(f"[PEER_MANAGER] Peer already exists: {address}")
            return False

        peer = SavedPeer(
            name=name,
            address=address,
            public_key=public_key,
            notes=notes,
            auto_connect=auto_connect
        )

        self.peers[address] = peer
        self.save_peers()

        print(f"[PEER_MANAGER] Added peer: {name} ({address})")
        return True

    def remove_peer(self, address: str) -> bool:
        """
        Remove a peer

        Returns:
            bool: True if removed, False if not found
        """
        # Normalize address
        if not address.startswith('tcp://'):
            address = f'tcp://{address}'

        if address in self.peers:
            name = self.peers[address].name
            del self.peers[address]
            self.save_peers()
            print(f"[PEER_MANAGER] Removed peer: {name}")
            return True

        print(f"[PEER_MANAGER] Peer not found: {address}")
        return False

    def update_peer(self, address: str, **kwargs) -> bool:
        """
        Update peer properties

        Args:
            address: Peer address
            **kwargs: Properties to update (name, notes, auto_connect, etc.)
        """
        # Normalize address
        if not address.startswith('tcp://'):
            address = f'tcp://{address}'

        if address not in self.peers:
            print(f"[PEER_MANAGER] Peer not found: {address}")
            return False

        peer = self.peers[address]

        for key, value in kwargs.items():
            if hasattr(peer, key):
                setattr(peer, key, value)

        self.save_peers()
        print(f"[PEER_MANAGER] Updated peer: {peer.name}")
        return True

    def mark_seen(self, address: str):
        """Update last_seen timestamp for a peer"""
        if not address.startswith('tcp://'):
            address = f'tcp://{address}'

        if address in self.peers:
            self.peers[address].last_seen = time.time()
            self.save_peers()

    def get_peer(self, address: str) -> Optional[SavedPeer]:
        """Get a peer by address"""
        if not address.startswith('tcp://'):
            address = f'tcp://{address}'
        return self.peers.get(address)

    def get_auto_connect_peers(self) -> List[str]:
        """Get list of peer addresses to auto-connect to"""
        return [
            peer.address
            for peer in self.peers.values()
            if peer.auto_connect
        ]

    def get_all_peers(self) -> List[SavedPeer]:
        """Get all saved peers"""
        return list(self.peers.values())

    def list_peers(self):
        """Print all saved peers with details"""
        if not self.peers:
            print("\n[PEER_MANAGER] No saved peers\n")
            return

        print(f"\n[PEER_MANAGER] Saved Peers ({len(self.peers)}):")
        print("=" * 70)

        for i, peer in enumerate(self.peers.values(), 1):
            # Auto-connect indicator
            status = "✓ Auto" if peer.auto_connect else "○ Manual"

            # Last seen
            if peer.last_seen > 0:
                time_ago = time.time() - peer.last_seen
                if time_ago < 60:
                    last_seen = "Just now"
                elif time_ago < 3600:
                    last_seen = f"{int(time_ago / 60)}m ago"
                elif time_ago < 86400:
                    last_seen = f"{int(time_ago / 3600)}h ago"
                else:
                    last_seen = f"{int(time_ago / 86400)}d ago"
            else:
                last_seen = "Never"

            print(f"\n  {status} {i}. {peer.name}")
            print(f"      Address: {peer.address}")
            print(f"      Last seen: {last_seen}")

            if peer.notes:
                print(f"      Notes: {peer.notes}")

            if peer.public_key:
                print(f"      Public key: {peer.public_key[:16]}...")

        print("\n" + "=" * 70 + "\n")

    def export_peers(self, output_file: str):
        """Export peers to a file (for sharing/backup)"""
        output_path = Path(output_file).expanduser()

        data = {
            'exported_at': time.time(),
            'peers': [asdict(p) for p in self.peers.values()]
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"[PEER_MANAGER] Exported {len(self.peers)} peers to {output_path}")

    def import_peers(self, input_file: str, merge: bool = True):
        """
        Import peers from a file

        Args:
            input_file: File to import from
            merge: If True, merge with existing peers. If False, replace all.
        """
        input_path = Path(input_file).expanduser()

        if not input_path.exists():
            print(f"[PEER_MANAGER] File not found: {input_path}")
            return

        try:
            with open(input_path, 'r') as f:
                data = json.load(f)

            imported_peers = data.get('peers', [])

            if not merge:
                self.peers.clear()

            count = 0
            for peer_data in imported_peers:
                peer = SavedPeer(**peer_data)
                if peer.address not in self.peers or not merge:
                    self.peers[peer.address] = peer
                    count += 1

            self.save_peers()
            print(f"[PEER_MANAGER] Imported {count} peers from {input_path}")

        except Exception as e:
            print(f"[PEER_MANAGER] Error importing peers: {e}")

    def search_peers(self, query: str) -> List[SavedPeer]:
        """Search peers by name, address, or notes"""
        query_lower = query.lower()

        return [
            peer for peer in self.peers.values()
            if query_lower in peer.name.lower()
            or query_lower in peer.address.lower()
            or query_lower in peer.notes.lower()
        ]
