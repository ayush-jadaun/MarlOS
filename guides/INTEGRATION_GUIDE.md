# Predictive Pre-Execution Integration Guide

## ✅ What's Been Created

The predictive system is fully implemented in `agent/predictive/`:

1. **PatternDetector** - Learns job patterns (repeated, sequences, time-based)
2. **ResultCache** - Stores pre-executed results with TTL
3. **SpeculationEngine** - Decides what to pre-execute based on economics
4. **PredictiveExtension** - Integration module (non-breaking)

## 🔧 How to Integrate (3 Simple Steps)

### Step 1: Add to agent/main.py **init** (around line 100)

```python
# After initializing online_learner, add:

# PREDICTIVE SYSTEM (optional, non-breaking)
from .predictive.integration import PredictiveExtension
self.predictive = PredictiveExtension(self)
```

### Step 2: Start/stop predictive system in agent/main.py

In `async def start(self)` method (around line 334):

```python
await self.online_learner.start()

# ADD THIS:
await self.predictive.start()
```

In `async def stop(self)` method (around line 362):

```python
await self.dashboard.stop()

# ADD THIS:
await self.predictive.stop()
```

### Step 3: Add hooks in `_handle_new_job` (around line 370)

**A) Observe job submission:**

```python
async def _handle_new_job(self, job_message: dict):
    """Handle new job broadcast - decide whether to bid"""
    job_id = job_message['job_id']
    job_type = job_message['job_type']

    print(f"\n📥 New job received: {job_id} ({job_type})")

    # ADD THIS: Observe for pattern learning
    self.predictive.observe_job_submission(job_message)

    # (rest of method continues unchanged...)
```

**B) Check cache in `_execute_job` method (around line 531):**

```python
async def _execute_job(self, job: dict, stake_amount: float):
    """Execute a job we won"""
    job_id = job['job_id']

    print(f"\n▶️  Executing job {job_id}")

    # ADD THIS: Check if we have a cached result
    cached_result = self.predictive.check_cache(job)
    if cached_result:
        print(f" CACHE HIT! Using pre-executed result")
        # Use cached result
        await self._handle_job_result(cached_result)
        return

    # Execute normally if no cache hit
    result = await self.executor.execute_job(job)
```

### Step 4: (Optional) Add stats to dashboard

In dashboard state broadcast, add:

```python
predictive_stats = self.predictive.get_stats()
```

## 🧪 Testing

### Test Script 1: Repeated Jobs

```bash
# Create test script
cat > test_predictive.py << 'EOF'
import asyncio
import time

async def test_repeated_jobs():
    # Submit same job 5 times to establish pattern
    for i in range(5):
        print(f"\n[TEST] Submitting job {i+1}/5")
        # Submit via CLI or programmatically
        await asyncio.sleep(30)  # 30 second interval

    print("\n[TEST] Pattern established! Next submission should hit cache...")
    await asyncio.sleep(30)

    # This one should be pre-executed and hit cache!
    print("[TEST] Submitting 6th job - expect CACHE HIT!")

asyncio.run(test_repeated_jobs())
EOF

python test_predictive.py
```

### Test Script 2: Manual Cache Test

```python
from agent.predictive.pattern_detector import PatternDetector
from agent.predictive.cache import ResultCache

# Create detector
detector = PatternDetector(min_occurrences=3)

# Simulate repeated job
job = {
    'job_id': 'test-1',
    'job_type': 'shell',
    'params': {'command': 'echo hello'}
}

# Observe it 3 times
for i in range(3):
    detector.observe_job(job)

# Check predictions
predictions = detector.predict_next_jobs()
print(f"Predictions: {predictions}")
```

## 📊 Monitoring

Check predictive stats:

```python
stats = agent.predictive.get_stats()
print(f"""
Pattern Detector:
  - Jobs seen: {stats['pattern_detector']['total_jobs_seen']}
  - Patterns: {stats['pattern_detector']['unique_fingerprints']}

Cache:
  - Hit rate: {stats['cache']['hit_rate']:.1f}%
  - Cache hits: {stats['cache']['cache_hits']}
  - Size: {stats['cache']['cache_size']}/{stats['cache']['max_size']}

Speculation:
  - Attempted: {stats['speculation']['speculations_attempted']}
  - Successful: {stats['speculation']['speculations_successful']}
  - Success rate: {stats['speculation']['success_rate']:.1f}%
""")
```

## 🎯 Demo for Hackathon

**Create a repeating job pattern:**

```bash
# Terminal 1: Start agent
python -m agent.main

# Terminal 2: Submit jobs
while true; do
    python cli/marlOS.py submit --type shell --command "echo 'Hello MarlOS'" --payment 10
    sleep 45
done
```

After 3 iterations (about 2.5 minutes), the system will:

1. Detect pattern (job every ~45s)
2. Pre-execute before next submission
3. **INSTANT CACHE HIT** when job actually arrives!

**Expected output:**

```
 CACHE HIT! Using pre-executed result
   Latency: 0.08s (would have been 2.3s)
   Saved: 2.22s of compute time!
```

## 🔥 Cool Demo Tricks

1. **Show before/after latency:**

   - First 3 jobs: normal latency (1-3s)
   - Job 4+: instant (<0.1s)

2. **Live stats in dashboard:**

   - Cache hit rate climbing
   - Pattern confidence increasing

3. **Show economic intelligence:**
   - High confidence (90%) → speculates
   - Low confidence (40%) → doesn't waste resources

## ⚠️ Important Notes

1. **Non-breaking:** If `predictive.enabled = False` in config, everything runs as before
2. **Resource limits:** Max 20% of capacity used for speculation
3. **Economic safety:** Only speculates when expected value > 3 AC

## 🐛 Troubleshooting

**"No cache hits":**

- Check: Are jobs identical? (same type + params)
- Check: Is TTL long enough? (default 300s = 5min)
- Check: Did pattern repeat 3+ times?

**"Too much speculation":**

- Decrease `max_speculation_ratio` in config
- Increase `min_pattern_confidence`

**"System not learning":**

- Check: Is `predictive.enabled = True`?
- Check: Are jobs being observed? (logs show "observed job")
