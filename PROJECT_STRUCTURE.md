# MarlOS Project Structure

Clean, organized directory structure for easy navigation and contribution.

## Root Directory

```
MarlOS/
├── README.md                      # Main project documentation
├── LICENSE                        # MIT License
├── setup.py                       # pip installation configuration
├── MANIFEST.in                    # Package data specification
├── PROJECT_STRUCTURE.md          # This file
├── requirements.txt               # Python dependencies
├── requirements-docker.txt        # Docker-specific dependencies
├── docker-compose.yml             # Docker orchestration
├── agent-config.yml               # Agent configuration template
│
├── agent/                         # Core agent implementation
├── cli/                           # Command-line interface
├── rl_trainer/                    # Reinforcement learning models
├── docs/                          # All documentation
├── scripts/                       # Installation and utility scripts
├── config/                        # Configuration files (MQTT, etc.)
├── docker/                        # Dockerfiles
├── hardware/                      # Hardware control (Arduino/ESP32)
├── examples/                      # Example scripts
├── test/                          # Test suites
├── data/                          # Runtime data (generated)
└── venv/                          # Virtual environment (local)
```

---

## 📁 Core Directories

### `agent/` - Core Agent Implementation
```
agent/
├── __init__.py
├── main.py                    # Main agent entry point
├── config.py                  # Configuration classes
│
├── p2p/                       # Peer-to-peer networking
│   ├── node.py                # P2P node implementation
│   ├── protocol.py            # Message protocol
│   ├── coordinator.py         # Coordinator election
│   ├── discovery.py           # Peer discovery
│   └── security.py            # Security & encryption
│
├── bidding/                   # Job auction system
│   ├── auction.py             # Auction mechanism
│   ├── scorer.py              # Bid scoring
│   └── router.py              # Job routing
│
├── executor/                  # Job execution engines
│   ├── engine.py              # Execution coordinator
│   ├── shell.py               # Shell command runner
│   ├── docker.py              # Docker job runner
│   ├── security.py            # Security tools (malware, port scan)
│   ├── hardware.py            # Hardware control (MQTT)
│   └── recovery.py            # Checkpoint & recovery
│
├── tokens/                    # Token economy
│   ├── wallet.py              # Wallet implementation
│   └── economy.py             # Economic rules
│
├── trust/                     # Trust & reputation
│   ├── reputation.py          # Reputation tracking
│   └── watchdog.py            # Malicious behavior detection
│
├── rl/                        # Reinforcement learning
│   ├── policy.py              # RL policy (PPO)
│   ├── online_learner.py      # Online learning
│   └── state.py               # State representation
│
├── predictive/                # Predictive pre-execution
│   ├── integration.py         # Prediction system
│   └── speculation.py         # Speculative execution
│
├── dashboard/                 # Web dashboard
│   └── server.py              # WebSocket server
│
├── crypto/                    # Cryptography
│   └── signing.py             # Ed25519 signatures
│
└── schema/                    # Data schemas
    └── schema.py              # Job and message schemas
```

### `cli/` - Command-Line Interface
```
cli/
├── __init__.py
├── main.py                    # Interactive CLI (marl command)
└── marlOS.py                  # Direct commands
```

### `rl_trainer/` - RL Model Training
```
rl_trainer/
├── train_policy.py            # Training script
├── models/                    # Trained models
│   └── policy_v1.zip
└── logs/                      # Training logs
```

---

## 📖 Documentation (`docs/`)

### Setup & Installation
- **[PIP_INSTALL.md](docs/PIP_INSTALL.md)** - pip installation guide
- **[INSTALL.md](docs/INSTALL.md)** - Interactive installer walkthrough
- **[QUICKSTART.md](docs/QUICKSTART.md)** - 5-minute manual setup
- **[COMMANDS.md](docs/COMMANDS.md)** - CLI command reference

### Deployment
- **[DISTRIBUTED_DEPLOYMENT.md](docs/DISTRIBUTED_DEPLOYMENT.md)** - Deploy on real devices
- **[DEPLOYMENT_VERIFICATION.md](docs/DEPLOYMENT_VERIFICATION.md)** - Testing guide
- **[SHARE.md](docs/SHARE.md)** - Share with your team

### Architecture
- **[NETWORK_DESIGN.md](docs/NETWORK_DESIGN.md)** - P2P communication
- **[ARCHITECTURE_RL.md](docs/ARCHITECTURE_RL.md)** - RL system design
- **[ARCHITECTURE_TOKEN.md](docs/ARCHITECTURE_TOKEN.md)** - Token economy
- **[RL_PREDICTION_DESIGN.md](docs/RL_PREDICTION_DESIGN.md)** - Predictive execution
- **[CHECKPOINT_RECOVERY_GUIDE.md](docs/CHECKPOINT_RECOVERY_GUIDE.md)** - Fault tolerance

### Reference
- **[PIP_INSTALLATION_SUMMARY.md](docs/PIP_INSTALLATION_SUMMARY.md)** - pip setup summary

---

## 🔧 Scripts (`scripts/`)

### Installation & Setup
- **`install-marlos.sh`** - Interactive installer (Linux/Mac/WSL)
- **`start-node.sh`** - Launch script template (Linux/Mac)
- **`start-node.bat`** - Launch script template (Windows)

### Testing
- **`test_deployment.sh`** - Automated deployment test suite

---

## 🐳 Docker (`docker/`)

```
docker/
├── Dockerfile.agent           # Standard agent image
└── Dockerfile.agent.optimized # Optimized image (CPU-only PyTorch)
```

---

## ⚙️ Configuration (`config/`)

```
config/
└── mosquitto.conf             # MQTT broker configuration
```

---

## 🔌 Hardware (`hardware/`)

```
hardware/
└── arduino/                   # Arduino sketches for LED control
```

---

## 📊 Examples (`examples/`)

Example usage scripts and job templates.

---

## 🧪 Tests (`test/`)

Test suites and benchmarks.

---

## 📦 Generated/Local (Not in Git)

These directories are created during runtime and excluded from version control:

```
data/                          # Runtime data
├── keys/                      # Cryptographic keys
├── <node-id>/                 # Node-specific data
│   ├── wallet.json
│   ├── reputation.json
│   └── checkpoints/
└── agent.log

venv/                          # Python virtual environment

models/                        # Downloaded/trained models

logs/                          # Application logs
```

---

## 🗂️ Key Files

### Root Level

| File | Purpose |
|------|---------|
| `README.md` | Main project documentation, quick start |
| `setup.py` | pip package configuration |
| `LICENSE` | MIT License |
| `MANIFEST.in` | Package data inclusion rules |
| `requirements.txt` | Python dependencies |
| `docker-compose.yml` | Multi-agent Docker setup |
| `agent-config.yml` | Agent configuration template |

### Entry Points

| File | Command | Purpose |
|------|---------|---------|
| `cli/main.py` | `marl` | Interactive CLI |
| `agent/main.py` | `python -m agent.main` | Start agent |
| `rl_trainer/train_policy.py` | `python rl_trainer/train_policy.py` | Train RL model |

---

## 🚀 Quick Navigation

### Want to...

**Install MarlOS?**
- Start with [README.md](README.md)
- pip install: [docs/PIP_INSTALL.md](docs/PIP_INSTALL.md)
- Full setup: [docs/INSTALL.md](docs/INSTALL.md)

**Deploy on real devices?**
- Quick: [docs/QUICKSTART.md](docs/QUICKSTART.md)
- Complete: [docs/DISTRIBUTED_DEPLOYMENT.md](docs/DISTRIBUTED_DEPLOYMENT.md)

**Understand the architecture?**
- Network: [docs/NETWORK_DESIGN.md](docs/NETWORK_DESIGN.md)
- RL: [docs/ARCHITECTURE_RL.md](docs/ARCHITECTURE_RL.md)
- Economy: [docs/ARCHITECTURE_TOKEN.md](docs/ARCHITECTURE_TOKEN.md)

**Use the CLI?**
- Commands: [docs/COMMANDS.md](docs/COMMANDS.md)
- Interactive: Just run `marl`

**Modify the code?**
- Agent core: `agent/main.py`
- P2P networking: `agent/p2p/`
- Job execution: `agent/executor/`
- RL policy: `agent/rl/`
- CLI interface: `cli/main.py`

**Add a new job type?**
- Create runner in `agent/executor/`
- Register in `agent/main.py` → `_register_job_runners()`

**Train new RL model?**
- Script: `rl_trainer/train_policy.py`
- Models: `rl_trainer/models/`

**Share with team?**
- Guide: [docs/SHARE.md](docs/SHARE.md)
- Installer: `scripts/install-marlos.sh`

---

## 📝 File Naming Conventions

### Documentation
- `UPPERCASE.md` - Major documentation files
- Descriptive names: `DISTRIBUTED_DEPLOYMENT.md`, `QUICKSTART.md`

### Scripts
- `kebab-case.sh` - Shell scripts: `install-marlos.sh`
- `.bat` extension for Windows

### Code
- `snake_case.py` - Python files: `online_learner.py`
- `camelCase` - Classes: `MarlOSAgent`, `P2PNode`

### Configuration
- `kebab-case.yml` - Config files: `agent-config.yml`

---

## 🔍 Finding Things

### By Feature

| Feature | Location |
|---------|----------|
| P2P Networking | `agent/p2p/` |
| Job Execution | `agent/executor/` |
| RL Policy | `agent/rl/` |
| Token Economy | `agent/tokens/` |
| Trust System | `agent/trust/` |
| CLI Interface | `cli/` |
| Web Dashboard | `agent/dashboard/` |
| Predictive System | `agent/predictive/` |

### By Action

| Action | File |
|--------|------|
| Start agent | `agent/main.py` |
| Run CLI | `cli/main.py` |
| Submit job | `cli/marlOS.py` execute |
| Train model | `rl_trainer/train_policy.py` |
| Install system | `scripts/install-marlos.sh` |

---

## 🚫 Excluded from Git

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/

# Virtual environments
venv/
env/

# Runtime data
data/
logs/
*.log

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Node modules (dashboard)
dashboard/node_modules/
```

---

## 📦 pip Package Structure

When installed via `pip install marlos`:

```
site-packages/
└── marlos/
    ├── agent/
    ├── cli/
    ├── rl_trainer/
    ├── docs/        (included)
    ├── scripts/     (included)
    └── ...
```

Entry point creates global command:
```bash
marl  # → cli/main.py:cli()
```

---

## 🤝 Contributing

When adding new features:

1. **Code** → `agent/` or relevant subdirectory
2. **Tests** → `test/`
3. **Docs** → `docs/` with descriptive name
4. **Scripts** → `scripts/` if needed
5. **Update** this file if structure changes

---

## 📊 Directory Sizes (Approximate)

```
agent/          ~500 KB  (source code)
cli/            ~100 KB  (CLI code)
docs/           ~500 KB  (documentation)
rl_trainer/     ~50 MB   (trained models)
dashboard/      ~200 MB  (node_modules)
venv/           ~500 MB  (Python packages)
data/           varies   (runtime data)
```

---

## ✨ Clean Root Directory

Before reorganization:
```
MarlOS/
├── README.md
├── INSTALL.md
├── QUICKSTART.md
├── DEPLOYMENT_VERIFICATION.md
├── SHARE.md
├── PIP_INSTALL.md
├── COMMANDS.md
├── PIP_INSTALLATION_SUMMARY.md
├── install-marlos.sh
├── start-node.sh
├── start-node.bat
├── test_deployment.sh
└── ... (cluttered!)
```

After reorganization:
```
MarlOS/
├── README.md                 # Main docs only
├── LICENSE
├── setup.py
├── PROJECT_STRUCTURE.md
├── requirements.txt
├── docker-compose.yml
├── docs/                     # All docs organized
├── scripts/                  # All scripts organized
└── ... (clean!)
```

---

**Much cleaner and more professional!** 🎉

All documentation is now in `docs/`, all scripts in `scripts/`, and root directory contains only essential files.
