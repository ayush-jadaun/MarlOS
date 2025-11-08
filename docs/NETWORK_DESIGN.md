# MarlOS Network Design
## Decentralized P2P Architecture

**Version:** 1.0.0
**Last Updated:** 2025-01-08

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Network Topology](#network-topology)
4. [Communication Protocol](#communication-protocol)
5. [Security Model](#security-model)
6. [Consensus Mechanisms](#consensus-mechanisms)
7. [Failure Recovery](#failure-recovery)
8. [Performance Optimizations](#performance-optimizations)
9. [Network Metrics](#network-metrics)

---

## Overview

MarlOS implements a **fully decentralized peer-to-peer network** where every node is equal. There is no master node, no central coordinator, and no single point of failure. The network uses **ZeroMQ** (ØMQ) for high-performance asynchronous messaging with a **publish-subscribe (PUB/SUB)** topology.

### Key Characteristics

- **Decentralized**: No master node or central authority
- **Self-organizing**: Automatic peer discovery and connection
- **Self-healing**: Automatic recovery from node failures
- **Byzantine-tolerant**: Resistant to malicious nodes
- **Scalable**: Designed for 3-100+ nodes
- **Low-latency**: Sub-second message propagation

---

## Architecture

### Component Hierarchy

```
MarlOSAgent
 └── P2PNode
      ├── Publisher Socket (PUB)
      ├── Subscriber Socket (SUB)
      ├── Message Queue
      ├── Peer Registry
      ├── Security Layer (Ed25519)
      └── Coordinator Election
```

### Network Layers

#### 1. Transport Layer (ZeroMQ)
- **Protocol**: TCP/IP
- **Sockets**: PUB/SUB pattern
- **Serialization**: JSON (orjson for performance)
- **Compression**: Optional gzip for large payloads

#### 2. Discovery Layer
- **Beacon Broadcasting**: UDP multicast for local discovery
- **Bootstrap Peers**: Manual peer list for cross-network
- **Gossip Protocol**: Peer information propagation

#### 3. Security Layer
- **Signatures**: Ed25519 digital signatures on all messages
- **Encryption**: NaCl asymmetric encryption (optional)
- **Replay Protection**: Nonce-based anti-replay
- **Clock Sync**: NTP-style clock synchronization

#### 4. Application Layer
- **Message Routing**: Type-based message handlers
- **State Synchronization**: Eventually-consistent state
- **Job Coordination**: Decentralized auction protocol

---

## Network Topology

### Mesh Network

MarlOS uses a **full mesh topology** where every node connects to every other node:

```
    Node A ←―――→ Node B
      ↑  ╲     ╱  ↑
      |    ╲ ╱    |
      |    ╱ ╲    |
      ↓  ╱     ╲  ↓
    Node C ←―――→ Node D
```

**Advantages**:
- No single point of failure
- Direct peer-to-peer communication
- Redundant paths for message delivery
- High fault tolerance

**Challenges**:
- O(n²) connections for n nodes
- Higher bandwidth usage
- More complex state synchronization

**Mitigations**:
- Connection limits (max 50 peers by default)
- Message deduplication
- Rate limiting per peer

---

## Communication Protocol

### Message Types

All messages follow a standard envelope format:

```json
{
  "msg_type": "MESSAGE_TYPE",
  "sender_id": "node-123",
  "timestamp": 1704672000.123,
  "nonce": "abc123xyz789",
  "signature": "ed25519_signature_here",
  "payload": { ... }
}
```

### Core Message Types

#### 1. Discovery Messages

**PEER_ANNOUNCE**
```json
{
  "msg_type": "PEER_ANNOUNCE",
  "payload": {
    "node_id": "agent-1",
    "node_name": "MarlOS Node 1",
    "pub_endpoint": "tcp://192.168.1.100:5555",
    "capabilities": ["shell", "docker", "malware_scan"],
    "trust_score": 0.85,
    "active_jobs": 2,
    "wallet_balance": 150.0
  }
}
```

**PING / PONG** (Heartbeat)
```json
{
  "msg_type": "PING",
  "payload": {
    "timestamp": 1704672000.123
  }
}
```

#### 2. Job Workflow Messages

**JOB_BROADCAST**
```json
{
  "msg_type": "JOB_BROADCAST",
  "payload": {
    "job_id": "job-abc123",
    "job_type": "shell",
    "command": "ls -la",
    "priority": 0.8,
    "deadline": 1704672060.0,
    "payment": 10.0,
    "requirements": [],
    "submitter": "client-node-5"
  }
}
```

**JOB_BID**
```json
{
  "msg_type": "JOB_BID",
  "payload": {
    "job_id": "job-abc123",
    "bidder_id": "agent-1",
    "score": 0.85,
    "stake": 10.0,
    "estimated_completion": 5.0,
    "trust_score": 0.92
  }
}
```

**JOB_CLAIM**
```json
{
  "msg_type": "JOB_CLAIM",
  "payload": {
    "job_id": "job-abc123",
    "claimer_id": "agent-1",
    "backup_id": "agent-2"
  }
}
```

**JOB_RESULT**
```json
{
  "msg_type": "JOB_RESULT",
  "payload": {
    "job_id": "job-abc123",
    "executor_id": "agent-1",
    "status": "success",
    "output": "...",
    "duration": 4.5,
    "payment_earned": 12.0
  }
}
```

#### 3. Consensus Messages

**AUCTION_COORDINATE**
```json
{
  "msg_type": "AUCTION_COORDINATE",
  "payload": {
    "job_id": "job-abc123",
    "coordinator_id": "agent-3",
    "all_bids": [...],
    "winner_id": "agent-1",
    "backup_id": "agent-2"
  }
}
```

#### 4. Economic Messages

**TOKEN_TRANSACTION**
```json
{
  "msg_type": "TOKEN_TRANSACTION",
  "payload": {
    "tx_id": "tx-xyz789",
    "from": "agent-1",
    "to": "agent-2",
    "amount": 10.0,
    "reason": "job_payment",
    "signature": "..."
  }
}
```

**REPUTATION_UPDATE**
```json
{
  "msg_type": "REPUTATION_UPDATE",
  "payload": {
    "node_id": "agent-1",
    "trust_score": 0.92,
    "total_jobs": 150,
    "success_rate": 0.96,
    "timestamp": 1704672000.0
  }
}
```

---

## Security Model

### Cryptographic Security

#### 1. Ed25519 Digital Signatures

Every message is signed with the sender's private key:

```python
# Message signing
message_hash = sha256(json.dumps(payload))
signature = ed25519_sign(message_hash, private_key)

# Verification
is_valid = ed25519_verify(signature, message_hash, public_key)
```

**Key Generation**:
- Keys generated on first startup
- Stored in `data/keys/{node_id}.key`
- Private key never leaves the node

#### 2. Replay Attack Protection

**Nonce-based Protection**:
```python
nonce = f"{node_id}:{timestamp}:{random_hex(16)}"
seen_nonces = LRU_cache(maxsize=10000)

if nonce in seen_nonces:
    reject_message("Replay attack detected")
```

**Timestamp Validation**:
```python
local_time = time.time()
msg_time = message['timestamp']

if abs(local_time - msg_time) > 30:  # 30-second tolerance
    reject_message("Timestamp out of bounds")
```

#### 3. Rate Limiting

**Per-Peer Rate Limiting**:
```python
rate_limiter = {
    'agent-1': {'count': 45, 'window_start': 1704672000},
    'agent-2': {'count': 12, 'window_start': 1704672000}
}

MAX_MSGS_PER_SEC = 100

if peer_rate > MAX_MSGS_PER_SEC:
    blacklist_peer(peer_id, duration=3600)  # 1 hour ban
```

#### 4. Message Size Limits

```python
MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10 MB

if len(message_bytes) > MAX_MESSAGE_SIZE:
    reject_message("Message too large")
```

---

## Consensus Mechanisms

### Decentralized Coordinator Election

MarlOS uses **deterministic coordinator election** to ensure all nodes agree on who coordinates each auction, without communication overhead.

#### Algorithm

```python
def elect_coordinator(job_id: str, known_peers: List[str]) -> str:
    """
    Deterministic election based on job_id hash.
    All nodes independently elect the same coordinator.
    """
    # Hash job_id to get deterministic random value
    hash_value = int(hashlib.sha256(job_id.encode()).hexdigest(), 16)

    # Sort peers for deterministic ordering
    sorted_peers = sorted(known_peers)

    # Select coordinator (same result on all nodes)
    coordinator_index = hash_value % len(sorted_peers)
    coordinator = sorted_peers[coordinator_index]

    return coordinator
```

**Properties**:
- **Deterministic**: All nodes elect the same coordinator
- **Fair**: Each node has equal probability over time
- **Byzantine-tolerant**: No single node can manipulate election
- **Zero communication**: No message exchange needed

### Quorum Consensus

For critical decisions (job claims, transaction validation), MarlOS requires **quorum consensus**:

```python
QUORUM_THRESHOLD = 0.66  # 66% agreement required

def validate_claim(job_id: str, claimer_id: str) -> bool:
    """Validate job claim via quorum consensus"""

    # Collect votes from all peers
    votes = collect_votes(job_id, timeout=5.0)

    # Count votes for this claimer
    votes_for = sum(1 for v in votes if v['winner'] == claimer_id)
    total_votes = len(votes)

    # Require 66% agreement
    return (votes_for / total_votes) >= QUORUM_THRESHOLD
```

---

## Failure Recovery

### Node Failure Detection

**Heartbeat Monitoring**:
```python
HEARTBEAT_INTERVAL = 3  # seconds
HEARTBEAT_TIMEOUT = 15  # seconds

# Each node broadcasts PING every 3 seconds
# If no PING received for 15 seconds, mark peer as dead
```

**Failure Detection**:
```python
def check_peer_health(peer_id: str) -> bool:
    last_seen = peer_registry[peer_id]['last_heartbeat']
    time_since = time.time() - last_seen

    if time_since > HEARTBEAT_TIMEOUT:
        mark_peer_dead(peer_id)
        trigger_recovery(peer_id)
        return False

    return True
```

### Job Recovery

**Primary-Backup Pattern**:

1. **During Auction**: Select both primary winner AND backup
2. **Backup Monitoring**: Backup monitors primary's heartbeats
3. **Automatic Takeover**: If primary fails, backup takes over job
4. **Result Propagation**: Backup broadcasts result as if primary

```python
class JobRecovery:
    def monitor_primary(self, job_id: str, primary_id: str):
        """Backup monitors primary's heartbeats"""

        timeout = JOB_TIMEOUT + 30  # Grace period
        last_heartbeat = time.time()

        while time.time() - last_heartbeat < timeout:
            if received_heartbeat(job_id, primary_id):
                last_heartbeat = time.time()

            await asyncio.sleep(1)

        # Primary failed - take over
        if not is_job_completed(job_id):
            self.takeover_job(job_id)
```

### Network Partition Recovery

**Split-Brain Prevention**:
```python
def handle_partition():
    """Handle network partition gracefully"""

    # Detect partition
    if len(known_peers) < MIN_PEERS:
        enter_degraded_mode()

    # Continue operating with known peers
    # When partition heals:
    #   1. Re-discover full peer set
    #   2. Sync state via gossip
    #   3. Resolve conflicts deterministically
```

**Conflict Resolution**:
- Use timestamps for causal ordering
- Prefer higher trust scores in ties
- Deterministic tie-breaking (hash-based)

---

## Performance Optimizations

### 1. Async I/O with uvloop

```python
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# ~2x performance improvement over default asyncio
```

### 2. Message Deduplication

```python
class MessageDeduplicator:
    def __init__(self):
        self.seen = LRUCache(maxsize=10000)

    def is_duplicate(self, msg_id: str) -> bool:
        if msg_id in self.seen:
            return True
        self.seen[msg_id] = True
        return False
```

### 3. Connection Pooling

```python
# Reuse ZMQ sockets instead of creating new ones
socket_pool = {
    'pub': zmq_context.socket(zmq.PUB),
    'sub': zmq_context.socket(zmq.SUB)
}

# Set high water marks for buffering
socket.setsockopt(zmq.SNDHWM, 1000)
socket.setsockopt(zmq.RCVHWM, 1000)
```

### 4. Fast JSON Parsing

```python
import orjson  # Rust-based JSON parser

# 3-5x faster than standard json module
payload = orjson.dumps(data)
data = orjson.loads(payload)
```

---

## Network Metrics

### Key Performance Indicators

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Message Latency** | < 50ms | Time from send to receive |
| **Peer Discovery Time** | < 5s | Time to discover all peers |
| **Heartbeat Frequency** | 3s | PING interval |
| **Failure Detection Time** | < 15s | Time to detect dead peer |
| **Job Broadcast Latency** | < 100ms | Time for all nodes to receive job |
| **Consensus Time** | < 2s | Time to reach quorum |
| **Network Overhead** | < 10 KB/job | Total bytes per job |
| **Max Throughput** | 100 jobs/s | System-wide throughput |

### Monitoring Dashboard

```python
class NetworkMonitor:
    def get_metrics(self):
        return {
            'peer_count': len(known_peers),
            'messages_sent': total_messages_sent,
            'messages_received': total_messages_received,
            'avg_latency_ms': calculate_avg_latency(),
            'bandwidth_usage_mbps': calculate_bandwidth(),
            'blacklisted_peers': len(blacklist),
            'partition_detected': is_partitioned()
        }
```

---

## Configuration

### Optimal Network Settings

```yaml
network:
  # Ports
  pub_port: 5555
  sub_port: 5556
  beacon_port: 5557

  # Discovery
  discovery_interval: 5       # seconds
  heartbeat_interval: 3       # seconds
  max_peers: 50               # connection limit

  # Security
  message_signature: true
  replay_protection: true
  clock_sync_tolerance: 30    # seconds
  rate_limit_msgs_per_sec: 100

  # Performance
  socket_high_water_mark: 1000
  message_queue_size: 10000
  use_uvloop: true
```

---

## Best Practices

### 1. Network Sizing

- **Small (3-5 nodes)**: Testing, development
- **Medium (5-20 nodes)**: Production, single datacenter
- **Large (20-50 nodes)**: Multi-datacenter, high availability
- **Very Large (50+ nodes)**: Consider hierarchical topology

### 2. Security

- ✅ Always enable message signatures
- ✅ Use replay protection in production
- ✅ Monitor rate limits and blacklist
- ✅ Rotate keys every 90 days
- ❌ Never disable authentication

### 3. Performance

- ✅ Use uvloop on Linux/Mac
- ✅ Enable orjson for JSON parsing
- ✅ Set appropriate HWM values
- ✅ Monitor network bandwidth
- ✅ Use message compression for large payloads

### 4. Reliability

- ✅ Always configure backup nodes
- ✅ Set heartbeat interval < timeout/5
- ✅ Monitor partition detection
- ✅ Test failure scenarios regularly

---

## Troubleshooting

### Common Issues

#### Peers Not Discovering

**Symptoms**: Nodes can't find each other

**Solutions**:
1. Check firewall rules (ports 5555-5557)
2. Verify broadcast_address setting
3. Manually specify bootstrap_peers
4. Check network connectivity (ping)

#### High Message Latency

**Symptoms**: Messages take >100ms to propagate

**Solutions**:
1. Reduce peer count (max_peers < 20)
2. Enable uvloop
3. Check network bandwidth
4. Reduce message size

#### Split-Brain Partitions

**Symptoms**: Network divides into isolated groups

**Solutions**:
1. Check network connectivity
2. Verify quorum thresholds
3. Use deterministic coordinator election
4. Monitor peer count

---

## Future Enhancements

### Planned Features

1. **DHT-based Discovery**: Kademlia DHT for scalable peer discovery
2. **Gossip Optimization**: Epidemic broadcast trees
3. **NAT Traversal**: STUN/TURN for cross-NAT communication
4. **IPv6 Support**: Full IPv6 compatibility
5. **Hierarchical Topology**: Hub-and-spoke for 100+ nodes
6. **Bandwidth Optimization**: Message batching and compression

---

## References

- ZeroMQ Guide: https://zguide.zeromq.org/
- Ed25519 Signatures: https://ed25519.cr.yp.to/
- Gossip Protocols: https://www.cs.cornell.edu/projects/Quicksilver/public_pdfs/2007PromiseAndLimitations.pdf
- Byzantine Fault Tolerance: https://pmg.csail.mit.edu/papers/osdi99.pdf

---

**Document Version:** 1.0.0
**Last Updated:** 2025-01-08
**Maintained By:** Team async_await
