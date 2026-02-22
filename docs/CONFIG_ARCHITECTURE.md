# MarlOS Configuration Architecture

## Overview

MarlOS uses a **two-tier configuration system** following production-grade practices:

1. **System Config** - Global settings shared across all nodes
2. **Node Config** - Per-node instance-specific settings

---

## Configuration Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    CONFIGURATION LAYERS                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Layer 1: System Config (agent-config.yml)                  │
│  ├─ Token economy rules (taxation, UBI, fairness)          │
│  ├─ Trust system parameters                                 │
│  ├─ RL hyperparameters                                      │
│  ├─ Bidding & auction rules                                 │
│  ├─ Security settings                                       │
│  └─ Logging, performance, etc.                              │
│  📍 Location: ./agent-config.yml (repository)                │
│  🔒 Scope: ALL nodes in the network                         │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Layer 2: Node Config (per-node YAML)                       │
│  ├─ Node ID (auto-generated UUID)                           │
│  ├─ Node name                                               │
│  ├─ Network mode (private/public)                           │
│  ├─ Bootstrap peers (specific to this node)                 │
│  ├─ Ports (if custom)                                       │
│  ├─ Data directory                                          │
│  └─ Overrides for system config                             │
│  📍 Location: ~/.marlos/nodes/{node-id}/config.yaml         │
│  🔒 Scope: THIS node only                                   │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Layer 3: Environment Variables (highest priority)          │
│  ├─ NODE_ID                                                 │
│  ├─ BOOTSTRAP_PEERS                                         │
│  ├─ NETWORK_MODE                                            │
│  └─ Port overrides                                          │
│  📍 Location: Shell environment / launch script             │
│  🔒 Scope: Runtime override                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘

Configuration Precedence (highest to lowest):
Environment Variables > Node Config > System Config > Defaults
```

---

## 1. System Config (agent-config.yml)

**Purpose:** Define network-wide rules and defaults

**Location:** `./agent-config.yml` (in repository)

**Contains:**

- Token economy (taxation, UBI, fairness engine)
- Trust & reputation system
- RL algorithm parameters
- Bidding & auction rules
- Job execution settings (runners, timeouts)
- Security & cryptography
- Logging & monitoring
- Performance tuning
- Experimental features

**Who Edits:**

- Network administrators
- Core developers
- Governance process (in production)

**Example:**

```yaml
# agent-config.yml - System-wide config
token_economy:
  progressive_tax:
    brackets:
      - threshold: 100
        rate: 0.00
      - threshold: 500
        rate: 0.05

trust:
  starting_trust: 0.5
  quarantine_threshold: 0.2

reinforcement_learning:
  model_path: "rl_trainer/models/policy_v1.zip"
  state_dim: 25
```

---

## 2. Node Config (per-node)

**Purpose:** Instance-specific settings for each running node

**Location:** `~/.marlos/nodes/{node-id}/config.yaml`

**Auto-Generated:** When you create a node via CLI

**Contains:**

- Node identity (ID, name)
- Network settings (mode, peers, ports)
- Local paths (data dir, log dir)
- System config overrides (optional)

**Who Edits:**

- Node operators
- Individual users
- Automated deployment scripts

**Example:**

```yaml
# ~/.marlos/nodes/agent-abc123/config.yaml - Node-specific

# Node Identity (AUTO-GENERATED)
node:
  id: agent-abc123
  name: "My Home Laptop"
  created_at: "2025-01-15T10:30:00Z"

# Network Configuration (THIS NODE)
network:
  mode: private
  bootstrap_peers:
    - "tcp://office-pc.duckdns.org:5555"
    - "tcp://192.168.1.100:5555"
  pub_port: 5555
  sub_port: 5556

# Local Paths
paths:
  data_dir: "~/.marlos/nodes/agent-abc123/data"
  log_dir: "~/.marlos/nodes/agent-abc123/logs"

# System Config Overrides (OPTIONAL)
overrides:
  token_economy:
    starting_balance: 500.0  # Override default 100.0

  executor:
    max_concurrent_jobs: 10  # Override default 3
```

---

## Workflow: Creating a New Node

### Step 1: User Creates Node via CLI

```bash
marl
# Select: Start MarlOS → Native/Real Device
# Choose Network Mode: Private
# Node ID: (auto-generated: agent-f7a3b9c2)
# Bootstrap Peers: tcp://192.168.1.100:5555
```

### Step 2: System Auto-Generates Node Config

```
Creating node: agent-f7a3b9c2
├─ Generating node ID: agent-f7a3b9c2
├─ Creating directory: ~/.marlos/nodes/agent-f7a3b9c2/
├─ Writing node config: ~/.marlos/nodes/agent-f7a3b9c2/config.yaml
├─ Creating data dir: ~/.marlos/nodes/agent-f7a3b9c2/data/
├─ Creating log dir: ~/.marlos/nodes/agent-f7a3b9c2/logs/
└─ Generating launch script: ~/.marlos/nodes/agent-f7a3b9c2/start.sh
```

### Step 3: Node Config File Created

```yaml
# Auto-generated file: ~/.marlos/nodes/agent-f7a3b9c2/config.yaml

# DO NOT EDIT: Auto-generated section
node:
  id: agent-f7a3b9c2
  name: "agent-f7a3b9c2"
  created_at: "2025-01-15T10:30:45Z"
  system_config: "./agent-config.yml"

# EDITABLE: Network configuration
network:
  mode: private
  bootstrap_peers:
    - "tcp://192.168.1.100:5555"
  pub_port: 5555
  sub_port: 5556
  dht_enabled: false

# EDITABLE: Local paths
paths:
  data_dir: "~/.marlos/nodes/agent-f7a3b9c2/data"
  log_dir: "~/.marlos/nodes/agent-f7a3b9c2/logs"
  keys_dir: "~/.marlos/nodes/agent-f7a3b9c2/data/keys"

# EDITABLE: Dashboard (local override)
dashboard:
  port: 3001

# OPTIONAL: System config overrides
# Uncomment to override system-wide settings
# overrides:
#   token_economy:
#     starting_balance: 500.0
#   executor:
#     max_concurrent_jobs: 5
```

---

## Config Loading Process

```python
def load_config(node_id: str = None):
    """
    Load configuration with proper precedence

    Precedence (highest to lowest):
    1. Environment variables
    2. Node config (~/.marlos/nodes/{node-id}/config.yaml)
    3. System config (./agent-config.yml)
    4. Hardcoded defaults
    """

    # Load system config (defaults)
    system_config = yaml.safe_load(open('agent-config.yml'))

    # Load node config (overrides)
    if node_id:
        node_config_path = Path.home() / ".marlos" / "nodes" / node_id / "config.yaml"
        if node_config_path.exists():
            node_config = yaml.safe_load(open(node_config_path))

            # Merge configs (node config overrides system)
            config = deep_merge(system_config, node_config)
        else:
            config = system_config
    else:
        config = system_config

    # Apply environment variable overrides
    config = apply_env_overrides(config)

    return config
```

---

## CLI Configuration Management

### View System Config

```bash
marl → Configuration → View System Config
```

Shows: agent-config.yml (network-wide settings)

### View Node Config

```bash
marl → Configuration → View Node Config
# Select node: agent-abc123
```

Shows: ~/.marlos/nodes/agent-abc123/config.yaml

### Edit System Config

```bash
marl → Configuration → Edit System Config
```

Opens: agent-config.yml in editor
Affects: ALL nodes

### Edit Node Config

```bash
marl → Configuration → Edit Node Config
# Select node: agent-abc123
```

Opens: ~/.marlos/nodes/agent-abc123/config.yaml
Affects: ONLY that node

### List All Nodes

```bash
marl → Configuration → List Nodes
```

Output:

```
Registered Nodes:

1. agent-abc123 (My Home Laptop)
   Created: 2025-01-15
   Status: Offline
   Config: ~/.marlos/nodes/agent-abc123/config.yaml

2. agent-xyz789 (Office PC)
   Created: 2025-01-14
   Status: Running
   Config: ~/.marlos/nodes/agent-xyz789/config.yaml
```

---

## Use Cases

### Use Case 1: Personal Multi-Device Setup

**System Config:** Leave defaults
**Node Configs:**

```yaml
# Home Laptop (agent-abc123)
network:
  mode: private
  bootstrap_peers: ["tcp://office-pc.duckdns.org:5555"]
dashboard:
  port: 3001

# Office PC (agent-xyz789)
network:
  mode: private
  bootstrap_peers: []  # No bootstrap, this is the seed node
dashboard:
  port: 3001
```

### Use Case 2: Production Deployment

**System Config:** Tuned for production

```yaml
# agent-config.yml
token_economy:
  fairness:
    diversity_quotas:
      enabled: true
      max_share: 0.20
logging:
  level: "INFO"
  rotation:
    enabled: true
```

**Node Configs:** Auto-deployed

```yaml
# Node 1 (datacenter-1)
network:
  mode: public
  dht_enabled: true
overrides:
  executor:
    max_concurrent_jobs: 20

# Node 2 (datacenter-2)
network:
  mode: public
  dht_enabled: true
overrides:
  executor:
    max_concurrent_jobs: 20
```

### Use Case 3: Testing Different Strategies

```yaml
# Test Node A (conservative)
overrides:
  reinforcement_learning:
    exploration_rate: 0.05  # Low exploration

# Test Node B (aggressive)
overrides:
  reinforcement_learning:
    exploration_rate: 0.30  # High exploration
```

---

## Benefits

✅ **Separation of Concerns**

- System config = network rules
- Node config = instance settings

✅ **Easy Multi-Node Management**

- Each node has its own config
- No conflicts between nodes

✅ **Flexible Overrides**

- Keep system defaults
- Override per node as needed

✅ **Production Ready**

- Clear configuration hierarchy
- Easy to deploy and manage
- Supports automation

✅ **Version Control Friendly**

- System config in git
- Node configs local (not tracked)

---

## File Structure

```
MarlOS/
├── agent-config.yml                    # System config (in repo)
├── agent/
│   └── config.py                       # Config loader
└── ~/.marlos/                          # User directory
    ├── nodes/
    │   ├── agent-abc123/               # Node 1
    │   │   ├── config.yaml             # Node config
    │   │   ├── data/                   # Node data
    │   │   │   ├── keys/               # Crypto keys
    │   │   │   ├── wallet.json         # Wallet
    │   │   │   └── reputation.json     # Reputation
    │   │   ├── logs/                   # Node logs
    │   │   └── start.sh                # Launch script
    │   │
    │   └── agent-xyz789/               # Node 2
    │       ├── config.yaml
    │       ├── data/
    │       ├── logs/
    │       └── start.sh
    │
    ├── peers.json                      # Global saved peers
    └── system-config-override.yaml     # Optional: override system config
```

---

## Migration Path

For existing installations:

1. **Backup existing config:**

   ```bash
   cp ~/.marlos/config.yaml ~/.marlos/config.yaml.backup
   ```

2. **Let CLI detect and migrate:**

   ```bash
   marl
   # System detects old config format
   # Offers to migrate to new structure
   ```

3. **Automatic migration:**
   - Extracts node-specific settings
   - Creates node directory
   - Preserves all settings

---

## Summary

| Aspect | System Config | Node Config |
|--------|--------------|-------------|
| **File** | `agent-config.yml` | `~/.marlos/nodes/{id}/config.yaml` |
| **Scope** | All nodes | Single node |
| **Contains** | Network rules | Instance settings |
| **Who Edits** | Admin/Developers | Node operators |
| **Version Control** | Yes (git) | No (local) |
| **Auto-Generated** | No | Yes |
| **Overridable** | By node config | By env vars |

**This is production-grade configuration management!** 🎯
