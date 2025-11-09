# RL-Based Prediction Design

## Current System vs RL System

### Current (Statistical)
```
Pattern: Job seen 3 times → 95% confidence
Limitation: Can't learn complex patterns like:
  - "Job X comes after Y, but only on Mondays"
  - "User submits 3 docker builds, then 1 test, pattern repeats"
  - "High network load → user switches to lighter jobs"
```

### With RL (Learned)
```
RL Agent learns:
  State: [time, day, recent_jobs, network, user_behavior, ...]
  Action: Predict next job type (one-hot: [shell, docker, test, ...])
  Reward: +20 if predicted correctly, -5 if wrong
```

---

## Implementation Plan

### Option 1: RL for Job Type Prediction (Supervised Learning Style)

**Train a classifier:**
```python
# State: Context features
state = [
    hour_of_day,           # 0-23
    day_of_week,          # 0-6
    jobs_in_last_hour,    # count
    last_job_type_1,      # one-hot
    last_job_type_2,
    last_job_type_3,
    time_since_last_job,  # seconds
    user_id,              # one-hot
    network_load,         # 0-1
    queue_length          # count
]

# Action: Predicted next job type
action_space = [shell, docker, docker_build, malware_scan, ...]

# Reward:
if prediction == actual_job:
    reward = +20
else:
    reward = -5
```

**Algorithm: PPO or DQN**
- Train on job submission history
- Update online as new jobs arrive

### Option 2: RL for Speculation Decision (Current Best Fit)

**Keep pattern detector as-is, use RL to decide when to speculate:**

```python
class SpeculationPolicy:
    """RL policy that decides: Should I speculate on this prediction?"""

    def __init__(self):
        self.model = PPO.load("models/speculation_policy.zip")

    def should_speculate(self, prediction: dict, context: dict) -> bool:
        state = [
            prediction['confidence'],      # From pattern detector
            context['cpu_idle'],          # Resource availability
            context['cache_size'],        # How full is cache
            context['recent_hit_rate'],   # Are predictions working?
            context['balance'],           # Token balance
            prediction['expected_in'],    # Time until job arrives
            context['active_jobs'],       # Current load
        ]

        # RL decides: SPECULATE (1) or WAIT (0)
        action, _ = self.model.predict(state)

        return action == 1
```

**This is EASIER because:**
- Pattern detector stays simple (works now)
- RL only optimizes speculation strategy
- Smaller state space
- Can train faster

---

## Quick Implementation (30 minutes)

I can add RL speculation policy:

### File 1: `agent/predictive/rl_speculation.py`

```python
import numpy as np

class RLSpeculationPolicy:
    """RL policy for speculation decisions"""

    def __init__(self, rl_enabled: bool = False):
        self.enabled = rl_enabled
        self.state_history = []

        if rl_enabled:
            try:
                from stable_baselines3 import PPO
                self.model = PPO.load("rl_trainer/models/speculation_policy.zip")
            except:
                print("[RL-PREDICT] Model not found, using heuristic")
                self.model = None
        else:
            self.model = None

    def decide(self, prediction: dict, agent_context: dict) -> tuple[bool, float]:
        """
        Decide whether to speculate

        Returns:
            (should_speculate, confidence)
        """
        state = self._calculate_state(prediction, agent_context)

        if self.model:
            # RL decision
            action, _ = self.model.predict(state, deterministic=True)
            should_speculate = action == 1
            confidence = 0.9  # From model
        else:
            # Fallback heuristic (current logic)
            expected_value = self._calculate_expected_value(prediction)
            should_speculate = expected_value >= 3.0
            confidence = prediction['confidence']

        return should_speculate, confidence

    def _calculate_state(self, prediction: dict, context: dict) -> np.ndarray:
        """7D state for speculation decision"""
        return np.array([
            prediction.get('confidence', 0.5),
            context.get('cpu_idle_pct', 0.5),
            context.get('cache_utilization', 0.0),
            context.get('recent_hit_rate', 0.0),
            context.get('balance', 100) / 1000.0,  # Normalize
            min(prediction.get('expected_in', 60), 300) / 300.0,  # Normalize
            context.get('active_jobs', 0) / 10.0  # Normalize
        ], dtype=np.float32)

    def record_outcome(self, state: np.ndarray, action: int, reward: float):
        """Record for online learning"""
        self.state_history.append({
            'state': state,
            'action': action,
            'reward': reward
        })
```

### File 2: `rl_trainer/train_speculation.py`

```python
"""
Train RL policy for speculation decisions
"""

import gym
import numpy as np
from stable_baselines3 import PPO

class SpeculationEnv(gym.Env):
    """Environment for learning speculation strategy"""

    def __init__(self):
        # State: [confidence, cpu_idle, cache_util, hit_rate, balance, expected_in, active_jobs]
        self.observation_space = gym.spaces.Box(
            low=0, high=1, shape=(7,), dtype=np.float32
        )

        # Action: [WAIT, SPECULATE]
        self.action_space = gym.spaces.Discrete(2)

    def step(self, action):
        # Simulate speculation outcome
        confidence = self.state[0]

        if action == 1:  # SPECULATE
            # Did prediction come true?
            if np.random.random() < confidence:
                reward = 20  # Cache hit!
            else:
                reward = -5  # Wasted compute
        else:  # WAIT
            reward = 0  # No benefit, no cost

        return self.state, reward, True, {}

# Train
env = SpeculationEnv()
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=100_000)
model.save("models/speculation_policy")
```

---

## Why Current System Still Works

Even without RL, the statistical approach is valuable because:

1. **Simple patterns are common**:
   - CI/CD pipelines (same job every commit)
   - Cron jobs (hourly backups)
   - Development workflows (build → test → deploy)

2. **High confidence predictions are reliable**:
   - 100% confidence from pattern detector = actually works!
   - Economic constraints prevent waste

3. **Good enough for hackathon demo**:
   - Shows the concept works
   - Can add RL later as "future work"

---

## Best Approach for Hackathon

**Keep current system + Add RL as optional enhancement:**

1. **Base system** (current): Statistical pattern detection ✓
2. **RL Layer** (30 min to add): RL speculation policy
3. **Demo**: Show both working together

This way you have:
- Working system NOW ✓
- RL integration (shows ML expertise) ✓
- "Future: Use RL for pattern detection too" (slide)
