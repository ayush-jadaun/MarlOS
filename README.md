<h1 align="center">MarlOS: A Multi-Agent Reinforcement Learning Operating System</h1>
<p align="center">
</p>

[![Built at Hack36](https://raw.githubusercontent.com/nihal2908/Hack-36-Readme-Template/main/BUILT-AT-Hack36-9-Secure.png)](https://raw.githubusercontent.com/nihal2908/Hack-36-Readme-Template/main/BUILT-AT-Hack36-9-Secure.png)


## Introduction:
**MarlOS** is a **decentralized, fairness-aware distributed computing operating system** that removes the need for centralized orchestrators like Kubernetes or cloud controllers.  
It operates as a **peer-to-peer (P2P)** network using **ZeroMQ (PUB/SUB)** for communication — where every node is equal, autonomous, and cryptographically authenticated via **Ed25519 signatures**.  

MarlOS introduces a **Fairness-Aware Economic Layer**, using adaptive tokenomics (**MarlCredits**) to ensure equitable participation and prevent resource monopolies.  
Through **multi-agent reinforcement learning**, nodes learn cooperative bidding, resource sharing, and self-healing behaviors — creating a **self-regulating computational swarm** without any central authority.

---

## Demo Video Link:
<a href="#">Coming Soon</a>

---

## Presentation Link:
<a href="https://docs.google.com/presentation/d/10vXArIEf-o9x8L8SwAFzW25JaCazC9Aice8XeP9UAkM/edit?usp=sharing">PPT Link Here</a>

---

## Table of Contents:
1. [Core Architecture & Network](#core-architecture--network)
2. [Reinforcement Learning Engine](#reinforcement-learning-engine)
3. [Economic Fairness Engine](#economic-fairness-engine)
4. [Job Execution & Management](#job-execution--management)
5. [Getting Started](#getting-started)
6. [Technology Stack](#technology-stack)
7. [Contributors](#contributors)

---

## Core Architecture & Network
- **Fully Decentralized:** No master node; peer discovery via ZeroMQ gossip protocol.  
- **Cryptographic Security:** Every P2P message is signed using Ed25519 with timestamps and nonces to prevent replay attacks.  
- **Self-Healing:** Detects node failure and automatically migrates active jobs to backup nodes.  
- **Quorum Consensus:** Maintains consistency and prevents double-claims even under network partitions.

---

## Reinforcement Learning Engine
- **RL-Based Bidding:** Each node runs a PPO agent that decides to **Bid**, **Forward**, or **Defer** tasks based on a 25-dimensional state vector representing local and global conditions.  
- **Speculative Execution:** A secondary predictive agent anticipates likely future jobs and executes them in advance for zero-latency responses.

---

## Economic Fairness Engine
- **Token Economy (MarlCredits):** Nodes stake, earn, and spend credits in decentralized job auctions.  
- **Trust & Reputation System:** Each node maintains a 0.0–1.0 trust score; low-trust peers are quarantined automatically.  
- **Progressive Taxation + UBI:** Wealth redistribution mechanisms promote network balance and inclusivity.  
- **Diversity Quotas & Starvation Prevention:** Dynamic bid modifiers ensure all nodes get fair access to jobs.  
- **Proof-of-Work Verification:** Random audits validate completed jobs to deter Byzantine behavior.

---

## Job Execution & Management
- **Extensible Job Runners:** Supports shell, Docker, and cybersecurity tasks (`malware_scan`, `vuln_scan`, `hash_crack`, `forensics`).  
- **Dynamic Complexity Scoring:** Rewards scale (1×–5×) with task difficulty.  
- **Deterministic Coordinator Election:** Transparent synchronization for distributed job allocation.  
- **Self-Healing Runtime:** When a node fails, jobs migrate seamlessly to a verified backup peer.

---

## Getting Started

### ⚡ Quickest: Install with pip (Recommended)

Install MarlOS globally with pip and use the `marl` command:

```bash
pip install git+https://github.com/ayush-jadaun/MarlOS.git
```

Then run:
```bash
marl  # Interactive menu
```

Or use directly:
```bash
marl start           # Start MarlOS
marl execute "cmd"   # Run a command
marl status          # Check status
marl --help          # See all commands
```

**See complete guide:** [docs/PIP_INSTALL.md](docs/PIP_INSTALL.md) 📦

---

### 🚀 One-Line Interactive Installation (Full Setup)

For the easiest setup experience, use our interactive installer that guides you through everything:

```bash
curl -sSL https://raw.githubusercontent.com/ayush-jadaun/MarlOS/main/scripts/install-marlos.sh | bash
```

Or download and run locally:
```bash
wget https://raw.githubusercontent.com/ayush-jadaun/MarlOS/main/scripts/install-marlos.sh
chmod +x install-marlos.sh
./install-marlos.sh
```

**The installer will:**
- ✅ Detect your OS and install dependencies
- ✅ Clone the repository
- ✅ Ask about deployment mode (Docker vs Real Device)
- ✅ Configure network settings interactively
- ✅ Set up firewall rules automatically
- ✅ Create launch scripts for your node
- ✅ Optionally set up systemd service (Linux)
- ✅ Start your node automatically

---

### Quick Start with Docker

For local testing with containerized nodes:
```bash
docker-compose up -d
```
This starts 3 agent nodes and an MQTT broker for demonstration.

---

### Distributed Deployment on Real Devices

To deploy MarlOS across actual laptops, desktops, or servers for true distributed computing:

**🎯 Interactive Installer (Recommended):** [Run installer](#-one-line-interactive-installation-full-setup)
**⚡ 5-Minute Manual Setup:** [docs/QUICKSTART.md](docs/QUICKSTART.md)
**📖 Complete Guide:** [docs/DISTRIBUTED_DEPLOYMENT.md](docs/DISTRIBUTED_DEPLOYMENT.md)

**Quick Manual Overview:**
```bash
# On each device:
export NODE_ID="laptop-1"
export BOOTSTRAP_PEERS="tcp://192.168.1.101:5555,tcp://192.168.1.102:5555"
./start-node.sh  # or start-node.bat on Windows
```

The system automatically discovers peers, elects coordinators, and distributes jobs using reinforcement learning and cryptographic security.

---

## Technology Stack:
1. **Python** – Core system logic and RL agent implementation  
2. **ZeroMQ** – Decentralized PUB/SUB messaging network  
3. **PyTorch / Stable Baselines3** – Reinforcement learning framework  
4. **Ed25519** – Digital signature and cryptographic authentication  
5. **Docker** – Job containerization and isolated execution  
6. **SQLite / JSON-Ledger** – Local token economy and trust tracking

---

## Contributors:

**Team Name:** async_await

- [Ayush Jadaun](https://github.com/ayushjadaun)
- [Shreeya Srivastava](https://github.com/shreesriv12)
- [Arnav Raj](https://github.com/arnavraj-7)

---

### Made at:
[![Built at Hack36](https://raw.githubusercontent.com/nihal2908/Hack-36-Readme-Template/main/BUILT-AT-Hack36-9-Secure.png)](https://raw.githubusercontent.com/nihal2908/Hack-36-Readme-Template/main/BUILT-AT-Hack36-9-Secure.png)

---

## Documentation

### Setup & Installation
- **[pip Installation Guide](docs/PIP_INSTALL.md)** - Install with pip and use `marl` command
- **[Interactive Installer Guide](docs/INSTALL.md)** - Full system setup walkthrough
- **[Quick Start Guide](docs/QUICKSTART.md)** - 5-minute manual setup
- **[Commands Reference](docs/COMMANDS.md)** - Complete command guide
- **[Distributed Deployment](docs/DISTRIBUTED_DEPLOYMENT.md)** - Deploy on real devices
- **[Deployment Verification](docs/DEPLOYMENT_VERIFICATION.md)** - Testing your setup
- **[Share Guide](docs/SHARE.md)** - Share with your team

### Architecture & Design
- **[Network Design](docs/NETWORK_DESIGN.md)** - P2P communication architecture
- **[RL Architecture](docs/ARCHITECTURE_RL.md)** - Reinforcement learning details
- **[Token Economy](docs/ARCHITECTURE_TOKEN.md)** - Economic system design
- **[Checkpoint Recovery](docs/CHECKPOINT_RECOVERY_GUIDE.md)** - Fault tolerance mechanisms
- **[RL Prediction](docs/RL_PREDICTION_DESIGN.md)** - Predictive pre-execution system