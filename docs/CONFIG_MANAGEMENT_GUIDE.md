# MarlOS Configuration Management Guide

## Overview

MarlOS provides comprehensive configuration management through both the CLI and config files. You can customize every aspect of your node's behavior.

---

## 📝 Configuration Methods

### Method 1: CLI Configuration Menu

**Access:** `marl` → Option 9 (Configuration)

The Configuration Management menu provides:

```
⚙️  Configuration Management

┌───┬────────────────────────────────────────┐
│ 1 │ 📝 View Current Configuration          │
│ 2 │ ✏️  Edit YAML Config File              │
│ 3 │ 📋 Manage Saved Peers (Private Mode)   │
│ 4 │ 🔧 Edit Launch Script                  │
│ 5 │ 📄 Generate Sample Config              │
│ 6 │ 🌐 Network Mode Settings               │
│ 7 │ ♻️  Reset to Defaults                   │
│ 0 │ ← Back to Main Menu                    │
└───┴────────────────────────────────────────┘
```

### Method 2: YAML Config File

**Location:** `~/.marlos/config.yaml`

Edit directly or generate sample:
```bash
marl
# Select: Configuration → Generate Sample Config
```

### Method 3: Environment Variables

Set before starting node:
```bash
export NODE_ID="my-node"
export NETWORK_MODE="private"
export BOOTSTRAP_PEERS="tcp://192.168.1.100:5555"
marl
```

### Method 4: Launch Scripts

Edit your launch script:
```bash
marl
# Select: Configuration → Edit Launch Script
```

---

## 🎯 Quick Tasks

### View Current Settings

```bash
marl
# Select: Configuration → View Current Configuration
```

Shows:
- Environment variables
- YAML config status
- Saved peers count
- Network mode

### Edit YAML Config

```bash
marl
# Select: Configuration → Edit YAML Config File
```

This will:
1. Generate sample if doesn't exist
2. Open in your default editor (Notepad on Windows, nano on Linux)
3. Save automatically

### Manage Peers (Private Mode)

```bash
marl
# Select: Configuration → Manage Saved Peers
```

Options:
- **List peers** - View all saved peers
- **Add peer** - Add new device
- **Remove peer** - Remove device
- **Toggle auto-connect** - Enable/disable auto-connect
- **Export peers** - Backup to file
- **Import peers** - Restore from backup

### Change Network Mode

```bash
marl
# Select: Configuration → Network Mode Settings
```

Or edit launch script:
```bash
# For Private Mode
set NETWORK_MODE=private
set DHT_ENABLED=false

# For Public Mode
set NETWORK_MODE=public
set DHT_ENABLED=true
```

---

## ⚙️ Configuration Options

### Network Configuration

```yaml
network:
  mode: private          # or 'public'
  pub_port: 5555
  sub_port: 5556
  beacon_port: 5557

  # Private Mode
  bootstrap_peers:
    - "tcp://192.168.1.100:5555"
    - "tcp://office-pc.duckdns.org:5555"

  # Public Mode
  dht_enabled: true
  dht_port: 5559
  dht_bootstrap_nodes:
    - ["dht1.marlos.network", 5559]

  discovery_interval: 5
  heartbeat_interval: 3
  max_peers: 50
```

### Token Economy

```yaml
token:
  starting_balance: 100.0      # Initial tokens
  network_fee: 0.05            # 5% transaction fee
  idle_reward: 1.0             # Tokens/hour for being online
  stake_requirement: 10.0      # Min stake for jobs
  success_bonus: 0.20          # 20% bonus for on-time
  late_penalty: 0.10           # 10% penalty for late
  failure_penalty: 1.0         # Lose full stake on failure
```

### Trust System

```yaml
trust:
  starting_trust: 0.5              # New nodes start at 50%
  max_trust: 1.0
  min_trust: 0.0
  quarantine_threshold: 0.2        # <20% trust = quarantine
  rehabilitation_jobs: 10          # Jobs to exit quarantine
  success_reward: 0.02             # +2% per success
  late_reward: 0.01                # +1% if late but complete
  failure_penalty: 0.05            # -5% per failure
  malicious_penalty: 0.50          # -50% for malicious behavior
```

### Job Executor

```yaml
executor:
  max_concurrent_jobs: 3      # Max parallel jobs
  job_timeout: 300            # 5 minutes
  docker_enabled: true        # Allow Docker jobs
  sandbox_enabled: true       # Isolate jobs
```

### Dashboard

```yaml
dashboard:
  host: "0.0.0.0"            # Bind to all interfaces
  port: 3001
  cors_origins:
    - "http://localhost:3000"
    - "http://localhost:5173"
```

### Reinforcement Learning

```yaml
rl:
  model_path: "rl_trainer/models/policy_v1.zip"
  state_dim: 35
  action_dim: 3              # BID, FORWARD, DEFER
  online_learning: false     # Learn from experience
  exploration_rate: 0.1      # 10% random actions
  enabled: true
```

### Predictive System (Experimental)

```yaml
predictive:
  enabled: false                  # Enable speculation
  min_pattern_confidence: 0.75    # 75% confidence required
  min_occurrences: 3              # Pattern seen 3+ times
  max_speculation_ratio: 0.2      # Max 20% resources
  min_expected_value: 3.0         # Min 3 AC profit expected
  cache_ttl: 300                  # Cache 5 minutes
  max_cache_size: 100
```

---

## 📁 File Locations

| File | Location | Purpose |
|------|----------|---------|
| **Config** | `~/.marlos/config.yaml` | Main configuration |
| **Peers** | `~/.marlos/peers.json` | Saved peers (private mode) |
| **Scripts** | `~/.marlos/scripts/` | Launch scripts |
| **Data** | `~/.marlos/data/` | Keys, jobs, etc. |
| **Keys** | `~/.marlos/data/keys/` | Cryptographic keys |

---

## 🔒 Security Best Practices

### 1. Protect Your Keys

```bash
chmod 600 ~/.marlos/data/keys/*
```

### 2. Use Strong Node IDs

```yaml
node_id: secure-node-$(uuidgen)
```

### 3. Limit Peers (Private Mode)

```yaml
network:
  max_peers: 10    # Only allow trusted peers
```

### 4. Enable Sandbox

```yaml
executor:
  sandbox_enabled: true
  docker_enabled: true
```

### 5. Monitor Trust Scores

```yaml
trust:
  quarantine_threshold: 0.3    # Stricter quarantine
```

---

## 🚀 Usage Examples

### Example 1: Personal Network

```yaml
# ~/.marlos/config.yaml
network:
  mode: private
  bootstrap_peers:
    - "tcp://home-laptop.duckdns.org:5555"
    - "tcp://office-pc.tailscale.com:5555"
  max_peers: 5

token:
  starting_balance: 1000.0    # Give yourself more tokens

trust:
  starting_trust: 1.0         # Trust your own devices
```

### Example 2: Public Contributor

```yaml
# ~/.marlos/config.yaml
network:
  mode: public
  dht_enabled: true
  max_peers: 50

executor:
  max_concurrent_jobs: 10     # Handle more jobs

rl:
  online_learning: true       # Learn from network
```

### Example 3: High-Security Node

```yaml
# ~/.marlos/config.yaml
network:
  mode: private
  max_peers: 3

executor:
  docker_enabled: false       # No Docker
  sandbox_enabled: true
  max_concurrent_jobs: 1      # One at a time

trust:
  quarantine_threshold: 0.5   # Very strict
  malicious_penalty: 1.0      # Ban malicious nodes
```

---

## 🛠️ Troubleshooting

### Config Not Loading

**Problem:** Changes not taking effect

**Solution:**
1. Check file location: `~/.marlos/config.yaml`
2. Verify YAML syntax (use online validator)
3. Restart node
4. Check for environment variable override

### Can't Edit Config

**Problem:** Editor not opening

**Solution:**

**Windows:**
```bash
notepad %USERPROFILE%\.marlos\config.yaml
```

**Linux/Mac:**
```bash
nano ~/.marlos/config.yaml
```

### Peers Not Auto-Connecting

**Problem:** Saved peers don't connect on startup

**Solution:**
1. Check `~/.marlos/peers.json`
2. Verify `auto_connect: true`
3. Check network mode is `private`
4. Test peer addresses manually

### Lost Configuration

**Problem:** Config disappeared

**Solution:**
```bash
marl
# Configuration → Generate Sample Config
# Then edit with your settings
```

---

## 📖 Related Documentation

- [Network Modes Guide](USER_GUIDE_NETWORK_MODES.md)
- [Cross-Internet Discovery](CROSS_INTERNET_DISCOVERY.md)
- [Installation Guide](../INSTALL.md)

---

## 💡 Tips

1. **Backup your config:**
   ```bash
   cp ~/.marlos/config.yaml ~/.marlos/config.yaml.backup
   ```

2. **Version control your config:**
   ```bash
   git init ~/.marlos
   cd ~/.marlos
   git add config.yaml peers.json
   git commit -m "My MarlOS config"
   ```

3. **Share config with team:**
   ```bash
   # Export (remove sensitive data first!)
   cp ~/.marlos/config.yaml team-config.yaml
   ```

4. **Test config changes:**
   - Start with one test node
   - Verify behavior
   - Then update all nodes

5. **Use comments in YAML:**
   ```yaml
   # This is my home laptop config
   # Updated: 2025-01-15
   network:
     mode: private  # Using private mode for security
   ```

---

Happy configuring! 🎉
