<h1 align="center">MarlOS</h1>
<p align="center"><strong>Decentralized, self-organizing compute network powered by Multi-Agent Reinforcement Learning</strong></p>
<p align="center">
  <a href="https://github.com/ayush-jadaun/MarlOS/actions/workflows/ci.yml"><img src="https://github.com/ayush-jadaun/MarlOS/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://youtu.be/EGv7Z3kXv30"><img src="https://img.shields.io/badge/YouTube-Demo-red?style=flat-square&logo=youtube" /></a>
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" />
</p>

---

MarlOS is a **peer-to-peer distributed computing OS** where every node is autonomous, cryptographically authenticated, and makes its own bidding decisions using reinforcement learning — with no central orchestrator, no Kubernetes, no cloud controller.

When a job enters the network, nodes independently decide whether to **Bid**, **Forward**, or **Defer** it. The winner is determined by a decentralized auction. Payment flows automatically via a token economy. Nodes that fail get replaced by their pre-assigned backups. Nodes that misbehave get quarantined by the trust system.

The whole thing runs without asking permission from anyone.

---

## Why This Matters

Centralized compute infrastructure (AWS, Kubernetes, Ray) has a fundamental problem: there is always a single point of control. That control can be taken away, rate-limited, or priced out of reach.

MarlOS is the opposite. Any device — a laptop, a server, a Raspberry Pi — can join the network, earn tokens by completing jobs, and participate as a first-class compute node. No registration. No approval. Cryptographic identity is self-generated on first start.

This architecture is particularly relevant for the current shift toward **agentic AI**: when AI agents (Claude, GPT, AutoGen crews) need to execute code, run containers, scan networks, or process files, they need a compute layer that is cheap, decentralized, and programmable. MarlOS is designed to be exactly that layer.

---

## How It Works

### Data Flow

```
Job Submitted
     │
     ▼
[P2P Broadcast] ──── ZeroMQ PUB/SUB ────► All Nodes Receive
                                                │
                                    ┌───────────┼───────────┐
                                    ▼           ▼           ▼
                                  BID        FORWARD      DEFER
                              (RL decides) (RL decides) (RL decides)
                                    │
                                    ▼
                           [Decentralized Auction]
                           Ed25519-signed bids
                           Deterministic winner
                                    │
                                    ▼
                           [Winner Claims Job]
                           Stakes MarlCredits
                           Assigns backup node
                                    │
                                    ▼
                           [Execution Engine]
                           Shell / Docker / Security
                                    │
                              ┌─────┴─────┐
                              ▼           ▼
                          Success       Failure
                              │           │
                         Pay winner   Slash stake
                         +trust       -trust
                         +reputation  RecoveryManager
                                      takes over
```

### The Three Decisions (RL Actions)

Every node runs a **PPO policy** trained on a 25-dimensional state vector. For each incoming job, the policy outputs one of:

| Action | When | Effect |
|--------|------|--------|
| `BID=0` | Node has capacity, good match | Enter decentralized auction |
| `FORWARD=1` | Another node is better suited | Route job to that peer |
| `DEFER=2` | Overloaded or low trust | Skip this job |

The 25D state vector encodes: CPU/memory/disk, job type and priority, wallet balance, peer count, historical success rate, trust score, and 7 fairness metrics (Gini coefficient, diversity factor, UBI eligibility, tax rate, affirmative boost, job complexity, cooperative index).

See [`docs/ARCHITECTURE_RL.md`](docs/ARCHITECTURE_RL.md) for full state vector specification and training methodology.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        MarlOS Node                          │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  P2P     │  │  RL      │  │ Bidding  │  │ Executor │   │
│  │ ZMQ      │  │ Policy   │  │ Auction  │  │ Engine   │   │
│  │ Ed25519  │  │ PPO      │  │ Scorer   │  │ Shell    │   │
│  │ Gossip   │  │ 25D state│  │ Router   │  │ Docker   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  │ Security │   │
│       │             │             │         └──────────┘   │
│       └─────────────┴─────────────┘                        │
│                           │                                 │
│  ┌──────────┐  ┌──────────┴──┐  ┌──────────┐  ┌────────┐  │
│  │  Token   │  │   Trust /   │  │Predictive│  │ Dash-  │  │
│  │ Economy  │  │ Reputation  │  │Pre-exec  │  │ board  │  │
│  │ Wallet   │  │ Quarantine  │  │Spec cache│  │ WS:3001│  │
│  │ Ledger   │  │ Watchdog    │  │RL specul │  │        │  │
│  └──────────┘  └─────────────┘  └──────────┘  └────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Key Source Files

| Component | File | Purpose |
|-----------|------|---------|
| Main agent | `agent/main.py` | Wires all components; message handlers |
| Configuration | `agent/config.py` | 3-tier config: defaults → YAML → env vars |
| P2P network | `agent/p2p/node.py` | ZMQ gossip, Ed25519 auth, rate limiting |
| Message protocol | `agent/p2p/protocol.py` | All message types and dataclasses |
| RL policy | `agent/rl/policy.py` | PPO decision engine (BID/FORWARD/DEFER) |
| State calculator | `agent/rl/state.py` | 25D state vector builder |
| Auction | `agent/bidding/auction.py` | Non-blocking decentralized auction |
| Bid scorer | `agent/bidding/scorer.py` | Score calculation for bids |
| Job router | `agent/bidding/router.py` | Peer selection for FORWARD action |
| Execution engine | `agent/executor/engine.py` | Job dispatch and tracking |
| Recovery manager | `agent/executor/recovery.py` | Heartbeat monitoring and job takeover |
| Wallet | `agent/tokens/wallet.py` | SQLite-backed token balance and staking |
| Ledger | `agent/tokens/ledger.py` | Distributed transaction log |
| Token economy | `agent/tokens/economy.py` | Payment calculation, taxation, UBI |
| Reputation | `agent/trust/reputation.py` | 0.0–1.0 trust scores, quarantine logic |
| Watchdog | `agent/trust/watchdog.py` | Automatic trust penalisation |
| DHT manager | `agent/p2p/dht_manager.py` | Kademlia peer discovery (public mode) |
| Coordinator | `agent/p2p/coordinator.py` | Deterministic leader election |
| Predictive | `agent/predictive/` | RL-powered speculative pre-execution |
| Dashboard | `agent/dashboard/server.py` | WebSocket dashboard on port 3001 |
| CLI | `cli/main.py` | `marl` command entry point |
| RL trainer | `rl_trainer/train_policy.py` | Offline PPO training script |

---

## What Makes It Different

### 1. Nodes make their own decisions using RL

There is no scheduler, no central queue, no master node assigning work. Each node independently evaluates every job against its own state and the network context, then decides what to do. The PPO policy is trained across four market scenarios — normal operation, high competition, resource scarcity, and job abundance — so it generalises across real-world conditions.

### 2. Fairness is a first-class citizen

Seven fairness metrics are embedded directly in the RL state vector. The reward function penalises monopolisation, rewards cooperative behaviour, and includes progressive taxation, UBI for struggling nodes, and affirmative action bonuses for nodes with low win rates. Wealth inequality (Gini coefficient) is a live network metric that influences every bidding decision.

See [`docs/ARCHITECTURE_TOKEN.md`](docs/ARCHITECTURE_TOKEN.md) for the full economic model.

### 3. Cryptographic security without a blockchain

Every P2P message is Ed25519-signed with a timestamp and nonce. Replay protection, clock synchronisation, and quorum consensus are built into the message layer. No proof-of-work, no gas fees, no blockchain overhead.

### 4. Self-healing at the protocol level

When a node wins a job, it selects a backup node (second-highest bidder) and broadcasts a `JOB_CLAIM` message naming both. The backup monitors heartbeats. If the primary goes silent for 15 seconds, the backup takes over — resuming from the last checkpoint if one exists — and broadcasts a `JOB_TAKEOVER` message so the rest of the network updates their state. No human intervention required.

See [`docs/CHECKPOINT_RECOVERY_GUIDE.md`](docs/CHECKPOINT_RECOVERY_GUIDE.md) for details.

### 5. Any hardware can participate

The execution engine is extensible. Currently registered runners:
- `shell` — arbitrary shell commands
- `docker` — containerised workloads
- `docker_build` — container builds
- `malware_scan`, `port_scan`, `hash_crack`, `threat_intel` — security tools

Adding a new runner is registering a single async function. See `agent/main.py::_register_job_runners()`.

---

## Network Modes

### Private Mode (default)

Nodes connect to a manually specified peer list. Suitable for a home lab, a team's machines, or an office network. Peers are saved to `~/.marlos/peers.json` and auto-reconnected on restart.

```bash
NODE_ID=node-1 BOOTSTRAP_PEERS="tcp://192.168.1.100:5555" python -m agent.main
```

### Public Mode

Uses Kademlia DHT for automatic global peer discovery. Any MarlOS node running in public mode serves as a bootstrap point. Sybil resistance is enforced: nodes must have a minimum token balance (`min_peer_stake=10 AC`) and each /24 subnet is limited to 3 peers.

```bash
NODE_ID=node-1 NETWORK_MODE=public DHT_ENABLED=true \
  DHT_BOOTSTRAP="bootstrap1.example.com:5559" python -m agent.main
```

See [`docs/USER_GUIDE_NETWORK_MODES.md`](docs/USER_GUIDE_NETWORK_MODES.md) and [`docs/NETWORK_DESIGN.md`](docs/NETWORK_DESIGN.md).

---

## What This Can Become

MarlOS was built as a hackathon project. The infrastructure is real. Here is what it is positioned to grow into:

### Distributed AI Agent Compute

The BID/FORWARD/DEFER action space maps directly to how AI orchestrators (LangGraph, AutoGen, CrewAI) route tasks. A MarlOS network becomes a **P2P compute marketplace for AI agents**: Claude submits a job via MCP, the network auctions it, the winning node executes it, payment flows in MarlCredits. No AWS, no fixed pricing, no single provider.

The WebSocket dashboard on port 3001 is one layer away from becoming an MCP server. The `ai_task` job type can be added as a runner in the same way `shell` or `docker` was added.

### Private Compute Mesh for Teams

Private mode works today. A team of 5 developers with MarlOS on their laptops gets automatic workload distribution, token-based billing between teammates, and fault-tolerant job execution. No infrastructure needed beyond the machines themselves.

---

## Current Status

| Feature | Status |
|---------|--------|
| P2P messaging (ZMQ + Ed25519) | Working |
| Decentralized auction | Working |
| RL bidding (PPO) | Working |
| Token economy | Working |
| Trust / reputation / quarantine | Working |
| Self-healing (heartbeat + takeover) | Working |
| Job forwarding (JOB_FORWARD handler) | Fixed — was broken |
| Predictive pre-execution | Working |
| Dashboard (WebSocket) | Working |
| Private mode (manual peers) | Working |
| Public mode (DHT discovery) | Partially working — bootstrap wired, PEX loop closed |
| Online RL learning | Working — was a no-op, now fixed |
| Integration tests (multi-node) | 1/10 pass — active area of work |

---

## Getting Started

### Install with pip

```bash
pip install git+https://github.com/ayush-jadaun/MarlOS.git
marl start
```

See [`docs/PIP_INSTALL.md`](docs/PIP_INSTALL.md). If `marl` is not found after install, see [`docs/PATH_SETUP_QUICK_REFERENCE.md`](docs/PATH_SETUP_QUICK_REFERENCE.md).

### Install with one-line script

```bash
curl -sSL https://raw.githubusercontent.com/ayush-jadaun/MarlOS/main/scripts/install-marlos.sh | bash
```

### Run with Docker (local multi-node testing)

```bash
docker-compose up -d   # starts 3 nodes
```

### Manual setup (real devices)

```bash
# On each device:
git clone https://github.com/ayush-jadaun/MarlOS.git && cd MarlOS
pip install -e .

# Node 1 (no bootstrap needed — it IS the bootstrap)
NODE_ID=node-1 python -m agent.main

# Node 2 (points at node-1)
NODE_ID=node-2 BOOTSTRAP_PEERS="tcp://<node1-ip>:5555" python -m agent.main

# Submit a job from anywhere
marl execute "echo hello from the mesh"
```

See [`docs/QUICKSTART.md`](docs/QUICKSTART.md) and [`docs/DISTRIBUTED_DEPLOYMENT.md`](docs/DISTRIBUTED_DEPLOYMENT.md).

### Configuration

Configuration is resolved in three layers (highest priority wins):

| Layer | Source | Example |
|-------|--------|---------|
| 1 (lowest) | Dataclass defaults in `agent/config.py` | `pub_port=5555` |
| 2 | YAML file at `~/.marlos/nodes/{NODE_ID}/config.yaml` | custom node config |
| 3 (highest) | Environment variables | `PUB_PORT=6000` |

Key env vars: `NODE_ID`, `PUB_PORT`, `SUB_PORT`, `DASHBOARD_PORT`, `NETWORK_MODE`, `BOOTSTRAP_PEERS`, `DHT_ENABLED`, `DHT_BOOTSTRAP`.

See [`docs/CONFIG_ARCHITECTURE.md`](docs/CONFIG_ARCHITECTURE.md) and [`docs/FULL_CONFIG_USAGE.md`](docs/FULL_CONFIG_USAGE.md).

---

## Running Tests

```bash
# All tests (skip integration)
python -m pytest test/ --ignore=test/integration -v

# Specific module
python -m pytest test/token/ -v
python -m pytest test/ -k "rl or fairness or auction" -v
```

---

## Demo

- **Video:** [https://youtu.be/EGv7Z3kXv30](https://youtu.be/EGv7Z3kXv30)
- **Slides:** [Canva Presentation](https://www.canva.com/design/DAG4KrB5-D0/W-mglhEG6lW3rpzn7PW4BA/view)

---

## Documentation Index

### Setup
- [`docs/PIP_INSTALL.md`](docs/PIP_INSTALL.md) — Install with pip
- [`docs/INSTALL.md`](docs/INSTALL.md) — Full interactive installer walkthrough
- [`docs/QUICKSTART.md`](docs/QUICKSTART.md) — 5-minute manual setup
- [`docs/COMMANDS.md`](docs/COMMANDS.md) — All CLI commands
- [`docs/DISTRIBUTED_DEPLOYMENT.md`](docs/DISTRIBUTED_DEPLOYMENT.md) — Deploy on real devices
- [`docs/PATH_SETUP_QUICK_REFERENCE.md`](docs/PATH_SETUP_QUICK_REFERENCE.md) — Fix PATH issues

### Configuration & Network
- [`docs/CONFIG_ARCHITECTURE.md`](docs/CONFIG_ARCHITECTURE.md) — 3-tier config system design
- [`docs/CONFIG_MANAGEMENT_GUIDE.md`](docs/CONFIG_MANAGEMENT_GUIDE.md) — Manage node configs
- [`docs/FULL_CONFIG_USAGE.md`](docs/FULL_CONFIG_USAGE.md) — Complete config reference
- [`docs/USER_GUIDE_NETWORK_MODES.md`](docs/USER_GUIDE_NETWORK_MODES.md) — Private vs Public mode
- [`docs/NETWORK_DESIGN.md`](docs/NETWORK_DESIGN.md) — P2P communication architecture

### Architecture & Design
- [`docs/ARCHITECTURE_RL.md`](docs/ARCHITECTURE_RL.md) — RL system, 25D state vector, PPO training
- [`docs/ARCHITECTURE_TOKEN.md`](docs/ARCHITECTURE_TOKEN.md) — Token economy, taxation, UBI, Gini
- [`docs/CHECKPOINT_RECOVERY_GUIDE.md`](docs/CHECKPOINT_RECOVERY_GUIDE.md) — Fault tolerance and job migration
- [`docs/RL_PREDICTION_DESIGN.md`](docs/RL_PREDICTION_DESIGN.md) — Speculative pre-execution system
- [`docs/PREDICTIVE_CONFIG.md`](docs/PREDICTIVE_CONFIG.md) — Predictive system configuration

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| P2P messaging | ZeroMQ PUB/SUB |
| Cryptography | Ed25519 (PyNaCl) |
| RL framework | PyTorch + Stable-Baselines3 (PPO) |
| Job isolation | Docker |
| Token storage | SQLite (wallet), JSON (ledger) |
| Event loop | winloop (Windows) / uvloop (Linux/macOS) |
| Dashboard | WebSockets (aiohttp) |

---

## Contributors

**Team async_await — built at Hack36**

- [Ayush Jadaun](https://github.com/ayushjadaun)
- [Shreeya Srivastava](https://github.com/shreesriv12)
- [Arnav Raj](https://github.com/arnavraj-7)

---

[![Built at Hack36](https://raw.githubusercontent.com/nihal2908/Hack-36-Readme-Template/main/BUILT-AT-Hack36-9-Secure.png)](https://hack36.com)
