# Predictive Pre-Execution Configuration Guide

The predictive system uses RL to achieve "negative latency" by pre-executing jobs before they arrive!

## Quick Start

### Enable/Disable the System

**In Code (agent/config.py):**
```python
@dataclass
class PredictiveConfig:
    # Turn the entire system on/off
    enabled: bool = True  # Set to False to disable completely
```

**Via Config File (config.yaml):**
```yaml
predictive:
  enabled: true  # Set to false to disable
```

**At Runtime:**
```python
config = AgentConfig()
config.predictive.enabled = False  # Disable predictive system
agent = MarlOSAgent(config)
```

## Configuration Options

### Basic Settings

```python
@dataclass
class PredictiveConfig:
    # Feature toggle
    enabled: bool = True  # Master switch - turn off to disable all predictive features

    # Pattern detection
    min_pattern_confidence: float = 0.75  # Only predict patterns with 75%+ confidence
    min_occurrences: int = 3  # Pattern must occur at least 3 times

    # Economic constraints
    max_speculation_ratio: float = 0.2  # Max 20% of compute on speculation
    min_expected_value: float = 3.0  # Only speculate if expected profit > 3 AC

    # Rewards/penalties
    correct_prediction_reward: int = 20  # +20 AC for cache hit
    wrong_prediction_penalty: int = 5   # -5 AC for wasted compute

    # Cache settings
    cache_ttl: int = 300  # Cache results for 5 minutes
    max_cache_size: int = 100  # Store max 100 pre-executed results

    # RL Speculation
    rl_speculation_enabled: bool = True  # Use RL for decisions (vs simple heuristic)
    rl_model_path: str = "rl_trainer/models/speculation_policy.zip"
```

### Configuration Examples

#### 1. Disable Predictive System Completely
```python
config.predictive.enabled = False
```

#### 2. Use Heuristic Instead of RL
```python
config.predictive.enabled = True
config.predictive.rl_speculation_enabled = False  # Use simple expected value heuristic
```

#### 3. Conservative Mode (Less Speculation)
```python
config.predictive.enabled = True
config.predictive.min_pattern_confidence = 0.90  # Only very confident predictions
config.predictive.max_speculation_ratio = 0.1   # Max 10% of compute
config.predictive.min_expected_value = 10.0     # Higher profit threshold
```

#### 4. Aggressive Mode (More Speculation)
```python
config.predictive.enabled = True
config.predictive.min_pattern_confidence = 0.60  # Lower confidence threshold
config.predictive.max_speculation_ratio = 0.4   # Up to 40% of compute
config.predictive.min_expected_value = 1.0      # Lower profit threshold
```

#### 5. Training Mode (Collect Data, Don't Speculate)
```python
config.predictive.enabled = True
config.predictive.max_speculation_ratio = 0.0  # No speculation, just pattern learning
```

## YAML Configuration File

Create `config.yaml`:

```yaml
# Basic agent config
node_id: "agent-001"
node_name: "my-agent"

# Predictive system configuration
predictive:
  enabled: true

  # Pattern detection
  min_pattern_confidence: 0.75
  min_occurrences: 3

  # Economics
  max_speculation_ratio: 0.2
  min_expected_value: 3.0
  correct_prediction_reward: 20
  wrong_prediction_penalty: 5

  # Cache
  cache_ttl: 300
  max_cache_size: 100

  # RL
  rl_speculation_enabled: true
  rl_model_path: "rl_trainer/models/speculation_policy.zip"

# Other agent configs...
network:
  pub_port: 5555
  sub_port: 5556

token:
  starting_balance: 100.0
```

Then load:
```python
config = load_config("config.yaml")
agent = MarlOSAgent(config)
```

## Monitoring

### Check if Predictive System is Active

```python
# Get stats
stats = agent.predictive.get_stats()

if stats['enabled']:
    print("Predictive system is ACTIVE")

    # Cache stats
    cache_stats = stats['cache']
    print(f"Cache hit rate: {cache_stats['hit_rate']:.1f}%")
    print(f"Cache size: {cache_stats['cache_size']}/{cache_stats['max_size']}")

    # Speculation stats
    spec_stats = stats['speculation']
    print(f"Speculations: {spec_stats['speculations_attempted']}")
    print(f"Success rate: {spec_stats['success_rate']:.1f}%")

    # RL policy stats
    if 'rl_policy' in stats:
        rl_stats = stats['rl_policy']
        print(f"RL model loaded: {rl_stats['model_loaded']}")
        print(f"Decisions made: {rl_stats['decisions_made']}")
else:
    print("Predictive system is DISABLED")
```

### Dashboard Integration

The dashboard automatically shows predictive stats when enabled:
- Cache hit rate
- Number of speculations
- Success rate
- RL policy status

## Performance Impact

### When Enabled (rl_speculation_enabled=True)
- **Pros:**
  - Instant job completion for predicted jobs (negative latency!)
  - Higher earnings from cache hits (+20 AC each)
  - Learns optimal speculation strategy over time

- **Cons:**
  - Uses up to 20% of compute for speculation (configurable)
  - Risk of wasted compute on wrong predictions (-5 AC)
  - Requires trained RL model

### When Using Heuristic (rl_speculation_enabled=False)
- **Pros:**
  - No need for trained model
  - Simple expected value calculation
  - Still gets cache hits

- **Cons:**
  - Less adaptive than RL
  - May miss profitable speculation opportunities
  - May over-speculate in some scenarios

### When Disabled (enabled=False)
- **Pros:**
  - No computational overhead
  - No risk of wasted speculation

- **Cons:**
  - No negative latency benefits
  - Misses potential +20 AC rewards
  - No pattern learning

## Troubleshooting

### "Model not found" Warning
```
[RL-SPEC] Model not found at rl_trainer/models/speculation_policy.zip, using heuristic fallback
```

**Solution:**
1. Train the model: `python rl_trainer/train_speculation.py`
2. Or disable RL: `config.predictive.rl_speculation_enabled = False`

### High Failed Speculation Rate

If you see many failed speculations (wasted compute):

```python
# Make speculation more conservative
config.predictive.min_pattern_confidence = 0.90
config.predictive.min_expected_value = 5.0
```

### No Cache Hits

If cache hit rate is 0%:

1. Check if patterns are being detected:
```python
stats = agent.predictive.pattern_detector.get_stats()
print(f"Patterns detected: {stats['patterns_detected']}")
```

2. Increase cache TTL:
```python
config.predictive.cache_ttl = 600  # 10 minutes
```

3. Lower pattern confidence threshold:
```python
config.predictive.min_pattern_confidence = 0.60
```

## Best Practices

1. **Start Conservative**: Use default settings first, then tune based on results

2. **Monitor Metrics**: Watch cache hit rate and speculation success rate

3. **Train the Model**: For best results, train the RL model with your workload

4. **Adjust for Workload**:
   - Repetitive jobs → Increase speculation ratio
   - Random jobs → Decrease speculation ratio
   - High-value jobs → Increase min expected value

5. **Test in Stages**:
   - Stage 1: Enable pattern detection only (max_speculation_ratio=0)
   - Stage 2: Enable speculation with heuristic
   - Stage 3: Train and enable RL model

## Summary

| Setting | Default | Recommended Range |
|---------|---------|-------------------|
| `enabled` | True | True/False |
| `rl_speculation_enabled` | True | True/False |
| `min_pattern_confidence` | 0.75 | 0.60 - 0.95 |
| `max_speculation_ratio` | 0.2 | 0.0 - 0.4 |
| `min_expected_value` | 3.0 | 1.0 - 10.0 |
| `cache_ttl` | 300s | 60 - 900s |
| `max_cache_size` | 100 | 50 - 500 |

**Quick Disable:** `config.predictive.enabled = False`

**Quick RL Disable:** `config.predictive.rl_speculation_enabled = False`
