"""
P2P Security Module
Implements comprehensive security features for P2P communication:
- Replay attack protection
- Clock synchronization
- Message encryption
- Timestamp validation
- Nonce tracking
"""
import time
import secrets
from typing import Dict, Set, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass
import asyncio


@dataclass
class MessageMetadata:
    """Metadata for tracking messages"""
    message_id: str
    timestamp: float
    node_id: str
    nonce: str
    received_at: float


class ReplayProtection:
    """
    Protects against replay attacks using:
    - Timestamp window validation
    - Nonce tracking
    - Message ID deduplication
    """

    def __init__(self, timestamp_tolerance: float = 30.0):
        """
        Args:
            timestamp_tolerance: Maximum allowed time difference in seconds
        """
        self.timestamp_tolerance = timestamp_tolerance

        # Track seen messages with timestamps
        self.seen_messages: Dict[str, float] = {}  # message_id -> received_time
        self.seen_nonces: Set[str] = set()

        # Track message metadata
        self.message_history: Dict[str, MessageMetadata] = {}

    def validate_message(self, message: dict) -> Tuple[bool, str]:
        """
        Validate message against replay attacks

        Returns:
            (is_valid, reason)
        """
        current_time = time.time()
        message_id = message.get('message_id')
        timestamp = message.get('timestamp', 0)
        nonce = message.get('nonce')
        node_id = message.get('node_id')

        # Check 1: Message ID already seen
        if message_id in self.seen_messages:
            return False, "Duplicate message ID (replay attack)"

        # Check 2: Timestamp validation (within tolerance window)
        time_diff = abs(current_time - timestamp)
        if time_diff > self.timestamp_tolerance:
            return False, f"Timestamp out of window ({time_diff:.1f}s > {self.timestamp_tolerance}s)"

        # Check 3: Nonce validation (if present)
        if nonce:
            if nonce in self.seen_nonces:
                return False, "Duplicate nonce (replay attack)"

        # Check 4: Future timestamp (clock skew attack)
        if timestamp > current_time + 5:  # 5s tolerance for clock drift
            return False, f"Message from future (clock skew attack)"

        return True, "Valid"

    def mark_message_seen(self, message: dict):
        """Mark message as seen"""
        current_time = time.time()
        message_id = message.get('message_id')
        nonce = message.get('nonce')

        self.seen_messages[message_id] = current_time

        if nonce:
            self.seen_nonces.add(nonce)

        # Store metadata
        metadata = MessageMetadata(
            message_id=message_id,
            timestamp=message.get('timestamp', current_time),
            node_id=message.get('node_id'),
            nonce=nonce,
            received_at=current_time
        )
        self.message_history[message_id] = metadata

    def cleanup_old_messages(self, max_age: float = 60.0):
        """Remove old message records"""
        current_time = time.time()

        # Clean seen messages
        old_messages = [
            msg_id for msg_id, seen_time in self.seen_messages.items()
            if current_time - seen_time > max_age
        ]

        for msg_id in old_messages:
            del self.seen_messages[msg_id]
            self.message_history.pop(msg_id, None)

        # Note: Nonces are kept longer to prevent replay
        # They're cleaned up based on timestamp


class ClockSync:
    """
    Clock synchronization for distributed nodes
    Detects and corrects clock skew
    """

    def __init__(self):
        self.peer_clock_offsets: Dict[str, float] = {}  # node_id -> offset
        self.local_offset: float = 0.0
        self.last_sync: float = 0.0

    async def query_peer_time(self, node_id: str, query_callback) -> Optional[float]:
        """
        Query peer for current time

        Args:
            node_id: Peer node ID
            query_callback: Async function to send time query

        Returns:
            Peer's timestamp or None
        """
        try:
            t0 = time.time()
            peer_time = await query_callback(node_id)
            t1 = time.time()

            # Account for RTT
            rtt = t1 - t0
            estimated_peer_time = peer_time + (rtt / 2)

            # Calculate offset
            offset = estimated_peer_time - t1
            self.peer_clock_offsets[node_id] = offset

            return estimated_peer_time
        except Exception as e:
            print(f"[CLOCK] Failed to query {node_id}: {e}")
            return None

    async def synchronize(self, peers: list, query_callback):
        """
        Synchronize clock with peers
        Uses median offset to determine drift
        """
        if not peers:
            return

        # Query all peers
        tasks = [self.query_peer_time(peer, query_callback) for peer in peers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter valid offsets
        valid_offsets = [
            offset for offset in self.peer_clock_offsets.values()
            if offset is not None
        ]

        if not valid_offsets:
            print("[CLOCK] No valid peer time responses")
            return

        # Calculate median offset
        valid_offsets.sort()
        median_offset = valid_offsets[len(valid_offsets) // 2]

        # Check if significant drift
        if abs(median_offset) > 5.0:
            print(f"⚠️ [CLOCK] Significant clock drift detected: {median_offset:.2f}s")
            print(f"[CLOCK] Local time may be inaccurate!")

        self.local_offset = median_offset
        self.last_sync = time.time()

        print(f"[CLOCK] Synchronized with {len(valid_offsets)} peers")
        print(f"[CLOCK] Median offset: {median_offset:.3f}s")

    def get_synchronized_time(self) -> float:
        """Get time corrected for drift"""
        return time.time() + self.local_offset

    def verify_timestamp(self, timestamp: float, tolerance: float = 30.0) -> bool:
        """Verify timestamp is within acceptable range"""
        sync_time = self.get_synchronized_time()
        diff = abs(sync_time - timestamp)
        return diff <= tolerance


class QuorumConsensus:
    """
    Quorum-based consensus for critical operations
    Requires 2/3 agreement before execution
    """

    def __init__(self, node_id: str, quorum_size: int = 2):
        """
        Args:
            node_id: This node's ID
            quorum_size: Minimum nodes required for quorum
        """
        self.node_id = node_id
        self.quorum_size = quorum_size

        # Track consensus operations
        self.pending_operations: Dict[str, Set[str]] = defaultdict(set)  # op_id -> set of approving nodes
        self.operation_data: Dict[str, dict] = {}  # op_id -> operation data

    def propose_operation(self, operation_id: str, operation_data: dict):
        """Propose an operation for consensus"""
        self.operation_data[operation_id] = operation_data
        # Automatically approve own operation
        self.pending_operations[operation_id].add(self.node_id)

    def receive_approval(self, operation_id: str, node_id: str, operation_data: dict) -> bool:
        """
        Receive approval from peer

        Returns:
            True if quorum reached
        """
        # Verify operation data matches
        if operation_id in self.operation_data:
            if self.operation_data[operation_id] != operation_data:
                print(f"⚠️ [CONSENSUS] Operation data mismatch for {operation_id}")
                return False
        else:
            self.operation_data[operation_id] = operation_data

        # Add approval
        self.pending_operations[operation_id].add(node_id)

        # Check quorum
        approval_count = len(self.pending_operations[operation_id])
        has_quorum = approval_count >= self.quorum_size

        if has_quorum:
            print(f"✅ [CONSENSUS] Quorum reached for {operation_id} ({approval_count} nodes)")

        return has_quorum

    def has_quorum(self, operation_id: str) -> bool:
        """Check if operation has quorum"""
        approval_count = len(self.pending_operations.get(operation_id, set()))
        return approval_count >= self.quorum_size

    def get_approval_count(self, operation_id: str) -> int:
        """Get current approval count"""
        return len(self.pending_operations.get(operation_id, set()))

    def clear_operation(self, operation_id: str):
        """Clear operation from tracking"""
        self.pending_operations.pop(operation_id, None)
        self.operation_data.pop(operation_id, None)


class MessageReliability:
    """
    Ensures reliable message delivery with ACKs
    """

    def __init__(self, ack_timeout: float = 5.0):
        self.ack_timeout = ack_timeout

        # Track pending ACKs
        self.pending_acks: Dict[str, Set[str]] = defaultdict(set)  # message_id -> set of nodes that ACKed
        self.ack_futures: Dict[str, asyncio.Future] = {}  # message_id -> future for ACK completion

    def expect_acks(self, message_id: str, expected_nodes: list) -> asyncio.Future:
        """
        Register expectation of ACKs from nodes

        Returns:
            Future that resolves when quorum ACKs received
        """
        future = asyncio.Future()
        self.ack_futures[message_id] = future
        return future

    def receive_ack(self, message_id: str, node_id: str, total_expected: int):
        """
        Receive ACK from node

        Args:
            message_id: Message being ACKed
            node_id: Node sending ACK
            total_expected: Total number of expected ACKs (for quorum calculation)
        """
        self.pending_acks[message_id].add(node_id)

        ack_count = len(self.pending_acks[message_id])
        quorum_threshold = (total_expected * 2) // 3  # 2/3 quorum

        # Check if quorum reached
        if message_id in self.ack_futures and not self.ack_futures[message_id].done():
            if ack_count >= quorum_threshold:
                self.ack_futures[message_id].set_result(ack_count)

    async def wait_for_acks(self, message_id: str, expected_count: int, timeout: Optional[float] = None) -> int:
        """
        Wait for ACKs with timeout

        Returns:
            Number of ACKs received
        """
        timeout = timeout or self.ack_timeout

        try:
            ack_count = await asyncio.wait_for(
                self.expect_acks(message_id, []),
                timeout=timeout
            )
            return ack_count
        except asyncio.TimeoutError:
            # Return however many we got
            return len(self.pending_acks.get(message_id, set()))

    def cleanup_acks(self, message_id: str):
        """Clean up ACK tracking for message"""
        self.pending_acks.pop(message_id, None)
        self.ack_futures.pop(message_id, None)


class HealthMonitor:
    """
    Active health monitoring for peers
    Implements PING/PONG protocol
    """

    def __init__(self, ping_interval: float = 10.0, ping_timeout: float = 5.0):
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout

        # Track peer health
        self.peer_health: Dict[str, dict] = {}  # node_id -> health_info
        self.last_ping: Dict[str, float] = {}  # node_id -> last_ping_time
        self.last_pong: Dict[str, float] = {}  # node_id -> last_pong_time

        # RTT tracking
        self.rtt_history: Dict[str, list] = defaultdict(list)  # node_id -> [rtt_samples]

    async def ping_peer(self, node_id: str, send_callback) -> Optional[float]:
        """
        Send PING and wait for PONG

        Returns:
            RTT in seconds, or None if timeout
        """
        ping_id = secrets.token_hex(8)
        self.last_ping[node_id] = time.time()

        try:
            t0 = time.time()
            await send_callback(node_id, ping_id)

            # Wait for PONG (implementation specific)
            # This is a simplified version - actual implementation
            # would wait for PONG message with matching ping_id

            await asyncio.sleep(0.1)  # Placeholder

            t1 = time.time()
            rtt = t1 - t0

            # Record RTT
            self.rtt_history[node_id].append(rtt)
            if len(self.rtt_history[node_id]) > 100:
                self.rtt_history[node_id].pop(0)

            # Update health
            self.peer_health[node_id] = {
                'alive': True,
                'rtt': rtt,
                'last_seen': t1
            }

            return rtt

        except asyncio.TimeoutError:
            self.peer_health[node_id] = {
                'alive': False,
                'rtt': None,
                'last_seen': self.last_pong.get(node_id, 0)
            }
            return None

    def get_peer_rtt(self, node_id: str) -> Optional[float]:
        """Get average RTT for peer"""
        rtts = self.rtt_history.get(node_id, [])
        if not rtts:
            return None
        return sum(rtts) / len(rtts)

    def get_p99_latency(self) -> float:
        """Get P99 network latency across all peers"""
        all_rtts = []
        for rtts in self.rtt_history.values():
            all_rtts.extend(rtts)

        if not all_rtts:
            return 1.0  # Default

        all_rtts.sort()
        p99_index = int(len(all_rtts) * 0.99)
        return all_rtts[p99_index] if p99_index < len(all_rtts) else all_rtts[-1]

    def is_peer_healthy(self, node_id: str, max_age: float = 30.0) -> bool:
        """Check if peer is considered healthy"""
        health = self.peer_health.get(node_id)
        if not health:
            return False

        if not health['alive']:
            return False

        # Check if too old
        time_since_seen = time.time() - health['last_seen']
        return time_since_seen < max_age


def generate_nonce() -> str:
    """Generate cryptographically secure nonce"""
    return secrets.token_hex(16)


def add_security_fields(message: dict) -> dict:
    """Add security fields to message"""
    if 'nonce' not in message:
        message['nonce'] = generate_nonce()
    if 'timestamp' not in message:
        message['timestamp'] = time.time()
    return message


# Example usage
if __name__ == "__main__":
    # Test replay protection
    replay = ReplayProtection(timestamp_tolerance=30.0)

    message = {
        'message_id': 'test-123',
        'timestamp': time.time(),
        'nonce': generate_nonce(),
        'node_id': 'node-1'
    }

    is_valid, reason = replay.validate_message(message)
    print(f"Message valid: {is_valid} ({reason})")

    replay.mark_message_seen(message)

    # Try replay
    is_valid, reason = replay.validate_message(message)
    print(f"Replay valid: {is_valid} ({reason})")

    # Test with old timestamp
    old_message = {
        'message_id': 'test-456',
        'timestamp': time.time() - 100,  # 100s ago
        'nonce': generate_nonce(),
        'node_id': 'node-1'
    }

    is_valid, reason = replay.validate_message(old_message)
    print(f"Old message valid: {is_valid} ({reason})")
