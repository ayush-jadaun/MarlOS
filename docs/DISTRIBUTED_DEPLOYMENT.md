# MarlOS Distributed Deployment Guide

## From Docker Containers to Real Devices

This guide explains how to deploy MarlOS across actual physical devices (laptops, desktops, servers, Raspberry Pis) instead of Docker containers, creating a true distributed compute operating system.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Summary](#architecture-summary)
3. [Prerequisites](#prerequisites)
4. [Quick Start](#quick-start)
5. [Network Configuration](#network-configuration)
6. [Deployment Scenarios](#deployment-scenarios)
7. [Firewall & Security](#firewall--security)
8. [Testing & Verification](#testing--verification)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Topics](#advanced-topics)

---

## Overview

### Good News: MarlOS is Already Ready for Real Devices!

Your current Docker setup is essentially **simulating** what real distributed nodes would do. The architecture is fully decentralized with no Docker-specific dependencies. You only need to:

1. Install Python + dependencies on each device
2. Configure network addresses (replace Docker service names with real IPs)
3. Run the agent with proper environment variables

That's it! The P2P network, ZeroMQ communication, and all other systems work identically on real hardware.

---

## Architecture Summary

### Current Docker Setup

**Docker Compose Configuration** (`docker-compose.yml`):
- 3 agent containers (agent-1, agent-2, agent-3)
- 1 Mosquitto MQTT broker
- Custom bridge network (`marlos-net`)
- Internal DNS resolution (e.g., `marlos-agent-2:5555`)

**Key Components:**
- **ZeroMQ PUB/SUB**: Primary P2P communication layer
- **Publisher Socket**: Binds to `tcp://*:5555` (broadcasts to all peers)
- **Subscriber Socket**: Connects to all peer publishers
- **Bootstrap Discovery**: `BOOTSTRAP_PEERS` environment variable provides initial peer addresses
- **Gossip Protocol**: Periodic `PEER_ANNOUNCE` messages for auto-discovery

### How Nodes Communicate

#### 1. ZeroMQ Protocol (`agent/p2p/node.py`)

**Publisher Socket:**
- Binds to `tcp://*:5555` (configurable via `PUB_PORT`)
- Broadcasts messages to all subscribers
- Optimized socket options:
  - `TCP_KEEPALIVE`: Maintains long-lived connections
  - `SNDHWM`: 1000 message buffer
  - `IMMEDIATE`: No queuing for slow subscribers

**Subscriber Socket:**
- Connects to all peer publishers via `BOOTSTRAP_PEERS`
- Subscribes to all message types
- Connects to own publisher for loopback (enables fair auction participation)

**Message Flow:**
```
Node A → Broadcast via PUB socket → All subscribers receive → Validate signature → Process
```

#### 2. Network Discovery

**Bootstrap Peer Discovery** (Primary Method):
- Environment variable `BOOTSTRAP_PEERS` provides initial peer addresses
- Example: `tcp://marlos-agent-2:5555,tcp://marlos-agent-3:5555`
- On startup, nodes connect subscriber socket to bootstrap peers
- Docker's internal DNS resolves container names to IPs

**For Real Devices, simply replace with actual IPs:**
```bash
# Docker (internal DNS):
BOOTSTRAP_PEERS=tcp://marlos-agent-2:5555,tcp://marlos-agent-3:5555

# Real devices (IP addresses):
BOOTSTRAP_PEERS=tcp://192.168.1.101:5555,tcp://192.168.1.102:5555
```

**Gossip Protocol:**
- Periodic `PEER_ANNOUNCE` broadcasts every 5 seconds
- Contains: node_id, IP, port, capabilities, trust_score
- Peers automatically connect upon receiving announcement
- Self-organizing: no central registry needed

#### 3. Security Features

**Cryptographic Authentication:**
- Ed25519 signature on every message
- Public key verification before processing
- Timestamp validation (30s tolerance)
- Nonce tracking to prevent replay attacks

**Rate Limiting:**
- Token bucket algorithm per peer
- Max 10 messages burst, refill 2 tokens/second
- Blacklisting after 3 violations

#### 4. Job Execution Flow

1. Node broadcasts `JOB_BROADCAST` via ZMQ PUB
2. All peers receive, decide whether to bid (RL policy)
3. Bidders broadcast `JOB_BID` with score
4. Elected coordinator collects bids, determines winner
5. Winner broadcasts `JOB_CLAIM` with backup node
6. Winner executes job, broadcasts `JOB_RESULT`
7. Token economy handles payments, trust scores update

**Fault Tolerance:**
- Backup nodes assigned during claim
- Heartbeat monitoring during execution
- Automatic job takeover on failure
- Checkpoint/recovery mechanism for long jobs

---

## Prerequisites

### Hardware Requirements (Per Device)

**Minimum:**
- 2 CPU cores
- 2 GB RAM
- 10 GB disk space
- Network interface (WiFi/Ethernet)

**Recommended:**
- 4+ CPU cores
- 8+ GB RAM
- 50+ GB disk space (for job data/checkpoints)
- Gigabit Ethernet for low latency

### Software Requirements

**All Devices:**
- Python 3.11+ (`python --version`)
- pip package manager
- Git (for cloning repository)
- Network connectivity between devices

**Optional:**
- Docker (if you want job isolation)
- MQTT broker (for hardware device control)

### Operating System Support

- Linux (Ubuntu 20.04+, Debian 11+, Arch, etc.)
- macOS (12+)
- Windows (10/11 with WSL2 recommended)
- Raspberry Pi OS (64-bit)

---

## Quick Start

### Step 1: Install on Each Device

```bash
# Clone repository
git clone https://github.com/yourusername/MarlOS.git
cd MarlOS

# Install dependencies
pip install -r requirements.txt

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure Each Node

Create a launch script on each device:

**Device 1 (192.168.1.100)** - `start-node.sh`:
```bash
#!/bin/bash
# MarlOS Node Configuration

# Node Identity
export NODE_ID="laptop-1"
export NODE_NAME="Laptop-Ayush"

# Network Ports
export PUB_PORT=5555
export SUB_PORT=5556
export DASHBOARD_PORT=3001

# Bootstrap Peers (other devices)
export BOOTSTRAP_PEERS="tcp://192.168.1.101:5555,tcp://192.168.1.102:5555"

# Optional: Disable Docker for direct execution
export ENABLE_DOCKER=false

# Start the agent
echo "🚀 Starting MarlOS Node: $NODE_ID"
echo "📡 Bootstrap peers: $BOOTSTRAP_PEERS"
echo "🌐 Dashboard: http://0.0.0.0:$DASHBOARD_PORT"

python -m agent.main
```

**Device 2 (192.168.1.101)** - `start-node.sh`:
```bash
#!/bin/bash
export NODE_ID="laptop-2"
export NODE_NAME="Laptop-Arnav"
export PUB_PORT=5555
export SUB_PORT=5556
export DASHBOARD_PORT=3001
export BOOTSTRAP_PEERS="tcp://192.168.1.100:5555,tcp://192.168.1.102:5555"

python -m agent.main
```

**Device 3 (192.168.1.102)** - `start-node.sh`:
```bash
#!/bin/bash
export NODE_ID="desktop-1"
export NODE_NAME="Lab-Desktop"
export PUB_PORT=5555
export SUB_PORT=5556
export DASHBOARD_PORT=3001
export BOOTSTRAP_PEERS="tcp://192.168.1.100:5555,tcp://192.168.1.101:5555"

python -m agent.main
```

### Step 3: Make Scripts Executable and Run

```bash
chmod +x start-node.sh
./start-node.sh
```

### Step 4: Verify Network Discovery

**Check logs for peer discovery:**
```
[P2P] Starting node laptop-1
[P2P] Publisher bound to tcp://*:5555
[P2P] Connected to peer: tcp://192.168.1.101:5555
[P2P] Connected to peer: tcp://192.168.1.102:5555
[P2P] Received PEER_ANNOUNCE from laptop-2
[P2P] Received PEER_ANNOUNCE from desktop-1
```

**Access dashboard:**
```
http://192.168.1.100:3001  # Device 1
http://192.168.1.101:3001  # Device 2
http://192.168.1.102:3001  # Device 3
```

---

## Network Configuration

### Scenario 1: Same LAN (Local Network)

**Use Case:** All devices on same WiFi/Ethernet network (e.g., home lab, university network)

**Configuration:**
```bash
# Find each device's local IP
ip addr show      # Linux/Mac
ipconfig          # Windows

# Device 1: 192.168.1.100
export BOOTSTRAP_PEERS="tcp://192.168.1.101:5555,tcp://192.168.1.102:5555"

# Device 2: 192.168.1.101
export BOOTSTRAP_PEERS="tcp://192.168.1.100:5555,tcp://192.168.1.102:5555"

# Device 3: 192.168.1.102
export BOOTSTRAP_PEERS="tcp://192.168.1.100:5555,tcp://192.168.1.101:5555"
```

**Verification:**
```bash
# Test connectivity from Device 1
ping 192.168.1.101
ping 192.168.1.102

# Test port reachability
nc -zv 192.168.1.101 5555
nc -zv 192.168.1.102 5555
```

---

### Scenario 2: Different Networks (Internet/WAN)

**Use Case:** Devices in different locations (home, office, cloud)

**Requirements:**
- Public IP addresses or domain names
- Port forwarding on routers (ports 5555, 5556)
- Or use cloud server as bridge node

**Configuration:**

**Device 1 (Public IP: 203.0.113.45):**
```bash
export BOOTSTRAP_PEERS="tcp://198.51.100.89:5555,tcp://cloud-server.example.com:5555"
```

**Device 2 (Public IP: 198.51.100.89):**
```bash
export BOOTSTRAP_PEERS="tcp://203.0.113.45:5555,tcp://cloud-server.example.com:5555"
```

**Port Forwarding Setup:**

On your router:
```
External Port 5555 → Internal IP 192.168.1.100:5555
External Port 5556 → Internal IP 192.168.1.100:5556
```

**Dynamic DNS (Optional):**
```bash
# If your public IP changes frequently
# Use services like: No-IP, DuckDNS, Cloudflare DDNS

export BOOTSTRAP_PEERS="tcp://ayush-home.ddns.net:5555,tcp://arnav-lab.ddns.net:5555"
```

---

### Scenario 3: Hybrid Cloud + Local

**Use Case:** Mix of local devices and cloud servers

**Architecture:**
```
Local Devices (behind NAT) → Cloud Bridge Node (public IP) ← Remote Devices
```

**Cloud Server (203.0.113.45):**
```bash
export NODE_ID="cloud-bridge"
export BOOTSTRAP_PEERS=""  # No peers needed, acts as bootstrap point
python -m agent.main
```

**Local Devices (all NAT'd):**
```bash
# All local devices connect to cloud bridge
export BOOTSTRAP_PEERS="tcp://203.0.113.45:5555"
python -m agent.main
```

**Benefits:**
- No port forwarding needed on local routers
- Cloud server relays messages between NAT'd nodes
- Always-on availability

---

### Scenario 4: Raspberry Pi Cluster

**Use Case:** Dedicated compute cluster (edge computing, home lab)

**Hardware:**
- 4x Raspberry Pi 4 (4GB+ RAM recommended)
- Gigabit switch
- Static IP addresses

**Configuration:**

**Pi 1 (Coordinator) - 192.168.1.201:**
```bash
export NODE_ID="pi-coordinator"
export BOOTSTRAP_PEERS="tcp://192.168.1.202:5555,tcp://192.168.1.203:5555,tcp://192.168.1.204:5555"
python -m agent.main
```

**Pi 2-4 (Workers):**
```bash
# All workers bootstrap to Pi 1
export BOOTSTRAP_PEERS="tcp://192.168.1.201:5555"
python -m agent.main
```

**Performance Tips:**
- Use wired Ethernet (not WiFi) for stability
- Overclock RPi if needed (`/boot/config.txt`)
- Mount USB SSD for faster I/O
- Disable swap if using SD card

---

## Firewall & Security

### Linux (UFW)

```bash
# Allow MarlOS ports
sudo ufw allow 5555/tcp comment "MarlOS PUB"
sudo ufw allow 5556/tcp comment "MarlOS SUB"
sudo ufw allow 3001/tcp comment "MarlOS Dashboard"
sudo ufw allow 1883/tcp comment "MQTT Broker (optional)"

# Enable firewall
sudo ufw enable
sudo ufw status
```

### Linux (iptables)

```bash
sudo iptables -A INPUT -p tcp --dport 5555 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 5556 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 3001 -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4
```

### Windows Firewall

**PowerShell (Run as Administrator):**
```powershell
New-NetFirewallRule -DisplayName "MarlOS Ports" `
  -Direction Inbound `
  -Protocol TCP `
  -LocalPort 5555,5556,3001 `
  -Action Allow
```

**Or via GUI:**
1. Windows Security → Firewall & network protection
2. Advanced settings → Inbound Rules → New Rule
3. Port → TCP → 5555, 5556, 3001 → Allow

### macOS

```bash
# Add firewall exceptions (System Preferences → Security → Firewall)
# Or use command line (requires reboot):
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /usr/bin/python
```

### Security Best Practices

1. **Use SSH tunnels for sensitive networks:**
   ```bash
   ssh -L 5555:localhost:5555 user@remote-host
   ```

2. **Restrict to specific IPs (if possible):**
   ```bash
   sudo ufw allow from 192.168.1.0/24 to any port 5555
   ```

3. **Enable message encryption (already implemented):**
   - Ed25519 signatures verify message authenticity
   - TLS encryption for sensitive data (future enhancement)

4. **Monitor unauthorized access:**
   ```bash
   # Watch for suspicious connections
   watch -n 1 "netstat -tn | grep :5555"
   ```

---

## Testing & Verification

### Quick Test Script

Run the automated test suite to verify your deployment:

```bash
chmod +x test_deployment.sh
./test_deployment.sh

# Or specify custom port:
DASHBOARD_PORT=3001 ./test_deployment.sh
```

This will:
1. Check agent connectivity
2. Submit test jobs (echo, system info, python version)
3. Verify job execution
4. Display swarm status

---

### Manual Tests

### Test 1: Network Connectivity

```bash
# From Device 1, test reachability
ping -c 3 192.168.1.101
nc -zv 192.168.1.101 5555  # Should output: Connection succeeded
```

### Test 2: Node Discovery

```bash
# Check logs for successful peer discovery
tail -f data/agent.log | grep "PEER_ANNOUNCE"

# Expected output:
# [P2P] Received PEER_ANNOUNCE from laptop-2
# [P2P] Connected to peer: tcp://192.168.1.101:5555
```

### Test 3: Dashboard Access

```bash
# Check node status via API
curl http://192.168.1.100:3001/api/stats

# Expected response:
# {"node_id":"laptop-1","peers":2,"active_jobs":0,"wallet_balance":100.0}
```

### Test 4: Submit Test Job

```bash
# From any device with CLI installed
cd MarlOS
python cli/marlOS.py execute "echo 'Hello from distributed MarlOS!'"

# Or using the Marl alias (if configured):
# Marl execute "echo 'Hello from distributed MarlOS!'"

# Should see:
# ⚡ Executing: echo 'Hello from distributed MarlOS!'
# ✅ Job submitted via WebSocket: job-12345678
#    Type: shell
#    Payment: 10.0 AC
#    Priority: 0.5
```

**Check job execution in agent logs or dashboard:**
```bash
# Watch agent logs for auction and execution
tail -f data/agent.log | grep -E "(AUCTION|EXECUTOR|JOB)"

# Or access dashboard at:
http://192.168.1.100:3001  # Replace with your device IP
```

### Test 5: Load Balancing

```bash
# Submit multiple jobs and verify distribution
for i in {1..10}; do
  python -m cli.main execute "sleep 2 && echo Job $i"
done

# Check dashboard to see jobs distributed across nodes
```

### Test 6: Fault Tolerance

```bash
# Start 3 nodes, then kill one mid-job
# On Device 1: Submit long-running job
python -m cli.main execute "sleep 60 && echo Done"

# On Device 2: Kill the winning node (Ctrl+C)
# Job should automatically migrate to backup node
# Check logs: [RECOVERY] Job job_12345678 taken over by backup node
```

---

## Troubleshooting

### Problem: Nodes can't discover each other

**Symptoms:** No `PEER_ANNOUNCE` messages in logs

**Solutions:**
```bash
# 1. Verify network connectivity
ping <peer-ip>

# 2. Check firewall rules
sudo ufw status
telnet <peer-ip> 5555

# 3. Verify BOOTSTRAP_PEERS is correct
echo $BOOTSTRAP_PEERS

# 4. Check if ports are listening
netstat -tulpn | grep 5555
```

---

### Problem: "Connection refused" errors

**Symptoms:** `zmq.error.ZMQError: Connection refused`

**Solutions:**
```bash
# 1. Ensure node is actually running on target device
ps aux | grep "agent.main"

# 2. Check if port is bound
lsof -i :5555

# 3. Verify IP address is correct
ip addr show

# 4. Check firewall isn't blocking
sudo ufw status verbose
```

---

### Problem: High latency or slow job execution

**Symptoms:** Jobs take longer than expected

**Solutions:**
```bash
# 1. Check network latency
ping -c 10 <peer-ip>
# Ideal: <10ms on LAN, <100ms on WAN

# 2. Monitor CPU/memory usage
top
htop

# 3. Check for message queue buildup
# In dashboard, look for "Pending Messages" counter

# 4. Reduce concurrent jobs if needed
# Edit agent-config.yml:
executor:
  max_concurrent_jobs: 2  # Reduce from default 3
```

---

### Problem: "Peer not responding" warnings

**Symptoms:** `[WARN] Peer laptop-2 not responding to PING`

**Solutions:**
```bash
# 1. Check if peer is still running
ssh user@peer-ip "ps aux | grep agent.main"

# 2. Verify network stability
mtr <peer-ip>  # Shows packet loss

# 3. Check system clock sync (important!)
timedatectl status
# If clocks are skewed >30s, messages will be rejected

# 4. Restart unresponsive node
ssh user@peer-ip "pkill -f agent.main && ./start-node.sh"
```

---

### Problem: Jobs stuck in "pending" state

**Symptoms:** Job never gets executed

**Solutions:**
```bash
# 1. Check if any nodes are bidding
# In logs: [BIDDING] No bids received for job_12345678

# 2. Verify nodes have sufficient resources
# Check wallet balance: Should have > stake_requirement (10 AC)
curl http://localhost:3001/api/wallet

# 3. Check trust scores (must be > quarantine_threshold)
curl http://localhost:3001/api/reputation

# 4. Manually trigger job on specific node (debug mode)
export FORCE_BID=true
python -m agent.main
```

---

### Problem: Docker permissions errors (if using Docker)

**Symptoms:** `docker.errors.DockerException: Error while fetching server API`

**Solutions:**
```bash
# 1. Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# 2. Or disable Docker execution
export ENABLE_DOCKER=false

# 3. Use rootless Docker (security best practice)
dockerd-rootless-setuptool.sh install
```

---

## Advanced Topics

### Static IP Configuration

**Ubuntu/Debian (netplan):**
```yaml
# /etc/netplan/01-netcfg.yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: no
      addresses:
        - 192.168.1.100/24
      gateway4: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 1.1.1.1]
```

Apply: `sudo netplan apply`

---

### Systemd Service (Auto-start on Boot)

**Create service file:** `/etc/systemd/system/marlos.service`
```ini
[Unit]
Description=MarlOS Distributed Agent
After=network.target

[Service]
Type=simple
User=marlos
WorkingDirectory=/home/marlos/MarlOS
Environment="NODE_ID=laptop-1"
Environment="BOOTSTRAP_PEERS=tcp://192.168.1.101:5555,tcp://192.168.1.102:5555"
ExecStart=/home/marlos/MarlOS/venv/bin/python -m agent.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable marlos
sudo systemctl start marlos
sudo systemctl status marlos
```

---

### Monitoring & Observability

**Prometheus Metrics (Future Enhancement):**
```python
# Add to agent/main.py
from prometheus_client import start_http_server, Counter, Gauge

jobs_executed = Counter('marlos_jobs_executed_total', 'Total jobs executed')
active_peers = Gauge('marlos_active_peers', 'Number of active peers')
wallet_balance = Gauge('marlos_wallet_balance', 'Current wallet balance')

# Start metrics server
start_http_server(9090)
```

**Logging Best Practices:**
```bash
# Structured logging with rotation
python -m agent.main 2>&1 | tee -a logs/agent-$(date +%Y%m%d).log

# Or use systemd journal
journalctl -u marlos -f
```

---

### NAT Traversal (Advanced)

For devices behind strict NAT without port forwarding:

**Option 1: Use a relay server**
```python
# Deploy relay node on cloud with public IP
# All NAT'd nodes connect through relay
# Relay forwards messages between peers
```

**Option 2: Implement hole punching**
```python
# Use STUN servers to discover public endpoints
# Coordinate simultaneous connection attempts
# Establish P2P connection through NAT
```

**Option 3: Use VPN mesh network**
```bash
# Tailscale (easiest)
sudo tailscale up
# All devices get virtual IPs (e.g., 100.64.0.x)

export BOOTSTRAP_PEERS="tcp://100.64.0.2:5555,tcp://100.64.0.3:5555"
```

---

### Multi-Cloud Deployment

**Deploy on different cloud providers:**

**AWS EC2:**
```bash
# Launch t3.medium instance
# Security group: Allow 5555, 5556, 3001
export BOOTSTRAP_PEERS="tcp://<gcp-ip>:5555,tcp://<azure-ip>:5555"
```

**Google Cloud Compute:**
```bash
# Launch e2-medium instance
# Firewall rules: Allow tcp:5555-5556,3001
export BOOTSTRAP_PEERS="tcp://<aws-ip>:5555,tcp://<azure-ip>:5555"
```

**Azure VM:**
```bash
# Launch Standard_B2s instance
# Network security group: Allow 5555, 5556, 3001
export BOOTSTRAP_PEERS="tcp://<aws-ip>:5555,tcp://<gcp-ip>:5555"
```

**Benefits:**
- Geographic redundancy
- No single cloud vendor lock-in
- Reduced latency for global users

---

## Job Execution on Real Devices

### Job Types Available

MarlOS supports multiple job types. Here's what works with and without Docker:

| Job Type | Requires Docker? | Description |
|----------|------------------|-------------|
| **shell** | ❌ No | Execute shell commands directly (python, node, curl, etc.) |
| **malware_scan** | ❌ No | Scan files for malware using ClamAV |
| **port_scan** | ❌ No | Network port scanning using nmap |
| **hash_crack** | ❌ No | Password hash cracking using hashcat |
| **threat_intel** | ❌ No | Threat intelligence lookups |
| **led_control** | ❌ No | Hardware control via MQTT (requires hardware agent) |
| **docker** | ✅ Yes | Run commands in Docker containers |
| **docker_build** | ✅ Yes | Build Docker images |

### Shell Job Examples

**Basic command:**
```bash
python cli/marlOS.py execute "echo Hello World"
```

**System info:**
```bash
python cli/marlOS.py execute "uname -a"
python cli/marlOS.py execute "python --version"
```

**File operations:**
```bash
python cli/marlOS.py execute "ls -la /tmp"
python cli/marlOS.py execute "cat /etc/hosts"
```

**Network tests:**
```bash
python cli/marlOS.py execute "ping -c 3 google.com"
python cli/marlOS.py execute "curl https://api.github.com"
```

**Run Python code:**
```bash
python cli/marlOS.py execute "python -c 'print(2+2)'"
```

### Creating Complex Jobs

For non-shell jobs, create a job file:

**malware_scan.json:**
```json
{
  "job_type": "malware_scan",
  "priority": 0.7,
  "payment": 50.0,
  "payload": {
    "file_url": "https://example.com/suspicious.exe",
    "file_hash": "sha256:abc123..."
  }
}
```

Submit:
```bash
python cli/marlOS.py submit malware_scan.json
```

**port_scan.json:**
```json
{
  "job_type": "port_scan",
  "priority": 0.8,
  "payment": 30.0,
  "payload": {
    "target": "192.168.1.100",
    "ports": "1-1000"
  }
}
```

### Important Notes

1. **Shell Command Whitelist:** By default, shell jobs have security restrictions. Allowed commands:
   - File ops: `ls`, `cat`, `grep`, `find`, `head`, `tail`
   - System: `echo`, `pwd`, `date`, `hostname`, `uname`, `df`, `ps`
   - Network: `ping`, `curl`, `wget`
   - Dev tools: `python`, `node`, `npm`, `pip`, `git`

2. **Disable Docker (Optional):** If Docker is not installed:
   ```bash
   export ENABLE_DOCKER=false
   python -m agent.main
   ```
   This prevents Docker runner registration and avoids errors.

3. **Job Timeouts:** Default timeout is 60 seconds. Increase for long-running jobs:
   ```bash
   python cli/marlOS.py execute "sleep 120" --payment 20
   # Add timeout in job payload if using submit
   ```

---

## Comparison: Docker vs Real Devices

| Aspect | Docker Containers | Real Devices |
|--------|-------------------|--------------|
| **Discovery** | Service names (`marlos-agent-2`) | IP addresses (`192.168.1.101`) |
| **Networking** | Bridge network (`marlos-net`) | Real LAN/WAN |
| **Port Mapping** | Mapped (`5565:5555`) | Direct (`5555`) |
| **Configuration** | `docker-compose.yml` | Environment variables / scripts |
| **Isolation** | Container filesystem | Process-level |
| **Performance** | ~5-10% overhead | Native speed |
| **Resource Limits** | Docker constraints | OS limits |
| **Startup Time** | 2-5 seconds | <1 second |
| **Debugging** | `docker logs`, `docker exec` | Direct access, `ps`, `tail -f` |
| **Deployment** | `docker-compose up` | `./start-node.sh` |

---

## Key Advantages of Real Device Setup

1. **True Distributed Computing:** Actual compute resources from different machines
2. **Geographic Distribution:** Nodes can be in different cities/countries
3. **Heterogeneous Hardware:** Mix laptops, desktops, servers, Raspberry Pis, GPUs
4. **Fault Tolerance:** If one device crashes/loses power, others continue
5. **Real Network Conditions:** Test against actual latency, bandwidth, partitions
6. **No Container Overhead:** Direct hardware access for maximum performance
7. **Scalability:** Add new devices without Docker host limitations
8. **Edge Computing:** Deploy to IoT devices, embedded systems

---

## Conclusion

MarlOS's architecture makes the transition from Docker to real devices seamless:

- **No code changes required** – just configuration
- **ZeroMQ works across networks** – LAN, WAN, cloud
- **Gossip protocol handles discovery** – self-organizing
- **Fault tolerance built-in** – node failures don't stop the system

Your system is **production-ready** for distributed deployment!

---

## Next Steps

1. **Test on 2-3 devices first** – verify connectivity and discovery
2. **Monitor performance** – check latency, job distribution, fault recovery
3. **Scale gradually** – add more nodes as needed
4. **Deploy cloud bridge** – for NAT traversal (if needed)
5. **Set up monitoring** – Prometheus, Grafana, or custom dashboard

---

## Questions or Issues?

- Check logs: `tail -f data/agent.log`
- Inspect dashboard: `http://<node-ip>:3001`
- Debug with verbose mode: `export LOG_LEVEL=DEBUG`
- Review network design: `docs/NETWORK_DESIGN.md`
- Check architecture docs: `docs/ARCHITECTURE_RL.md`

---

**Built by Team async_await at Hack36**
