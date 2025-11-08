"""
P2P Node with ZMQ Gossip Protocol
Handles peer discovery, message broadcasting, and network communication
"""
import zmq
import zmq.asyncio
import asyncio
import sys
import asyncio

if sys.platform == 'win32':
    import winloop
    asyncio.set_event_loop_policy(winloop.EventLoopPolicy())
else:
    # Use uvloop on Linux/macOS for production
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except ImportError:
        pass
import json
import socket
import time
from typing import Dict, Set, Callable, Any, Deque
from collections import defaultdict, deque

from ..config import NetworkConfig
from ..crypto.signing import SigningKey, sign_message, verify_message
from ..crypto.encryption import AsymmetricEncryption, encrypt_message_field, decrypt_message_field
from .protocol import MessageType, BaseMessage, create_message
from .security import (
    ReplayProtection, ClockSync, QuorumConsensus,
    MessageReliability, HealthMonitor, generate_nonce, add_security_fields
)


class RateLimiter:
    """
    Token bucket rate limiter for message flood protection
    """

    def __init__(self, max_tokens: int = 10, refill_rate: float = 1.0):
        """
        Args:
            max_tokens: Maximum tokens (messages) allowed
            refill_rate: Tokens refilled per second
        """
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.tokens = max_tokens
        self.last_refill = time.time()

    def refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate

        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens
        Returns True if allowed, False if rate limit exceeded
        """
        self.refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def get_remaining(self) -> float:
        """Get remaining tokens"""
        self.refill()
        return self.tokens


class P2PNode:
    """
    Peer-to-peer node using ZMQ for gossip protocol with rate limiting
    """

    def __init__(self, node_id: str, signing_key: SigningKey, config: NetworkConfig):
        self.node_id = node_id
        self.signing_key = signing_key
        self.config = config

        # ZMQ Context
        self.context = zmq.asyncio.Context()

        # Sockets
        self.pub_socket = None  # Publisher
        self.sub_socket = None  # Subscriber

        # Peers
        self.peers: Dict[str, Dict[str, Any]] = {}  # node_id -> peer_info
        self.peer_addresses: Set[str] = set()

        # Message handlers
        self.message_handlers: Dict[str, list] = defaultdict(list)

        # State
        self.running = False
        self.local_ip = self._get_local_ip()

        # Message deduplication (FIXED: Track with timestamps)
        self.seen_messages: Dict[str, float] = {}  # message_id -> received_time
        self.message_ttl = 60  # seconds

        # Rate limiting
        self.rate_limiters: Dict[str, RateLimiter] = {}  # node_id -> RateLimiter
        self.blacklisted_nodes: Set[str] = set()
        self.blacklist_violations: Dict[str, int] = defaultdict(int)  # node_id -> violation_count
        self.max_violations = 3  # Blacklist after 3 violations

        # Message statistics
        self.message_stats: Dict[str, int] = defaultdict(int)  # message_type -> count
        self.peer_message_count: Dict[str, int] = defaultdict(int)  # node_id -> msg_count

        # SECURITY FEATURES
        self.replay_protection = ReplayProtection(timestamp_tolerance=30.0)
        self.clock_sync = ClockSync()
        self.consensus = QuorumConsensus(node_id, quorum_size=2)
        self.reliability = MessageReliability(ack_timeout=2.0)  # Reduced from 5.0s for faster auction
        self.health_monitor = HealthMonitor(ping_interval=10.0, ping_timeout=5.0)

        # Encryption (optional - for sensitive payloads)
        self.encryption: Optional[AsymmetricEncryption] = None

        # Peer synchronization
        self.peers_ready = asyncio.Event()
        self.min_peers_required = 0  # Set by start() if needed
    
    def _get_local_ip(self) -> str:
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    async def start(self):
        """Start the P2P node"""
        print(f"[P2P] Starting node {self.node_id}")

        # Publisher socket (broadcasts to all)
        self.pub_socket = self.context.socket(zmq.PUB)

        # CRITICAL: Set ZMQ socket options for low-latency Docker networking
        self.pub_socket.setsockopt(zmq.SNDHWM, 1000)  # Send high water mark
        self.pub_socket.setsockopt(zmq.LINGER, 0)     # Don't wait on close
        self.pub_socket.setsockopt(zmq.TCP_KEEPALIVE, 1)  # Keep connections alive
        self.pub_socket.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 60)
        self.pub_socket.setsockopt(zmq.IMMEDIATE, 1)  # Don't queue for slow subscribers

        pub_address = f"{self.config.broadcast_address}:{self.config.pub_port}"
        self.pub_socket.bind(pub_address)
        print(f"[P2P] Publisher bound to {pub_address}")

        # Subscriber socket (receives from all)
        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all

        # CRITICAL: Set ZMQ socket options for low-latency Docker networking
        self.sub_socket.setsockopt(zmq.RCVHWM, 1000)  # Receive high water mark
        self.sub_socket.setsockopt(zmq.LINGER, 0)     # Don't wait on close
        self.sub_socket.setsockopt(zmq.TCP_KEEPALIVE, 1)  # Keep connections alive
        self.sub_socket.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 60)
        # NOTE: CONFLATE mode removed - it was dropping messages in auction system
        # Every bid/claim must be delivered, not just the latest one

        # CRITICAL: Subscribe to own publisher for job_broadcast loopback
        # This enables fair auction participation for submitting agent
        self_address = f"tcp://localhost:{self.config.pub_port}"
        self.sub_socket.connect(self_address)
        print(f"[P2P] Subscribed to self: {self_address}")

        # Connect to bootstrap peers if specified
        import os
        bootstrap_peers = os.getenv('BOOTSTRAP_PEERS', '')
        if bootstrap_peers:
            for peer_addr in bootstrap_peers.split(','):
                peer_addr = peer_addr.strip()
                if peer_addr:
                    self.connect_to_peer(peer_addr)
                    print(f"[P2P] Connected to bootstrap peer: {peer_addr}")

        # Allow time for socket binding and subscription establishment
        # CRITICAL: ZMQ needs time in Docker for slow joiner prevention
        print(f"[P2P] Waiting for ZMQ connections to stabilize...")
        await asyncio.sleep(5.0)  # Increased to combat slow joiner syndrome
        print(f"[P2P] ZMQ connections ready")

        self.running = True

        # Start background tasks
        asyncio.create_task(self._discovery_loop())
        asyncio.create_task(self._message_receiver())
        asyncio.create_task(self._heartbeat_loop())
        asyncio.create_task(self._cleanup_loop())
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._clock_sync_loop())

        print(f"[P2P] Node started: {self.node_id}")
    
    async def stop(self):
        """Stop the P2P node"""
        print(f"[P2P] Stopping node {self.node_id}")
        self.running = False

        # Send goodbye (node_id is added automatically by broadcast_message)
        await self.broadcast_message(
            MessageType.PEER_GOODBYE
        )
        
        # Close sockets
        if self.pub_socket:
            self.pub_socket.close()
        if self.sub_socket:
            self.sub_socket.close()
        
        self.context.term()

    async def wait_for_peers(self, min_peers: int = 2, timeout: float = 30.0):
        """
        Wait for minimum number of peers before accepting jobs
        CRITICAL: Prevents split-brain scenarios

        Args:
            min_peers: Minimum peers required
            timeout: Maximum time to wait

        Raises:
            TimeoutError: If timeout reached before minimum peers discovered
        """
        print(f"[P2P] Waiting for {min_peers} peers (timeout: {timeout}s)...")
        start = time.time()

        while len(self.peers) < min_peers:
            if time.time() - start > timeout:
                raise TimeoutError(
                    f"Failed to discover {min_peers} peers within {timeout}s. "
                    f"Only {len(self.peers)} peers found: {list(self.peers.keys())}"
                )

            await asyncio.sleep(0.5)

        print(f"✅ [P2P] Minimum peers connected: {len(self.peers)} peers")
        print(f"[P2P] Peers: {list(self.peers.keys())}")

        # Perform initial clock synchronization
        await self.synchronize_clock()

        self.peers_ready.set()

    async def synchronize_clock(self):
        """Synchronize clock with peers"""
        if not self.peers:
            return

        async def query_callback(node_id):
            # In real implementation, send TIME_QUERY message
            # For now, use last_seen as proxy
            peer_info = self.peers.get(node_id, {})
            return peer_info.get('last_seen', time.time())

        await self.clock_sync.synchronize(list(self.peers.keys()), query_callback)

    def connect_to_peer(self, peer_address: str):
        """Connect to a peer's publisher"""
        if peer_address not in self.peer_addresses:
            self.sub_socket.connect(peer_address)
            self.peer_addresses.add(peer_address)
            print(f"[P2P] Connected to peer: {peer_address}")
    
    async def broadcast_message(self, message_type: MessageType, **kwargs):
        """Broadcast a message to all peers with security features"""
        # Create message
        message = create_message(
            message_type,
            node_id=self.node_id,
            timestamp=time.time(),
            **kwargs
        )

        # Convert to dict and add security fields
        message_dict = message.to_dict()
        message_dict = add_security_fields(message_dict)

        # Encrypt sensitive fields if encryption enabled
        if self.encryption and message_type == MessageType.JOB_BROADCAST:
            # Note: For broadcast, we don't encrypt (no specific recipient)
            # But we could encrypt payload for privacy
            pass

        # Sign message
        signed_message = sign_message(self.signing_key, message_dict)

        # Serialize and broadcast
        message_json = json.dumps(signed_message)
        await self.pub_socket.send_string(message_json)

        # Debug logging for job broadcasts
        if message_type == MessageType.JOB_BROADCAST:
            print(f"[P2P DEBUG] Broadcasted {message_type} from {self.node_id}: {kwargs.get('job_id')}")
            # DON'T mark job_broadcasts as seen here - let receiver handle it
            # This allows the agent to receive and process its own job_broadcast
        else:
            # Mark other message types as seen to prevent re-processing
            self.seen_messages[signed_message['message_id']] = time.time()

    async def broadcast_reliable(self, message_type: MessageType, **kwargs):
        """
        Broadcast with delivery confirmation (ACKs)
        Used for critical messages (claims, results)
        """
        message_id = kwargs.get('message_id', str(time.time()))

        # Broadcast message
        await self.broadcast_message(message_type, message_id=message_id, **kwargs)

        # Give time for message to propagate and be processed
        await asyncio.sleep(0.1)  # Reduced from 500ms to 100ms for faster auction

        # Wait for ACKs
        expected_count = len(self.peers)
        if expected_count > 0:
            ack_count = await self.reliability.wait_for_acks(message_id, expected_count, timeout=2.0)
            print(f"[P2P] Reliable broadcast: {ack_count}/{expected_count} ACKs for {message_type}")
            return ack_count >= (expected_count * 2 // 3)  # 2/3 quorum

        return True
    
    async def _message_receiver(self):
        """Receive and process messages with security validation"""
        while self.running:
            try:
                # This await should yield control and allow other coroutines to run
                message_json = await self.sub_socket.recv_string()
                message = json.loads(message_json)

                # Debug: Log all received messages with timestamp
                msg_type = message.get('type')
                receive_time = time.time()
                if msg_type == 'job_broadcast':
                    print(f"[P2P DEBUG] {self.node_id} received {msg_type} from {message.get('node_id')}")
                elif msg_type == 'job_bid':
                    bid_sent_time = message.get('timestamp', 0)
                    zmq_latency = (receive_time - bid_sent_time) * 1000
                    print(f"[P2P DEBUG] {self.node_id} ZMQ received job_bid from {message.get('node_id')} (ZMQ latency: {zmq_latency:.1f}ms)")

                # SECURITY CHECK 1: Verify signature BEFORE processing
                # CRITICAL: Must verify before marking as seen
                if not verify_message(message):
                    print(f"[P2P] Invalid signature from {message.get('node_id')}")
                    continue

                # SECURITY CHECK 2: Replay attack protection
                is_valid, reason = self.replay_protection.validate_message(message)
                if not is_valid:
                    if msg_type == 'job_broadcast':
                        print(f"[P2P SECURITY] Rejected {msg_type}: {reason}")
                    continue

                # SECURITY CHECK 3: Check message deduplication
                message_id = message.get('message_id')
                if message_id in self.seen_messages:
                    if msg_type == 'job_broadcast':
                        print(f"[P2P DEBUG] Skipping duplicate message {message_id}")
                    continue

                # Mark as seen AFTER validation
                self.seen_messages[message_id] = time.time()
                self.replay_protection.mark_message_seen(message)

                # CRITICAL: Allow job_broadcasts from self to enable fair auction participation
                # But ignore other message types from self to prevent feedback loops
                if message.get('node_id') == self.node_id:
                    if msg_type == 'job_broadcast':
                        job_id = message.get('job_id', 'unknown')
                        print(f"[P2P DEBUG] Processing own job_broadcast {job_id} for fair auction")
                        # Continue processing - don't skip
                    else:
                        # Ignore other message types from self (bids, claims, etc.)
                        continue

                # Handle message
                await self._handle_message(message)

            except Exception as e:
                print(f"[P2P] Error receiving message: {e}")
                await asyncio.sleep(0.1)
    
    def _check_rate_limit(self, node_id: str) -> bool:
        """
        Check if message from node_id is within rate limits
        Returns True if allowed, False if rate limited
        """
        # Check if blacklisted
        if node_id in self.blacklisted_nodes:
            return False

        # Create rate limiter for new peer
        if node_id not in self.rate_limiters:
            self.rate_limiters[node_id] = RateLimiter(
                max_tokens=10,  # Allow burst of 10 messages
                refill_rate=2.0  # Refill 2 tokens/second (120 msg/min)
            )

        # Check rate limit
        limiter = self.rate_limiters[node_id]
        allowed = limiter.consume()

        if not allowed:
            # Rate limit exceeded
            self.blacklist_violations[node_id] += 1
            print(f"⚠️  [P2P] Rate limit exceeded for {node_id} "
                  f"(violation {self.blacklist_violations[node_id]}/{self.max_violations})")

            # Blacklist if too many violations
            if self.blacklist_violations[node_id] >= self.max_violations:
                self._blacklist_node(node_id)

        return allowed

    def _blacklist_node(self, node_id: str):
        """Blacklist a node for rate limit violations"""
        self.blacklisted_nodes.add(node_id)
        print(f"🚫 [P2P] BLACKLISTED node {node_id} for excessive messaging")

        # Remove from peers
        self.peers.pop(node_id, None)
        self.rate_limiters.pop(node_id, None)

    def unblacklist_node(self, node_id: str):
        """Manually remove node from blacklist"""
        if node_id in self.blacklisted_nodes:
            self.blacklisted_nodes.remove(node_id)
            self.blacklist_violations.pop(node_id, None)
            print(f"✅ [P2P] Unblacklisted node {node_id}")

    async def _handle_message(self, message: dict):
        """Handle incoming message with rate limiting"""
        message_type = message.get('type')
        node_id = message.get('node_id')

        # Rate limiting check
        if node_id and node_id != self.node_id:
            if not self._check_rate_limit(node_id):
                # Rate limited - drop message
                return

        # Update message statistics
        self.message_stats[message_type] += 1
        if node_id:
            self.peer_message_count[node_id] += 1

        # Update peer info
        if node_id and node_id != self.node_id:
            if node_id not in self.peers:
                self.peers[node_id] = {}
            self.peers[node_id]['last_seen'] = time.time()
            self.peers[node_id]['public_key'] = message.get('public_key')

        # Handle ACK messages
        if message_type == MessageType.ACK:
            ack_message_id = message.get('ack_message_id')
            if ack_message_id:
                print(f"[P2P ACK] Received ACK from {node_id} for message {ack_message_id}")
                self.reliability.receive_ack(ack_message_id, node_id, len(self.peers))
            return

        # Send ACK for critical message types that need reliable delivery
        critical_types = [MessageType.JOB_CLAIM, MessageType.JOB_RESULT]
        if message_type in critical_types and node_id and node_id != self.node_id:
            message_id = message.get('message_id')
            if message_id:
                # Send ACK back to sender
                print(f"[P2P ACK] Sending ACK for {message_type} message {message_id} from {node_id}")
                await self.broadcast_message(
                    MessageType.ACK,
                    ack_message_id=message_id
                )

        # Call registered handlers
        if message_type in self.message_handlers:
            for handler in self.message_handlers[message_type]:
                try:
                    await handler(message)
                except Exception as e:
                    print(f"[P2P] Handler error for {message_type}: {e}")
                    import traceback
                    traceback.print_exc()
    
    def on_message(self, message_type: MessageType):
        """Decorator to register message handler"""
        def decorator(func: Callable):
            self.message_handlers[message_type].append(func)
            return func
        return decorator
    
    async def _discovery_loop(self):
        """Periodically announce presence"""
        while self.running:
            await self.broadcast_message(
                MessageType.PEER_ANNOUNCE,
                node_name=f"agent-{self.node_id}",
                ip=self.local_ip,
                port=self.config.pub_port
            )
            await asyncio.sleep(self.config.discovery_interval)
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        while self.running:
            await asyncio.sleep(30)
            # Optional: send ping to check connectivity
    
    async def _cleanup_loop(self):
        """Clean up old seen messages and dead peers"""
        while self.running:
            await asyncio.sleep(60)

            # Clean seen messages (FIXED: Actually remove old ones)
            current_time = time.time()
            old_messages = [
                msg_id for msg_id, seen_time in self.seen_messages.items()
                if current_time - seen_time > self.message_ttl
            ]
            for msg_id in old_messages:
                del self.seen_messages[msg_id]

            if old_messages:
                print(f"[P2P] Cleaned up {len(old_messages)} old messages")

            # Clean replay protection
            self.replay_protection.cleanup_old_messages(max_age=self.message_ttl)

            # Remove dead peers (not seen in 30 seconds)
            dead_peers = [
                node_id for node_id, info in self.peers.items()
                if current_time - info.get('last_seen', 0) > 30
            ]
            for node_id in dead_peers:
                print(f"[P2P] Peer timeout: {node_id}")
                del self.peers[node_id]

    async def _health_check_loop(self):
        """Active health monitoring with PING/PONG"""
        while self.running:
            await asyncio.sleep(self.health_monitor.ping_interval)

            # Ping all peers
            for node_id in list(self.peers.keys()):
                async def ping_callback(nid, ping_id):
                    await self.broadcast_message(MessageType.PING, ping_id=ping_id)

                try:
                    rtt = await self.health_monitor.ping_peer(node_id, ping_callback)
                    if rtt:
                        print(f"[HEALTH] {node_id}: RTT={rtt*1000:.1f}ms")
                except Exception as e:
                    print(f"[HEALTH] Failed to ping {node_id}: {e}")

    async def _clock_sync_loop(self):
        """Periodic clock synchronization"""
        while self.running:
            await asyncio.sleep(300)  # Sync every 5 minutes

            if self.peers:
                await self.synchronize_clock()
    
    def get_peer_count(self) -> int:
        """Get number of connected peers"""
        return len(self.peers)
    
    def get_peers(self) -> Dict[str, Dict]:
        """Get all peers"""
        return self.peers.copy()
