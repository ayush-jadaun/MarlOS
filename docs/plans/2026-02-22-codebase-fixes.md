# Codebase Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix five independent issues: stale file cleanup, debug print removal, real network latency in RL state, actual online learning update loop, and redundant doc deletion.

**Architecture:** All five tasks are independent — Task 1/5 are pure deletes, Task 2 is a logging refactor, Task 3 wires existing `HealthMonitor.get_p99_latency()` into `StateCalculator`, Task 4 adds behavioral cloning to the online learning loop.

**Tech Stack:** Python 3.11+, ZeroMQ, Stable-Baselines3, PyTorch

---

## Task 1: Delete stale root-level files

**Files:**
- Delete: `FINAL_TEST_REPORT.md`
- Delete: `INSTALL_FOR_FRIENDS.md` (duplicate of docs/INSTALL.md)
- Delete: `real_throughput_benchmark.py` (one-off script, not part of suite)
- Delete: `demo_checkpoint_recovery.py` (move intent: examples/ — just delete)
- Delete: `demo_recovery_with_checkpoint.py` (same)
- Delete: `test_submit.py` (one-off test, not in test suite)
- Delete: `test_job.json` (one-off test data)
- Delete: `PYPI_PUBLISHING_GUIDE.md` (not relevant to project users)

**Step 1: Delete all stale files**

```bash
cd /e/HACK36/MarlOS
rm FINAL_TEST_REPORT.md INSTALL_FOR_FRIENDS.md real_throughput_benchmark.py \
   demo_checkpoint_recovery.py demo_recovery_with_checkpoint.py \
   test_submit.py test_job.json PYPI_PUBLISHING_GUIDE.md
```

**Step 2: Verify root is clean**

```bash
ls /e/HACK36/MarlOS/*.py /e/HACK36/MarlOS/*.md /e/HACK36/MarlOS/*.json 2>/dev/null
```
Expected: Only `README.md`, `CHANGELOG.md`, `PROJECT_STRUCTURE.md` remain as .md files. No stray .py or .json at root.

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove stale root-level files and one-off scripts"
```

---

## Task 2: Fix node.py — remove duplicate import and replace debug prints with logging

**Files:**
- Modify: `agent/p2p/node.py`

**Problems:**
- Line 6 AND line 9: `import asyncio` appears twice
- Lines 317-320: raw `print(f"[P2P DEBUG]...")` in `broadcast_message()`
- Lines 356-364: raw `print(f"[P2P DEBUG]...")` in `_message_receiver()`
- Lines 393-396: raw `print(f"[P2P DEBUG]...")` for own message processing
- Lines 483, 493: `print(f"[P2P ACK]...")` should be debug-level

**Step 1: Add logging import, remove duplicate asyncio import**

In `agent/p2p/node.py`, change the top of the file from:
```python
import zmq
import zmq.asyncio
import asyncio
import sys
import asyncio
```
to:
```python
import logging
import zmq
import zmq.asyncio
import asyncio
import sys
```
Then add after the platform check block (after line ~20):
```python
logger = logging.getLogger(__name__)
```

**Step 2: Replace debug prints in broadcast_message() (lines 317-324)**

Replace:
```python
        # Debug logging for job broadcasts
        if message_type == MessageType.JOB_BROADCAST:
            print(f"[P2P DEBUG] Broadcasted {message_type} from {self.node_id}: {kwargs.get('job_id')}")
            # DON'T mark job_broadcasts as seen here - let receiver handle it
            # This allows the agent to receive and process its own job_broadcast
        else:
            # Mark other message types as seen to prevent re-processing
            self.seen_messages[signed_message['message_id']] = time.time()
```
with:
```python
        if message_type == MessageType.JOB_BROADCAST:
            logger.debug("Broadcasted %s from %s: %s", message_type, self.node_id, kwargs.get('job_id'))
        else:
            self.seen_messages[signed_message['message_id']] = time.time()
```

**Step 3: Replace debug prints in _message_receiver() (lines 356-364)**

Replace:
```python
                # Debug: Log all received messages with timestamp
                msg_type = message.get('type')
                receive_time = time.time()
                if msg_type == 'job_broadcast':
                    print(f"[P2P DEBUG] {self.node_id} received {msg_type} from {message.get('node_id')}")
                elif msg_type == 'job_bid':
                    bid_sent_time = message.get('timestamp', 0)
                    zmq_latency = (receive_time - bid_sent_time) * 1000
                    print(f"[P2P DEBUG] {self.node_id} ZMQ received job_bid from {message.get('node_id')} (ZMQ latency: {zmq_latency:.1f}ms)")
```
with:
```python
                msg_type = message.get('type')
                receive_time = time.time()
                if msg_type == 'job_bid':
                    bid_sent_time = message.get('timestamp', 0)
                    zmq_latency = (receive_time - bid_sent_time) * 1000
                    logger.debug("ZMQ received job_bid from %s (latency: %.1fms)", message.get('node_id'), zmq_latency)
```

**Step 4: Replace debug print for own job_broadcast processing (lines 393-396)**

Replace:
```python
                    if msg_type == 'job_broadcast':
                        job_id = message.get('job_id', 'unknown')
                        print(f"[P2P DEBUG] Processing own job_broadcast {job_id} for fair auction")
                        # Continue processing - don't skip
```
with:
```python
                    if msg_type == 'job_broadcast':
                        job_id = message.get('job_id', 'unknown')
                        logger.debug("Processing own job_broadcast %s for fair auction", job_id)
```

**Step 5: Replace ACK prints (lines 483, 493)**

Replace:
```python
                print(f"[P2P ACK] Received ACK from {node_id} for message {ack_message_id}")
```
with:
```python
                logger.debug("Received ACK from %s for message %s", node_id, ack_message_id)
```

Replace:
```python
                print(f"[P2P ACK] Sending ACK for {message_type} message {message_id} from {node_id}")
```
with:
```python
                logger.debug("Sending ACK for %s message %s from %s", message_type, message_id, node_id)
```

**Step 6: Verify the file parses cleanly**

```bash
python -c "import ast; ast.parse(open('agent/p2p/node.py').read()); print('OK')"
```
Expected: `OK`

**Step 7: Commit**

```bash
git add agent/p2p/node.py
git commit -m "fix: remove duplicate asyncio import and replace debug prints with logging in node.py"
```

---

## Task 3: Wire real network latency into RL state vector

**Files:**
- Modify: `agent/rl/state.py`
- Modify: `agent/main.py` (pass health_monitor to StateCalculator)

**Problem:** `agent/rl/state.py:102` has `network_latency = 0.1  # TODO`. The `HealthMonitor` in `agent/p2p/security.py` already tracks RTT via `get_p99_latency()` and `get_peer_rtt()`. We just need to wire it up.

**Step 1: Add `health_monitor` parameter to `StateCalculator.__init__`**

In `agent/rl/state.py`, change `__init__` signature:
```python
def __init__(self, node_id: str, enable_fairness: bool = True):
```
to:
```python
def __init__(self, node_id: str, enable_fairness: bool = True, health_monitor=None):
```

And inside `__init__`, add after `self.node_id = node_id`:
```python
        self.health_monitor = health_monitor  # HealthMonitor from P2PNode
```

**Step 2: Replace hardcoded latency in `_get_agent_state`**

Replace:
```python
            network_latency = 0.1  # TODO: Implement actual network measurement
```
with:
```python
            if self.health_monitor:
                raw_latency = self.health_monitor.get_p99_latency()
                # Normalize: clamp to [0, 1] where 1.0 = 1 second latency
                network_latency = min(1.0, raw_latency)
            else:
                network_latency = 0.1
```

**Step 3: Wire health_monitor in agent/main.py**

In `agent/main.py`, `__init__`, after `self.p2p = P2PNode(...)` and `self.rl_policy = RLPolicy(...)` are both created, add:
```python
        # Wire real network latency into RL state calculator
        self.rl_policy.state_calc.health_monitor = self.p2p.health_monitor
```

**Step 4: Verify state still produces correct shape**

```bash
cd /e/HACK36/MarlOS
python -c "
from agent.rl.state import StateCalculator
import time
sc = StateCalculator('test', enable_fairness=False)
job = {'job_type': 'shell', 'priority': 0.5, 'deadline': time.time()+300, 'payment': 100.0}
s = sc.calculate_state(job, 250.0, 0.75, 5, 2)
print('shape:', s.shape, '  latency slot:', s[3])
assert s.shape == (25,), f'Expected (25,), got {s.shape}'
assert 0.0 <= s[3] <= 1.0, f'Latency out of range: {s[3]}'
print('OK')
"
```
Expected: `shape: (25,)  latency slot: 0.1` (0.1 default when no health_monitor), then `OK`.

**Step 5: Run existing RL tests to make sure nothing broke**

```bash
cd /e/HACK36/MarlOS
python -m pytest test/ -k "rl or state or fairness" -v --timeout=30 2>&1 | tail -20
```
Expected: All previously passing tests still pass.

**Step 6: Commit**

```bash
git add agent/rl/state.py agent/main.py
git commit -m "feat: wire real P2P RTT into RL state vector (state[3] now live network latency)"
```

---

## Task 4: Implement online learning update (behavioral cloning on successful experiences)

**Files:**
- Modify: `agent/rl/online_learner.py`

**Problem:** Lines 155-163 have a `for` loop with a `# TODO: Actual training update` that does absolutely nothing. No weights are updated. The online learning system collects experiences but never learns from them.

**Approach:** Behavioral cloning — imitate the actions from successful experiences (reward > 0) by maximizing their log-probability under the current policy. This is a valid, simple form of online learning that actually updates PPO weights without requiring a full rollout environment.

**Step 1: Add torch import at top of online_learner.py**

The file already imports from `stable_baselines3`. Add at top:
```python
import torch
```

**Step 2: Replace the TODO loop in `_perform_update`**

Replace:
```python
            # Train for a few steps
            num_updates = min(10, len(experiences) // self.batch_size)

            for i in range(num_updates):
                # Sample batch
                batch_experiences = self.buffer.sample(self.batch_size)

                # TODO: Actual training update
                # For PPO, we'd need to compute advantages, update policy, etc.
```
with:
```python
            # Behavioral cloning: imitate successful actions
            # Filter to experiences with positive reward (good decisions to reinforce)
            successful = [e for e in experiences if e.reward > 0]

            if len(successful) < self.batch_size:
                print(f"[ONLINE LEARNER] Not enough successful experiences ({len(successful)}), skipping BC update")
            elif self.training_model is None:
                print(f"[ONLINE LEARNER] No training model available, skipping update")
            else:
                num_updates = min(10, len(successful) // self.batch_size)
                total_loss = 0.0

                for i in range(num_updates):
                    batch_experiences = self.buffer.sample(self.batch_size)
                    good_batch = [e for e in batch_experiences if e.reward > 0]
                    if not good_batch:
                        continue

                    states = np.array([e.state for e in good_batch])
                    actions = np.array([e.action for e in good_batch])

                    try:
                        from stable_baselines3.common.utils import obs_as_tensor
                        obs_t = obs_as_tensor(states, self.training_model.device)
                        act_t = torch.tensor(actions, dtype=torch.long,
                                             device=self.training_model.device)

                        # Get action log-probs from current policy
                        distribution = self.training_model.policy.get_distribution(obs_t)
                        log_probs = distribution.log_prob(act_t)

                        # Behavioral cloning loss: maximize log-prob of good actions
                        loss = -log_probs.mean()
                        total_loss += loss.item()

                        self.training_model.policy.optimizer.zero_grad()
                        loss.backward()
                        # Gradient clipping to avoid instability
                        torch.nn.utils.clip_grad_norm_(
                            self.training_model.policy.parameters(), max_norm=0.5
                        )
                        self.training_model.policy.optimizer.step()

                    except Exception as update_err:
                        print(f"[ONLINE LEARNER] BC update error (step {i}): {update_err}")
                        break

                if num_updates > 0:
                    avg_loss = total_loss / num_updates
                    print(f"[ONLINE LEARNER] BC updates: {num_updates}, avg loss: {avg_loss:.4f}")
```

**Step 3: Verify the file parses cleanly**

```bash
python -c "import ast; ast.parse(open('agent/rl/online_learner.py').read()); print('OK')"
```
Expected: `OK`

**Step 4: Run the existing online learner tests**

```bash
python -m pytest test/ -k "learner or online" -v --timeout=30 2>&1 | tail -20
```
Expected: All previously passing online learner tests still pass.

**Step 5: Commit**

```bash
git add agent/rl/online_learner.py
git commit -m "feat: implement behavioral cloning update loop in online learner (was TODO no-op)"
```

---

## Task 5: Delete clearly redundant docs

**Files to delete** (pure duplicates — content exists elsewhere):
- `docs/PIP_INSTALLATION_SUMMARY.md` — subset of PIP_INSTALL.md
- `docs/CROSS_INTERNET_DISCOVERY.md` — covered by DISTRIBUTED_DEPLOYMENT.md + NETWORK_DESIGN.md
- `docs/DEPLOYMENT_VERIFICATION.md` — covered by QUICKSTART.md
- `docs/INTEGRATION_GUIDE.md` — covered by INSTALL.md + CONFIG_MANAGEMENT_GUIDE.md

**Files to consolidate** (merge into one):
- Merge `docs/CONFIG_ARCHITECTURE.md` + `docs/CONFIG_MANAGEMENT_GUIDE.md` + `docs/FULL_CONFIG_USAGE.md` → keep only `docs/CONFIG_MANAGEMENT_GUIDE.md` (most complete, rename approach: keep file, add note at top of other two pointing to it)
- Add a one-liner redirect in `CONFIG_ARCHITECTURE.md` and `FULL_CONFIG_USAGE.md`:
  ```markdown
  > **Note:** This document has been consolidated. See [CONFIG_MANAGEMENT_GUIDE.md](CONFIG_MANAGEMENT_GUIDE.md) for the full reference.
  ```

**Step 1: Delete pure duplicates**

```bash
cd /e/HACK36/MarlOS/docs
rm PIP_INSTALLATION_SUMMARY.md CROSS_INTERNET_DISCOVERY.md DEPLOYMENT_VERIFICATION.md INTEGRATION_GUIDE.md
```

**Step 2: Redirect overlapping config docs**

In `docs/CONFIG_ARCHITECTURE.md`, prepend:
```markdown
> **This document has been consolidated. See [CONFIG_MANAGEMENT_GUIDE.md](CONFIG_MANAGEMENT_GUIDE.md) for the complete configuration reference.**

---
```

In `docs/FULL_CONFIG_USAGE.md`, prepend:
```markdown
> **This document has been consolidated. See [CONFIG_MANAGEMENT_GUIDE.md](CONFIG_MANAGEMENT_GUIDE.md) for the complete configuration reference.**

---
```

**Step 3: Update docs/README.md links if present**

```bash
grep -l "PIP_INSTALLATION_SUMMARY\|CROSS_INTERNET\|DEPLOYMENT_VERIFICATION\|INTEGRATION_GUIDE" /e/HACK36/MarlOS/docs/README.md /e/HACK36/MarlOS/README.md 2>/dev/null
```
If any files are returned, remove the dead links from them.

**Step 4: Verify docs directory**

```bash
ls /e/HACK36/MarlOS/docs/
```
Expected: Cleaner list without the deleted files.

**Step 5: Commit**

```bash
git add -A
git commit -m "docs: remove duplicate docs, add redirect notices to consolidated config docs"
```

---

## Execution Order

Tasks 1, 2, 3, 4, 5 are **all independent** — they touch different files.
Run them in parallel with separate subagents for maximum speed.

Suggested parallel grouping:
- **Agent A**: Task 1 + Task 5 (all file deletes / doc changes)
- **Agent B**: Task 2 + Task 3 (node.py + state.py code fixes)
- **Agent C**: Task 4 (online_learner.py standalone)
