# Full Configuration Usage Guide

## Overview

MarlOS has **TWO configuration systems**:

1. **Simplified Config** - Handled by `agent/config.py` dataclasses (basic settings)
2. **Full Config** - Your comprehensive `agent-config.yml` (ALL features)

## Current State

### ✅ What Works Now:

**Your `agent-config.yml` (584 lines)** includes:
- Agent identity
- P2P network with security
- Token economy (taxation, UBI, fairness engine)
- Trust system with gossip protocol
- Detailed RL configuration
- Bidding & auction system
- 9+ job runner types
- Predictive pre-execution
- Logging, performance tuning, security
- Experimental features
- Benchmarking

**The `agent/config.py`** currently parses:
- Basic network settings (ports, peers)
- Simple token economy
- Basic trust system
- RL model path
- Executor limits
- Dashboard settings

### ⚠️ Current Limitation:

The `config.py` dataclasses don't fully capture all the rich settings in `agent-config.yml`. Many components read settings directly from the YAML dict or use defaults.

---

## How to Use the Full Config

### Method 1: Copy Full Template via CLI

```bash
marl
# Select: 9 (Configuration)
# Select: 6 (Copy Full agent-config.yml Template)
```

This copies your comprehensive `agent-config.yml` to `~/.marlos/config.yaml`

### Method 2: Manual Copy

```bash
cp agent-config.yml ~/.marlos/config.yaml
```

### Method 3: Use Direct Path

```bash
python -m agent.main --config ./agent-config.yml
```

---

## Editing the Full Config

### Via CLI:

```bash
marl
# Select: 9 (Configuration)
# Select: 2 (Edit YAML Config File)
```

This opens the FULL config in your editor (Notepad/VSCode/nano).

### Manual Edit:

```bash
# Windows
notepad %USERPROFILE%\.marlos\config.yaml

# Linux/Mac
nano ~/.marlos/config.yaml
```

---

## Configuration Sections Explained

### 1. Token Economy (Lines 52-153)

**Progressive Taxation:**
```yaml
progressive_tax:
  enabled: true
  brackets:
    - threshold: 100
      rate: 0.00    # 0% for under 100 AC
    - threshold: 500
      rate: 0.05    # 5% for 100-500 AC
    # ... up to 30% above 10,000 AC
```

**Universal Basic Income (UBI):**
```yaml
ubi:
  enabled: true
  amount: 5.0          # AC per hour
  activity_window: 3600
```

**Fairness Engine:**
```yaml
fairness:
  diversity_quotas:
    enabled: true
    max_share: 0.30   # No node wins >30% of jobs

  affirmative_action:
    enabled: true
    thresholds:
      - win_rate: 0.10
        bonus: 0.20   # +20% boost if <10% win rate
```

**Job Complexity Multipliers:**
```yaml
complexity:
  multipliers:
    shell: 1.0
    docker_build: 2.5
    malware_scan: 2.0
    hash_crack: 3.0
    forensics: 3.5
```

### 2. Trust System (Lines 158-192)

**Trust Decay:**
```yaml
decay:
  enabled: true
  rate: 0.01       # -0.01 per day inactive
  min_trust: 0.1
```

**Gossip Protocol:**
```yaml
gossip:
  enabled: true
  interval: 60     # Broadcast reputation every 60s
```

### 3. Reinforcement Learning (Lines 197-263)

**Detailed State Space:**
```yaml
features:
  agent_state:      # [0-4] System resources
    - cpu_usage
    - memory_usage
    - active_jobs

  job_features:     # [5-9] Job characteristics
    - priority
    - deadline_urgency
    - payment_amount

  fairness:         # [18-24] Economic fairness
    - diversity_factor
    - tax_rate
    - gini_coefficient
```

**Online Learning:**
```yaml
online_learning:
  enabled: false         # Disabled by default
  learning_rate: 0.0003
  buffer_size: 10000
```

### 4. Job Execution (Lines 310-378)

**Multiple Runners:**
```yaml
runners:
  shell:
    enabled: true
    timeout: 60

  malware_scan:
    enabled: true
    scanner: "clamav"

  port_scan:
    enabled: true
    scanner: "nmap"

  hash_crack:
    enabled: true
    timeout: 3600      # 1 hour
    tool: "hashcat"

  forensics:
    enabled: true
    tools: ["volatility", "autopsy"]
```

### 5. Predictive System (Lines 386-424)

**Pattern Detection:**
```yaml
pattern_detection:
  min_confidence: 0.75
  min_occurrences: 3
  similarity_threshold: 0.85
```

**Economic Constraints:**
```yaml
economic:
  max_speculation_ratio: 0.20  # Max 20% resources
  min_expected_value: 3.0      # Min 3 AC profit
```

### 6. Logging (Lines 454-478)

**Component-Specific Levels:**
```yaml
components:
  p2p: "INFO"
  rl: "INFO"
  bidding: "INFO"
  fairness: "DEBUG"     # Debug fairness
```

### 7. Security (Lines 505-531)

**Rate Limiting:**
```yaml
rate_limiting:
  enabled: true
  max_requests_per_second: 100
  ban_threshold: 500
  ban_duration: 3600
```

**Blacklisting:**
```yaml
blacklist:
  enabled: true
  auto_blacklist: true
  persistence: true
```

---

## How Components Use Config

### Direct YAML Access:

Many components read the config dict directly:

```python
# In agent code
config_dict = yaml.safe_load(open('config.yaml'))
fairness_config = config_dict.get('token_economy', {}).get('fairness', {})
```

### Through Dataclasses:

Basic settings use `agent/config.py`:

```python
from agent.config import load_config

config = load_config('~/.marlos/config.yaml')
print(config.network.pub_port)  # Works
print(config.token.starting_balance)  # Works
```

### Hybrid Approach:

Most components use a mix of both:
- Core settings from dataclasses
- Advanced features from YAML dict

---

## Customization Examples

### Example 1: High-Performance Node

```yaml
# Edit config for maximum throughput
executor:
  max_concurrent_jobs: 10      # Handle 10 jobs at once

performance:
  max_workers: 8               # 8 thread pool workers
  message_queue_size: 20000    # Large message buffer
```

### Example 2: Fair & Inclusive Network

```yaml
# Maximize fairness
token_economy:
  fairness:
    diversity_quotas:
      max_share: 0.20          # Max 20% of jobs per node
      underdog_boost: 0.75     # 75% boost for struggling nodes

    affirmative_action:
      enabled: true
      thresholds:
        - win_rate: 0.05
          bonus: 0.30          # 30% boost if <5% win rate
```

### Example 3: Security-First

```yaml
# Maximum security
security:
  rate_limiting:
    max_requests_per_second: 50   # Strict rate limit
    ban_threshold: 100

  blacklist:
    auto_blacklist: true

trust:
  quarantine_threshold: 0.3       # Stricter quarantine
  malicious_penalty: 1.0          # Ban malicious nodes
```

### Example 4: Research & Development

```yaml
# Enable experimental features
experimental:
  federated_learning:
    enabled: true

reinforcement_learning:
  online_learning:
    enabled: true           # Learn continuously

predictive:
  enabled: true            # Negative latency!

logging:
  level: "DEBUG"           # Verbose logging
  components:
    fairness: "DEBUG"
    rl: "DEBUG"
```

---

## Editing Best Practices

### 1. Always Backup

```bash
cp ~/.marlos/config.yaml ~/.marlos/config.yaml.backup
```

### 2. Test Changes Incrementally

```bash
# Change one section at a time
# Test with: python -m agent.main --config ~/.marlos/config.yaml
```

### 3. Use Comments

```yaml
# My custom config for office network
# Updated: 2025-01-15
token_economy:
  starting_balance: 500.0  # Higher starting balance for testing
```

### 4. Validate YAML Syntax

Use online validators or:
```bash
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

---

## Accessing Config in Code

### For Component Developers:

If you're adding new features:

```python
# Option 1: Read full YAML
import yaml

with open(config_file) as f:
    config = yaml.safe_load(f)

fairness = config['token_economy']['fairness']
ubi_amount = config['token_economy']['ubi']['amount']

# Option 2: Add to dataclasses
# Edit agent/config.py to add new fields
```

---

## Future Improvements

### Planned:

1. **Full Dataclass Coverage** - Update `config.py` to include ALL settings
2. **Config Validation** - Validate all fields on load
3. **Config Migration** - Auto-update old configs
4. **Live Reload** - Change config without restart
5. **Web UI** - Edit config through dashboard

### You Can Help:

The full `agent-config.yml` is the **source of truth**. If you want all settings in dataclasses, we can update `config.py` to add:
- ProgressiveTaxConfig
- UBIConfig
- FairnessEngineConfig
- GossipConfig
- LoggingConfig
- Etc.

---

## Summary

✅ **Current State:**
- `agent-config.yml` = Full comprehensive config (584 lines)
- `config.py` = Simplified dataclasses (basic settings)
- CLI can copy, edit, and manage full config
- Most features work by reading YAML directly

✅ **What You Can Do:**
1. **Copy full template**: `marl → Configuration → Copy Full Template`
2. **Edit full config**: `marl → Configuration → Edit YAML Config`
3. **Use full config**: `python -m agent.main --config ~/.marlos/config.yaml`
4. **Edit ANY setting** in the YAML - it will be used by components

✅ **All Features Editable:**
- Progressive taxation ✅
- UBI ✅
- Fairness engine ✅
- Trust decay & gossip ✅
- Detailed RL features ✅
- Multiple job runners ✅
- Predictive system ✅
- Logging ✅
- Security ✅
- Everything in agent-config.yml ✅

---

**Your comprehensive `agent-config.yml` is production-ready and fully editable through the CLI!** 🎉
