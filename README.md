<h1 align="center">MarlOS</h1>
<p align="center"><strong>Decentralized, self-organizing compute network powered by Multi-Agent Reinforcement Learning</strong></p>
<p align="center">
  <a href="https://github.com/ayush-jadaun/MarlOS/actions/workflows/ci.yml"><img src="https://github.com/ayush-jadaun/MarlOS/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/Tests-236+-passing-brightgreen?style=flat-square" />
  <img src="https://img.shields.io/badge/License-Apache-2.0-green?style=flat-square" />
</p>

---

MarlOS is a **peer-to-peer distributed computing OS** where every node is autonomous, cryptographically authenticated, and makes its own bidding decisions using reinforcement learning — with no central orchestrator, no Kubernetes, no cloud controller.

When a job enters the network, nodes independently decide whether to **Bid**, **Forward**, or **Defer**. The winner is determined by a decentralized auction. Payment flows automatically via a token economy. Nodes that fail get replaced by backups. Nodes that misbehave get quarantined.

```bash
# Try it in 30 seconds
git clone https://github.com/ayush-jadaun/MarlOS.git && cd MarlOS
pip install -r requirements.txt
python scripts/demo.py
```

---

## Features

### Core System
- **RL-Driven Scheduling** — PPO policy on 25D state vector (BID/FORWARD/DEFER)
- **Decentralized Auctions** — Ed25519-signed bids, deterministic winner selection
- **Token Economy** — MarlCredits with staking, progressive taxation, UBI
- **Trust & Reputation** — 0.0-1.0 scores, automatic quarantine of bad actors
- **Self-Healing** — Backup node takeover, heartbeat monitoring, checkpoint recovery
- **Predictive Pre-Execution** — RL-powered speculation cache for near-zero latency

### New in v1.1
- **REST API** — HTTP endpoints for jobs, peers, wallet, trust, pipelines ([docs](docs/API_GUIDE.md))
- **MCP Server** — Claude and AI agents can submit jobs via Model Context Protocol ([docs](docs/API_GUIDE.md#mcp-server))
- **Job Pipelines (DAGs)** — Chain jobs with dependencies, output flows between steps ([docs](docs/API_GUIDE.md#pipelines))
- **Result Aggregation** — Submit batch jobs, get combined results ([docs](docs/API_GUIDE.md#job-groups))
- **Plugin System** — Drop a .py file in `plugins/`, restart, new runner available ([docs](docs/PLUGINS.md))
- **File Transfer** — P2P chunked transfer with SHA-256 integrity verification
- **Online Learning** — Exploration decay, behavioral cloning from successful experiences
- **D3.js Network Visualization** — Force-directed graph in the dashboard
- **JavaScript SDK** — `npm install marlos-sdk` for Node.js/browser integration ([docs](sdk/js/README.md))
- **Economic Whitepaper** — Formal token model with simulation results ([docs](docs/ECONOMIC_WHITEPAPER.md))

### Proven by Simulation
| Metric | Fairness ON | Fairness OFF |
|---|---|---|
| Gini Coefficient | **0.549** | 0.822 |
| Participation Rate | **100%** | 27% |
| Adversarial Detection | **100%** | — |
| False Positive Rate | **0%** | — |
| Online Learning Win Rate | **+9.2pp** improvement over 500 jobs |

Charts: [`docs/charts/`](docs/charts/)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         MarlOS Node                              │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │
│  │  P2P     │  │  RL      │  │ Bidding  │  │  Executor    │    │
│  │ ZMQ      │  │ PPO      │  │ Auction  │  │  Shell       │    │
│  │ Ed25519  │  │ 25D state│  │ Scorer   │  │  Docker      │    │
│  │ Gossip   │  │ Online   │  │ Router   │  │  Security    │    │
│  │ FileTx   │  │ Learning │  │          │  │  Plugins     │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘    │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │
│  │  Token   │  │  Trust   │  │Pipeline  │  │  Interfaces  │    │
│  │ Economy  │  │ Reputat. │  │ DAG      │  │  Dashboard   │    │
│  │ Wallet   │  │ Quarant. │  │ Aggreg.  │  │  REST API    │    │
│  │ Tax/UBI  │  │ Watchdog │  │ FileTx   │  │  MCP Server  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Job Submitted → P2P Broadcast → All Nodes Receive
                                      │
                          ┌───────────┼───────────┐
                          ▼           ▼           ▼
                        BID        FORWARD      DEFER
                    (RL decides) (RL decides) (RL decides)
                          │
                          ▼
                 Decentralized Auction
                 Ed25519-signed bids
                          │
                          ▼
                 Winner Claims Job → Stakes tokens → Executes
                          │
                    ┌─────┴─────┐
                    ▼           ▼
                Success       Failure
                Pay winner   Slash stake
                +trust       Backup takes over
```

---

## Quick Start

### Demo (one command)

```bash
python scripts/demo.py --nodes 3 --jobs 2
# or
marl demo
```

This starts 3 nodes on localhost, submits jobs, shows the full auction lifecycle, token transfers, and trust updates.

### Run a Node

```bash
# Single node
NODE_ID=my-node python -m agent.main

# With peers
NODE_ID=node-1 BOOTSTRAP_PEERS="tcp://192.168.1.100:5555" python -m agent.main
```

### Submit Jobs

```bash
# Via CLI
marl execute "echo hello"

# Via REST API
curl -X POST http://localhost:3101/api/jobs \
  -H "Content-Type: application/json" \
  -d '{"job_type": "shell", "payload": {"command": "echo hello"}, "payment": 50}'

# Via JavaScript SDK
import { MarlOSClient } from 'marlos-sdk';
const client = new MarlOSClient('http://localhost:3101');
const result = await client.submitAndWait('shell', { command: 'echo hello' });
```

### Submit a Pipeline (DAG)

```bash
curl -X POST http://localhost:3101/api/pipelines \
  -H "Content-Type: application/json" \
  -d '{
    "name": "security-scan",
    "steps": [
      {"id": "scan", "job_type": "port_scan", "payload": {"target": "10.0.0.0/24"}},
      {"id": "analyze", "job_type": "shell", "payload": {"command": "python analyze.py"}, "depends_on": ["scan"]}
    ]
  }'
```

### AI Agent Integration (MCP)

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "marlos": {
      "command": "python",
      "args": ["-m", "agent.mcp.server"],
      "env": {"MARLOS_API_URL": "http://localhost:3101"}
    }
  }
}
```

Then Claude can: *"Submit a port scan of 192.168.1.0/24 to MarlOS"*

---

## Network Modes

### Private Mode (default)
Connect to specific peers. Good for labs, teams, home networks.

```bash
NODE_ID=node-1 BOOTSTRAP_PEERS="tcp://192.168.1.100:5555,tcp://192.168.1.101:5555" python -m agent.main
```

### Public Mode
DHT-based global discovery. Anyone can join.

```bash
NODE_ID=node-1 NETWORK_MODE=public DHT_ENABLED=true \
  DHT_BOOTSTRAP="bootstrap1.example.com:5559" python -m agent.main
```

Sybil resistance: minimum stake (10 AC) and per-subnet peer limits.

---

## Job Types

| Type | Runner | Example |
|---|---|---|
| `shell` | Shell commands | `{"command": "echo hello"}` |
| `docker` | Docker containers | `{"image": "python:3.11", "command": "python -c 'print(1)'"}` |
| `docker_build` | Container builds | `{"dockerfile": ".", "tag": "myapp"}` |
| `port_scan` | Network scanning | `{"target": "192.168.1.0/24"}` |
| `malware_scan` | File analysis | `{"file_path": "/tmp/suspicious.bin"}` |
| `hash_crack` | Hash cracking | `{"hash": "5f4dcc3b...", "algorithm": "md5"}` |
| `threat_intel` | Threat lookups | `{"indicator": "evil.com"}` |
| Custom plugins | Drop in `plugins/` | See [Plugin Guide](docs/PLUGINS.md) |

---

## Running Tests

```bash
# Unit tests (fast, ~30s)
python -m pytest test/ --ignore=test/integration -v

# API tests
python -m pytest test/api/ -v

# Pipeline/DAG tests
python -m pytest test/pipeline/ -v

# Plugin tests
python -m pytest test/plugins/ -v

# Integration tests (3-node real network, ~3 min)
python -m pytest test/integration/ -v

# Benchmark
python scripts/benchmark.py --nodes 3 --jobs 10

# Economic simulation (generates charts)
python scripts/economic_simulation.py

# Adversarial resistance demo
python scripts/adversarial_demo.py
```

**236+ tests passing** across unit, API, pipeline, plugin, economic, adversarial, and integration tests.

---

## Configuration

Three layers (highest priority wins):

| Layer | Source | Example |
|---|---|---|
| 1 (lowest) | Dataclass defaults | `pub_port=5555` |
| 2 | YAML: `~/.marlos/nodes/{NODE_ID}/config.yaml` | Custom per-node |
| 3 (highest) | Environment variables | `PUB_PORT=6000` |

Key env vars: `NODE_ID`, `PUB_PORT`, `SUB_PORT`, `DASHBOARD_PORT`, `NETWORK_MODE`, `BOOTSTRAP_PEERS`, `DHT_ENABLED`, `DHT_BOOTSTRAP`

See [`docs/CONFIG_ARCHITECTURE.md`](docs/CONFIG_ARCHITECTURE.md) for details.

---

## Documentation

### Getting Started
- [`docs/LOCAL_TESTING.md`](docs/LOCAL_TESTING.md) — Run demos, benchmarks, and tests locally
- [`docs/CLI_GUIDE.md`](docs/CLI_GUIDE.md) — All `marl` CLI commands
- [`docs/QUICKSTART.md`](docs/QUICKSTART.md) — 5-minute manual setup

### Deployment
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — Single node, LAN, cloud, worldwide
- [`docs/DISTRIBUTED_DEPLOYMENT.md`](docs/DISTRIBUTED_DEPLOYMENT.md) — Real device deployment

### API & Integration
- [`docs/API_GUIDE.md`](docs/API_GUIDE.md) — REST API, MCP server, JavaScript SDK
- [`docs/PLUGINS.md`](docs/PLUGINS.md) — Writing custom runners
- [`sdk/js/README.md`](sdk/js/README.md) — JavaScript SDK reference

### Architecture
- [`docs/ARCHITECTURE_RL.md`](docs/ARCHITECTURE_RL.md) — 25D state vector, PPO, fairness metrics
- [`docs/ARCHITECTURE_TOKEN.md`](docs/ARCHITECTURE_TOKEN.md) — Token economy, taxation, UBI
- [`docs/ECONOMIC_WHITEPAPER.md`](docs/ECONOMIC_WHITEPAPER.md) — Formal economic model
- [`docs/NETWORK_DESIGN.md`](docs/NETWORK_DESIGN.md) — P2P protocol design
- [`docs/CHECKPOINT_RECOVERY_GUIDE.md`](docs/CHECKPOINT_RECOVERY_GUIDE.md) — Fault tolerance

### Configuration
- [`docs/CONFIG_ARCHITECTURE.md`](docs/CONFIG_ARCHITECTURE.md) — 3-tier config system
- [`docs/FULL_CONFIG_USAGE.md`](docs/FULL_CONFIG_USAGE.md) — All parameters
- [`docs/USER_GUIDE_NETWORK_MODES.md`](docs/USER_GUIDE_NETWORK_MODES.md) — Private vs Public

---

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ (async/await) |
| P2P | ZeroMQ PUB/SUB |
| Crypto | Ed25519 (PyNaCl) |
| RL | PyTorch + Stable-Baselines3 (PPO) |
| API | aiohttp (REST) + MCP SDK |
| Execution | Shell, Docker, custom plugins |
| Storage | SQLite (wallet), JSON (ledger) |
| Dashboard | React + D3.js + WebSockets |
| SDK | JavaScript/TypeScript |

---

## Project Structure

```
agent/                 # Core agent
  p2p/                 # ZMQ networking, Ed25519, file transfer
  rl/                  # PPO policy, online learner, state calc
  bidding/             # Auction, scoring, routing
  executor/            # Job runners (shell, docker, security)
  tokens/              # Wallet, ledger, economy
  trust/               # Reputation, watchdog, quarantine
  pipeline/            # DAGs, aggregator
  plugins/             # Plugin loader
  api/                 # REST API server
  mcp/                 # MCP server for AI agents
  dashboard/           # WebSocket server
  predictive/          # Speculation cache
cli/                   # marl CLI
scripts/               # Demo, benchmark, simulations
plugins/               # Custom runner plugins
sdk/js/                # JavaScript SDK
dashboard/             # React + D3.js frontend
test/                  # 236+ tests
docs/                  # Documentation
```

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines, code style, and how to write a new runner.

---

## Contributors

**Team async_await**

- [Ayush Jadaun](https://github.com/ayush-jadaun)
- [Shreeya Srivastava](https://github.com/shreesriv12)
- [Arnav Raj](https://github.com/arnavraj-7)

---

## License

Apache-2.0
