# MarlOS Deployment Guide

Complete reference for deploying MarlOS in every scenario, from a single dev node to a worldwide public network.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Port Reference](#port-reference)
3. [Environment Variables](#environment-variables)
4. [Single Node (Development)](#1-single-node-development)
5. [Multi-Node on One Machine](#2-multi-node-on-one-machine)
6. [Docker Deployment](#3-docker-deployment)
7. [LAN / Lab Setup](#4-lan--lab-setup)
8. [Cloud Deployment](#5-cloud-deployment)
9. [Public Mode (Worldwide)](#6-public-mode-worldwide)
10. [Monitoring and Health Checks](#7-monitoring-and-health-checks)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

All machines need:

- Python 3.11+
- Git
- pip

Install dependencies:

```bash
git clone https://github.com/ayush-jadaun/MarlOS.git
cd MarlOS
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

System packages (Linux only, optional):

```bash
# Ubuntu/Debian
sudo apt-get install -y libzmq3-dev nmap

# Fedora
sudo dnf install -y zeromq-devel nmap
```

macOS:

```bash
brew install zeromq nmap
```

---

## Port Reference

| Service        | Default Port | Env Var          | Protocol |
|----------------|--------------|------------------|----------|
| ZMQ Publisher  | 5555         | `PUB_PORT`       | TCP      |
| ZMQ Subscriber | 5556         | `SUB_PORT`       | TCP      |
| ZMQ Beacon     | 5557         | (hardcoded)      | TCP      |
| DHT (Public)   | 5559         | (config)         | UDP      |
| Dashboard (WS) | 3001         | `DASHBOARD_PORT` | TCP      |
| REST API       | 3101         | (dashboard + 100)| TCP      |

The REST API port is always `DASHBOARD_PORT + 100`. If `DASHBOARD_PORT=3001`, the REST API runs on `3101`.

---

## Environment Variables

Full list of env vars the agent reads at startup (defined in `agent/config.py:load_config()`):

| Variable          | Example                                      | Description                              |
|-------------------|----------------------------------------------|------------------------------------------|
| `NODE_ID`         | `laptop-1`                                   | Unique node identifier                   |
| `PUB_PORT`        | `5555`                                       | ZMQ publisher port                       |
| `SUB_PORT`        | `5556`                                       | ZMQ subscriber port                      |
| `DASHBOARD_PORT`  | `3001`                                       | WebSocket dashboard port                 |
| `NETWORK_MODE`    | `private` or `public`                        | Network operation mode                   |
| `BOOTSTRAP_PEERS` | `tcp://192.168.1.101:5555,tcp://192.168.1.102:5555` | Comma-separated peer PUB addresses |
| `DHT_ENABLED`     | `true`                                       | Enable Kademlia DHT (public mode)        |
| `DHT_BOOTSTRAP`   | `dht1.example.com:5559,dht2.example.com:5559` | DHT bootstrap nodes (host:port pairs)  |

If `NODE_ID` is not set, a random 8-char UUID is generated. Config precedence: dataclass defaults < YAML file (`~/.marlos/nodes/{NODE_ID}/config.yaml`) < env vars.

---

## 1. Single Node (Development)

The simplest way to run MarlOS. One node, no peers.

```bash
cd MarlOS
source venv/bin/activate

NODE_ID=dev-node python -m agent.main
```

The agent starts and prints its endpoints:

```
Dashboard URLs:
  - Local:   http://localhost:3001
  - Network: http://<your-ip>:3001
REST API: http://<your-ip>:3101
P2P Address: tcp://<your-ip>:5555
```

Submit a test job from a second terminal:

```bash
# Via CLI
source venv/bin/activate
python -m cli.main execute "echo hello world"

# Via REST API
curl -X POST http://localhost:3101/api/jobs \
  -H "Content-Type: application/json" \
  -d '{"job_type": "shell", "payload": {"command": "echo hello world"}, "payment": 50.0}'

# Via Python
python -c "
import asyncio, sys, os
sys.path.insert(0, '.')
from cli.marlOS import submit_job
submit_job({'job_type': 'shell', 'payload': {'command': 'echo hello'}, 'payment': 50.0})
"
```

Custom ports (useful if defaults conflict):

```bash
NODE_ID=dev-node PUB_PORT=6000 SUB_PORT=6001 DASHBOARD_PORT=4001 python -m agent.main
# REST API will be on 4101
```

---

## 2. Multi-Node on One Machine

### Option A: Use the Demo Script

The demo script (`scripts/demo.py`) starts multiple nodes on localhost with auto-wired ports and runs a full lifecycle (discovery, auction, execution, token transfer).

```bash
# Default: 3 nodes, 2 jobs
python scripts/demo.py

# Custom: 5 nodes, 10 jobs
python scripts/demo.py --nodes 5 --jobs 10
```

Port allocation by the demo script:

| Node | PUB Port | SUB Port | Dashboard |
|------|----------|----------|-----------|
| 1    | 6000     | 6001     | 4001      |
| 2    | 6010     | 6011     | 4002      |
| 3    | 6020     | 6021     | 4003      |
| N    | 6000+(N-1)*10 | 6001+(N-1)*10 | 4000+N |

The script handles peer wiring, cleanup, and prints results for each step.

### Option B: Manual Multi-Node

Open separate terminals. Each node needs unique ports and must list the others as bootstrap peers.

**Terminal 1:**

```bash
NODE_ID=node-1 PUB_PORT=5555 SUB_PORT=5556 DASHBOARD_PORT=3001 \
  BOOTSTRAP_PEERS="tcp://127.0.0.1:5565,tcp://127.0.0.1:5575" \
  python -m agent.main
```

**Terminal 2:**

```bash
NODE_ID=node-2 PUB_PORT=5565 SUB_PORT=5566 DASHBOARD_PORT=3002 \
  BOOTSTRAP_PEERS="tcp://127.0.0.1:5555,tcp://127.0.0.1:5575" \
  python -m agent.main
```

**Terminal 3:**

```bash
NODE_ID=node-3 PUB_PORT=5575 SUB_PORT=5576 DASHBOARD_PORT=3003 \
  BOOTSTRAP_PEERS="tcp://127.0.0.1:5555,tcp://127.0.0.1:5565" \
  python -m agent.main
```

Nodes discover each other via `PEER_ANNOUNCE` gossip within 5-10 seconds. Dashboards are at `http://localhost:3001`, `:3002`, `:3003`. REST APIs at `:3101`, `:3102`, `:3103`.

---

## 3. Docker Deployment

The project includes `docker-compose.yml` with 3 pre-configured agents and an optimized multi-stage Dockerfile.

### Start the cluster

```bash
# Build and start all 3 agents
docker-compose up -d --build

# Watch logs
docker-compose logs -f

# Watch a single agent
docker-compose logs -f agent-1
```

### Port mapping (host:container)

| Agent   | ZMQ PUB    | ZMQ SUB    | Dashboard  |
|---------|------------|------------|------------|
| agent-1 | 5555:5555  | 5556:5556  | 8081:3001  |
| agent-2 | 5565:5555  | 5566:5556  | 8082:3001  |
| agent-3 | 5575:5555  | 5576:5556  | 8083:3001  |

Inside the Docker bridge network (`marlos-net`), containers use internal DNS names (`marlos-agent-1`, `marlos-agent-2`, `marlos-agent-3`) and standard ports. The host-mapped ports are different to avoid conflicts.

### Access dashboards

```
http://localhost:8081   # agent-1
http://localhost:8082   # agent-2
http://localhost:8083   # agent-3
```

### Submit a job into the Docker cluster

```bash
# Hit agent-1's REST API (mapped to host port 8081+100 won't work; use the mapped dashboard port)
# The REST API inside the container is on 3101, but it's not port-mapped by default.
# Option 1: exec into a container
docker exec -it marlos-agent-1 python -c "
import asyncio
from cli.marlOS import submit_job
submit_job({'job_type': 'shell', 'payload': {'command': 'echo hello from docker'}, 'payment': 50.0})
"

# Option 2: Add REST API port mapping to docker-compose.yml if you want external access:
#   ports:
#     - "3101:3101"
```

### Stop and clean up

```bash
docker-compose down          # stop containers
docker-compose down -v       # stop and remove volumes
docker-compose down --rmi all  # also remove images
```

### Custom Dockerfile

Two Dockerfiles are available:

- `docker/Dockerfile.agent` -- full image with ClamAV (large, ~2GB+)
- `docker/Dockerfile.agent.optimized` -- multi-stage, CPU-only PyTorch, no ClamAV (~800MB)

The compose file uses the optimized one. To switch:

```yaml
build:
  dockerfile: docker/Dockerfile.agent  # full version
```

---

## 4. LAN / Lab Setup

Deploying on 5+ laptops/desktops on the same WiFi or wired network. This is the most common real-world demo scenario.

### Step 1: Install on every machine

Run on each laptop:

```bash
git clone https://github.com/ayush-jadaun/MarlOS.git
cd MarlOS
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Get each machine's IP

```bash
# Linux/macOS
ip addr show | grep "inet " | grep -v 127.0.0.1
# or: hostname -I

# macOS alternative
ipconfig getifaddr en0

# Windows
ipconfig | findstr "IPv4"
```

Write down the IPs. Example for 5 laptops:

| Machine  | IP              | NODE_ID    |
|----------|-----------------|------------|
| Laptop A | 192.168.1.100   | laptop-a   |
| Laptop B | 192.168.1.101   | laptop-b   |
| Laptop C | 192.168.1.102   | laptop-c   |
| Laptop D | 192.168.1.103   | laptop-d   |
| Laptop E | 192.168.1.104   | laptop-e   |

### Step 3: Open firewall ports on each machine

**Linux (UFW):**

```bash
sudo ufw allow 5555/tcp
sudo ufw allow 5556/tcp
sudo ufw allow 3001/tcp
sudo ufw allow 3101/tcp
```

**Windows (PowerShell as Admin):**

```powershell
New-NetFirewallRule -DisplayName "MarlOS" -Direction Inbound -Protocol TCP -LocalPort 5555,5556,3001,3101 -Action Allow
```

**macOS:**

```bash
# macOS firewall usually allows outgoing. For incoming, add Python to allowed apps:
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add $(which python3)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp $(which python3)
```

### Step 4: Test connectivity between machines

From Laptop A, ping every other machine:

```bash
ping -c 2 192.168.1.101
ping -c 2 192.168.1.102
ping -c 2 192.168.1.103
ping -c 2 192.168.1.104
```

If any fail, fix the network first. Common issues: machines on different WiFi bands (2.4 vs 5GHz), AP isolation enabled on the router, or firewall blocking ICMP.

### Step 5: Start nodes

You do not need to list every peer. Each node only needs 1-2 bootstrap peers. Gossip protocol handles full mesh discovery.

**Laptop A (192.168.1.100):**

```bash
cd MarlOS && source venv/bin/activate
NODE_ID=laptop-a \
  BOOTSTRAP_PEERS="tcp://192.168.1.101:5555,tcp://192.168.1.102:5555" \
  python -m agent.main
```

**Laptop B (192.168.1.101):**

```bash
cd MarlOS && source venv/bin/activate
NODE_ID=laptop-b \
  BOOTSTRAP_PEERS="tcp://192.168.1.100:5555,tcp://192.168.1.102:5555" \
  python -m agent.main
```

**Laptop C (192.168.1.102):**

```bash
cd MarlOS && source venv/bin/activate
NODE_ID=laptop-c \
  BOOTSTRAP_PEERS="tcp://192.168.1.100:5555" \
  python -m agent.main
```

**Laptop D (192.168.1.103):**

```bash
cd MarlOS && source venv/bin/activate
NODE_ID=laptop-d \
  BOOTSTRAP_PEERS="tcp://192.168.1.100:5555" \
  python -m agent.main
```

**Laptop E (192.168.1.104):**

```bash
cd MarlOS && source venv/bin/activate
NODE_ID=laptop-e \
  BOOTSTRAP_PEERS="tcp://192.168.1.101:5555" \
  python -m agent.main
```

### Step 6: Verify discovery

Wait 10-15 seconds. Each node's logs should show:

```
[P2P] Received PEER_ANNOUNCE from laptop-b
[P2P] Received PEER_ANNOUNCE from laptop-c
...
```

Check peer count via REST API from any machine:

```bash
curl http://192.168.1.100:3101/api/peers
# Expected: {"peers": [...], "count": 4}

curl http://192.168.1.100:3101/api/health
# Expected: {"status": "ok", "node_id": "laptop-a"}
```

Or open any node's dashboard in a browser: `http://192.168.1.100:3001`

### Step 7: Submit jobs

From any machine:

```bash
# Via CLI (submits to the local node, which broadcasts to the network)
python -m cli.main execute "echo 'Hello from the MarlOS swarm'"

# Via REST API targeting a specific node
curl -X POST http://192.168.1.100:3101/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "shell",
    "payload": {"command": "hostname && date"},
    "payment": 50.0,
    "priority": 0.8
  }'
```

The job is broadcast to all peers. Nodes bid using their RL policy, a coordinator picks the winner, and the winner executes the job. Watch the logs to see the auction and execution in real time.

### Quick-reference: one-liner per machine

For a fast demo, give each person this one command (replace IP and PEER):

```bash
cd MarlOS && source venv/bin/activate && NODE_ID=$(hostname) BOOTSTRAP_PEERS="tcp://<SEED_NODE_IP>:5555" python -m agent.main
```

Where `<SEED_NODE_IP>` is the IP of whichever machine starts first.

---

## 5. Cloud Deployment

Deploying on VPS instances (DigitalOcean, Oracle Cloud, Vultr, Hetzner, fly.io, etc.).

### Provision and install

```bash
# SSH into your VPS
ssh root@203.0.113.10

# Install system deps
apt-get update && apt-get install -y python3 python3-pip python3-venv git libzmq3-dev

# Clone and setup
git clone https://github.com/ayush-jadaun/MarlOS.git
cd MarlOS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Firewall rules

Every cloud provider has its own security group / firewall UI. You must allow inbound TCP on these ports:

| Port | Purpose       |
|------|---------------|
| 5555 | ZMQ Publisher |
| 5556 | ZMQ Subscriber|
| 3001 | Dashboard     |
| 3101 | REST API      |

**DigitalOcean:** Networking > Firewalls > Create Firewall > Add inbound rules for TCP 5555, 5556, 3001, 3101.

**Oracle Cloud:** VCN > Security Lists > Add Ingress Rules for TCP 5555-5556, 3001, 3101 from 0.0.0.0/0 (or restrict to known CIDRs).

**fly.io:** In `fly.toml`, expose the ports. Or use `flyctl proxy` for ZMQ ports.

**UFW on the VPS itself:**

```bash
sudo ufw allow 22/tcp     # SSH (don't lock yourself out)
sudo ufw allow 5555/tcp
sudo ufw allow 5556/tcp
sudo ufw allow 3001/tcp
sudo ufw allow 3101/tcp
sudo ufw enable
```

### Start the node

```bash
NODE_ID=cloud-vps-1 \
  BOOTSTRAP_PEERS="tcp://198.51.100.20:5555,tcp://203.0.113.30:5555" \
  python -m agent.main
```

### Run as a systemd service (auto-restart, boot persistence)

Create `/etc/systemd/system/marlos.service`:

```ini
[Unit]
Description=MarlOS Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/MarlOS
Environment="NODE_ID=cloud-vps-1"
Environment="BOOTSTRAP_PEERS=tcp://198.51.100.20:5555"
ExecStart=/root/MarlOS/venv/bin/python -m agent.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable marlos
sudo systemctl start marlos

# Check status
sudo systemctl status marlos

# View logs
journalctl -u marlos -f
```

### Hybrid: cloud + local machines

Use one cloud VPS as a "bridge" node with a public IP. All local machines behind NAT connect to it. They do not need port forwarding.

```
Local laptops  ---->  Cloud bridge (public IP)  <----  Other remote nodes
                      tcp://203.0.113.10:5555
```

**Cloud bridge:**

```bash
NODE_ID=bridge BOOTSTRAP_PEERS="" python -m agent.main
```

**Every local machine:**

```bash
NODE_ID=my-laptop BOOTSTRAP_PEERS="tcp://203.0.113.10:5555" python -m agent.main
```

The bridge relays `PEER_ANNOUNCE` messages. Local nodes behind NAT can subscribe to the bridge's PUB socket without needing inbound ports open. However, note that other peers cannot directly connect back to a NATed node's PUB socket. For full bidirectional P2P behind NAT, use a VPN mesh like Tailscale:

```bash
# After installing Tailscale on all machines:
sudo tailscale up

# Use Tailscale IPs (100.x.y.z) as bootstrap peers
NODE_ID=my-laptop BOOTSTRAP_PEERS="tcp://100.64.0.2:5555,tcp://100.64.0.3:5555" python -m agent.main
```

---

## 6. Public Mode (Worldwide)

Public mode uses Kademlia DHT for automatic peer discovery. Any machine can join without knowing specific peer IPs ahead of time.

**Status:** DHT bootstrap infrastructure is partially implemented. The `DHTManager` in `agent/p2p/dht_manager.py` works, but there are no permanently running public DHT bootstrap nodes yet. You can set up your own.

### How it works

1. Node starts in public mode with DHT enabled.
2. Node contacts DHT bootstrap nodes to join the Kademlia overlay.
3. Node announces itself to the DHT (`marlos_peer_{node_id}` key).
4. Node periodically queries the DHT for `marlos_global_peers` to discover other nodes.
5. Discovered peers are connected via ZMQ, same as private mode.
6. Sybil resistance: minimum 10 AC stake required, max 3 peers per /24 subnet.

### Set up your own DHT bootstrap node

Pick a VPS with a public IP. Run a MarlOS node in public mode:

```bash
NODE_ID=dht-bootstrap-1 \
  NETWORK_MODE=public \
  DHT_ENABLED=true \
  python -m agent.main
```

This node listens on UDP 5559 for DHT traffic and TCP 5555 for ZMQ. Note its public IP.

### Join the public network

On any machine anywhere:

```bash
NODE_ID=my-node \
  NETWORK_MODE=public \
  DHT_ENABLED=true \
  DHT_BOOTSTRAP="203.0.113.10:5559,198.51.100.20:5559" \
  python -m agent.main
```

The `DHT_BOOTSTRAP` variable takes comma-separated `host:port` pairs pointing to your DHT bootstrap nodes.

### Env vars summary for public mode

```bash
export NODE_ID="worldwide-node-42"
export NETWORK_MODE="public"
export DHT_ENABLED="true"
export DHT_BOOTSTRAP="dht1.yourserver.com:5559,dht2.yourserver.com:5559"
python -m agent.main
```

### Combining with bootstrap peers

You can use both DHT and explicit bootstrap peers. This is useful as a fallback:

```bash
NODE_ID=my-node \
  NETWORK_MODE=public \
  DHT_ENABLED=true \
  DHT_BOOTSTRAP="dht1.yourserver.com:5559" \
  BOOTSTRAP_PEERS="tcp://203.0.113.10:5555" \
  python -m agent.main
```

### Firewall for public mode

In addition to the standard ports, open the DHT port:

```bash
sudo ufw allow 5559/udp   # Kademlia DHT
sudo ufw allow 5555/tcp   # ZMQ PUB
sudo ufw allow 5556/tcp   # ZMQ SUB
```

---

## 7. Monitoring and Health Checks

### Dashboard (WebSocket)

Every running node exposes a real-time WebSocket dashboard:

```
http://<node-ip>:<DASHBOARD_PORT>
```

Default: `http://localhost:3001`

Connect from any browser on the same network. The dashboard shows peers, jobs, wallet balance, trust scores, and RL stats via live WebSocket updates.

### REST API

The REST API runs on `DASHBOARD_PORT + 100` (default: 3101). All endpoints return JSON.

**Health check:**

```bash
curl http://localhost:3101/api/health
# {"status": "ok", "node_id": "dev-node"}
```

**Full node status:**

```bash
curl http://localhost:3101/api/status
```

**List peers:**

```bash
curl http://localhost:3101/api/peers
# {"peers": [{"node_id": "...", "capabilities": [...], "trust": 0.5}], "count": 4}
```

**Wallet info:**

```bash
curl http://localhost:3101/api/wallet
# {"balance": 95.0, "staked": 10.0, "total_value": 105.0, "lifetime_earned": 150.0, "lifetime_spent": 55.0}
```

**Trust scores:**

```bash
curl http://localhost:3101/api/trust
# {"my_trust": 0.52, "quarantined": false, "peer_scores": {"node-2": 0.5, "node-3": 0.48}}
```

**RL / online learning stats:**

```bash
curl http://localhost:3101/api/rl
# {"online_learning": true, "buffer_size": 42, "updates_performed": 3, "exploration_rate": 0.09}
```

**Submit a job:**

```bash
curl -X POST http://localhost:3101/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "shell",
    "payload": {"command": "uname -a"},
    "payment": 30.0,
    "priority": 0.5
  }'
# {"job_id": "job-a1b2c3d4", "status": "submitted", "message": "Job broadcast to network for auction"}
```

**Check job result:**

```bash
curl http://localhost:3101/api/jobs/job-a1b2c3d4
# {"job_id": "job-a1b2c3d4", "status": "completed", "result": "Linux ...", "duration": 0.12}
```

**List all jobs:**

```bash
curl http://localhost:3101/api/jobs
```

**Submit a pipeline (DAG of jobs):**

```bash
curl -X POST http://localhost:3101/api/pipelines \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-pipeline",
    "stages": [
      {"job_type": "shell", "payload": {"command": "echo step1"}, "payment": 10.0},
      {"job_type": "shell", "payload": {"command": "echo step2"}, "payment": 10.0, "depends_on": [0]}
    ]
  }'
```

**Submit a batch group:**

```bash
curl -X POST http://localhost:3101/api/groups \
  -H "Content-Type: application/json" \
  -d '{
    "jobs": [
      {"job_type": "shell", "payload": {"command": "echo job1"}, "payment": 10.0},
      {"job_type": "shell", "payload": {"command": "echo job2"}, "payment": 10.0}
    ]
  }'
```

### Monitoring multiple nodes

Script to poll health across your cluster:

```bash
#!/bin/bash
NODES=("192.168.1.100:3101" "192.168.1.101:3101" "192.168.1.102:3101")

for node in "${NODES[@]}"; do
  status=$(curl -s --max-time 3 "http://$node/api/health" 2>/dev/null)
  if [ $? -eq 0 ]; then
    echo "OK   $node  $status"
  else
    echo "DOWN $node"
  fi
done
```

### Log monitoring

```bash
# If running directly
python -m agent.main 2>&1 | tee agent.log

# If running as systemd service
journalctl -u marlos -f --no-pager

# If running in Docker
docker-compose logs -f agent-1
```

---

## Troubleshooting

### Nodes cannot discover each other

1. Verify connectivity: `ping <peer-ip>`
2. Verify the port is open: `nc -zv <peer-ip> 5555` (Linux/macOS) or `Test-NetConnection -ComputerName <peer-ip> -Port 5555` (PowerShell)
3. Check `BOOTSTRAP_PEERS` format -- must be `tcp://IP:PORT`, comma-separated, no spaces
4. Wait 10-15 seconds for gossip to propagate
5. Check firewall rules on both sides

### "Address already in use" error

Another process is using the port. Either kill it or use different ports:

```bash
# Find what's using port 5555
lsof -i :5555        # Linux/macOS
netstat -ano | findstr :5555   # Windows

# Use different ports
PUB_PORT=6555 SUB_PORT=6556 DASHBOARD_PORT=4001 python -m agent.main
```

### Clock skew causing message rejection

MarlOS rejects messages with timestamps more than 30 seconds off. Sync clocks:

```bash
# Linux
sudo timedatectl set-ntp true

# macOS
sudo sntp -sS time.apple.com

# Windows
w32tm /resync
```

### Docker "connection refused" between containers

Make sure all containers are on the same Docker network (`marlos-net`). Containers reference each other by container name (`marlos-agent-1`), not `localhost`.

### Jobs stuck in "pending"

- Check that nodes have sufficient wallet balance (> 10 AC stake requirement)
- Check trust scores are above quarantine threshold (0.2)
- Verify at least one node supports the requested `job_type`
- Check with: `curl http://localhost:3101/api/wallet` and `curl http://localhost:3101/api/trust`

---

**Built by Team async_await at Hack36**
