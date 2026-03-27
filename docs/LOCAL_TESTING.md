# Local Testing Guide

How to test MarlOS on a single machine. Everything runs on localhost -- no Docker, no cloud, no extra hardware required.

---

## 1. Prerequisites

**Python 3.11+** is required. Check your version:

```bash
python --version
```

**Install dependencies:**

```bash
pip install -r requirements.txt
```

Key packages this pulls in: `pyzmq`, `stable-baselines3`, `gymnasium`, `cryptography`, `pynacl`, `aiohttp`, `rich`, `click`.

Optional (for chart generation in simulations):

```bash
pip install matplotlib
```

---

## 2. Run the E2E Demo

The demo starts a local multi-node MarlOS network, submits jobs, and walks you through the full lifecycle.

```bash
python scripts/demo.py --nodes 3 --jobs 2
```

Or via the CLI:

```bash
marl demo --nodes 3 --jobs 2
```

### What happens step by step

1. **Node startup** -- 3 agent nodes launch on localhost. Each gets its own ZMQ PUB/SUB ports (6000, 6010, 6020) and dashboard ports (4001, 4002, 4003). Every node starts with 100 AC (MarlCredits).
2. **Peer discovery** -- Nodes exchange heartbeats over ZMQ and discover each other. The demo waits up to 15 seconds for all nodes to see all peers.
3. **Initial state snapshot** -- Prints each node's balance, trust score (starts at 0.5), and executor capabilities.
4. **Job submission** -- Node 1 broadcasts 2 jobs to the network via ZMQ `JOB_BROADCAST` messages. Each job is a simple shell command (`echo "Hello from MarlOS job N!"`), with a payment of 50-60 AC.
5. **Auction and execution** -- All nodes receive the job broadcast. The RL policy (PPO, 3 actions: BID/FORWARD/DEFER) decides whether to bid. The `BiddingAuction` collects bids, picks a winner based on score (capability, trust, load), and the winner executes the job via the `ShellRunner`.
6. **Token transfer** -- The winner receives payment. The token economy handles staking, fees, and redistribution.
7. **Trust update** -- Successful execution increases the winner's trust score. Failed jobs decrease it.
8. **RL learning stats** -- Shows each node's online learning buffer size and update count.

**Expected output:** `RESULT: ALL SYSTEMS OPERATIONAL` means all jobs completed and all peers connected.

---

## 3. Run the Benchmark

Measures throughput, fairness, and economy health under load.

```bash
python scripts/benchmark.py --nodes 3 --jobs 10
```

For a heavier test:

```bash
python scripts/benchmark.py --nodes 5 --jobs 20 --verbose
```

### Output metrics explained

| Metric | What it means |
|---|---|
| **Completed / Failed** | How many jobs succeeded vs failed out of total submitted |
| **Throughput (jobs/min)** | Sustained job completion rate |
| **Jobs per node (stddev)** | How evenly work is distributed; lower = fairer |
| **Gini coefficient** | Wealth inequality across nodes (0 = perfect equality, 1 = one node has everything). Below 0.3 is "fair", 0.3-0.5 is "moderate", above 0.5 is "unfair" |
| **Trust (min/max/avg)** | Trust score range across nodes (0.0 to 1.0) |
| **Total experiences** | How many RL training samples were collected across all nodes |
| **Auctions won** | Total bids that won across all nodes |

**Pass criteria:** completion rate >= 90% and Gini < 0.5.

---

## 4. Run the Economic Simulation

Simulates 100 nodes and 1000 jobs (no real ZMQ networking -- pure simulation) to compare the fairness system ON vs OFF.

```bash
python scripts/economic_simulation.py
```

Custom parameters:

```bash
python scripts/economic_simulation.py --nodes 50 --jobs 500 --output docs/charts --seed 42
```

### Charts generated in `docs/charts/`

| File | What it shows |
|---|---|
| `gini_over_time.png` | Gini coefficient over time, fairness ON (green) vs OFF (red) |
| `wealth_distribution.png` | Side-by-side histograms of final node balances |
| `participation.png` | What fraction of nodes have won at least one job over time |
| `job_distribution.png` | How many jobs each node won, fair vs unfair |

The console also prints a comparison table: Gini coefficient, participation rate, min/max/median balance, and how many nodes are broke (< 10 AC).

**Requires matplotlib.** If not installed, the simulation still runs and prints the table -- it just skips chart generation.

---

## 5. Run the Adversarial Demo

Simulates a network with honest and malicious nodes. Demonstrates that the trust/reputation system detects and quarantines bad actors.

```bash
python scripts/adversarial_demo.py
```

Custom parameters:

```bash
python scripts/adversarial_demo.py --honest 10 --malicious 3 --jobs 100 --output docs/charts
```

### What to look for

- Malicious nodes fail 80% of their jobs and get caught 30% of the time with a harsh trust penalty (-0.50).
- Nodes with trust below 0.2 are quarantined and excluded from future job assignment.
- The console prints `[QUARANTINE]` lines as bad actors get caught.
- **Detection rate** should be 100% (all malicious nodes quarantined). **False positives** should be 0 (no honest nodes quarantined).

Charts generated: `adversarial_trust.png` (trust scores over time) and `adversarial_final_trust.png` (final trust bar chart).

---

## 6. Run the Online Learning Proof

Simulates a single RL agent processing 200 jobs, showing that the policy learns to bid better over time.

```bash
python scripts/online_learning_proof.py
```

Custom parameters:

```bash
python scripts/online_learning_proof.py --jobs 200 --output docs/charts
```

### What to look for in the output

- **Exploration rate** decays from 0.1 toward 0.01 (the agent explores less and exploits more).
- **Win rate** should increase from early to late jobs.
- **Bid threshold** evolves as the agent learns which jobs are worth bidding on.
- The script prints early vs late win rate and the improvement in percentage points.

Chart generated: `online_learning_proof.png` (4-panel: exploration decay, win rate, avg reward, bid threshold evolution).

---

## 7. Run the Test Suite

### All unit tests (skip integration)

```bash
python -m pytest test/ --ignore=test/integration -v
```

### With a timeout (recommended)

```bash
python -m pytest test/ --ignore=test/integration --timeout=30 -v
```

### By module

```bash
# Token economy
python -m pytest test/token/ -v

# RL policy and fairness
python -m pytest test/ -k "rl or state or fairness" -v

# P2P networking and security
python -m pytest test/p2p/ -v
python -m pytest test/test_p2p_security.py -v

# Trust and reputation
python -m pytest test/trust/ -v

# Executor
python -m pytest test/executor/ -v

# Prediction engine
python -m pytest test/prediction/ -v

# Routing
python -m pytest test/routing/ -v
```

### REST API tests

```bash
python -m pytest test/api/ -v
```

### Pipeline tests (DAG execution, result aggregation)

```bash
python -m pytest test/pipeline/ -v
```

### Plugin system tests

```bash
python -m pytest test/plugins/ -v
```

### Integration tests (may be flaky)

```bash
python -m pytest test/integration/ -v --timeout=60
```

Note: integration tests start real ZMQ sockets and full agent instances. Only 1 out of 10 currently passes reliably -- these are skipped by default.

---

## 8. Start a Real Node

### Start the agent

```bash
NODE_ID=dev-node python -m agent.main
```

This starts:
- **ZMQ PUB** on port 5555 (P2P message broadcasting)
- **ZMQ SUB** on port 5556 (P2P message receiving)
- **WebSocket dashboard** on port 3001
- **REST API** on port 3101 (dashboard port + 100)

### Check health

```bash
curl http://localhost:3101/api/health
```

### Get node status

```bash
curl http://localhost:3101/api/status
```

### Submit a job via REST API

```bash
curl -X POST http://localhost:3101/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "shell",
    "payload": {"command": "echo hello from MarlOS"},
    "payment": 50.0,
    "priority": 0.5
  }'
```

The response includes a `job_id`. Poll for the result:

```bash
curl http://localhost:3101/api/jobs/<job_id>
```

### Other useful endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | Health check |
| `/api/status` | GET | Full node status (balance, trust, peers, RL stats) |
| `/api/jobs` | GET | List all known jobs |
| `/api/jobs` | POST | Submit a job |
| `/api/jobs/{id}` | GET | Get job status/result |
| `/api/peers` | GET | Connected peers list |
| `/api/wallet` | GET | Wallet balance and transaction history |
| `/api/trust` | GET | Trust scores |
| `/api/rl` | GET | RL policy stats |
| `/api/pipelines` | POST | Submit a job pipeline (DAG) |
| `/api/groups` | POST | Submit a batch of jobs |

### Submit a job via CLI (requires running node)

```bash
marl execute "ls -la"
```

### Override ports with environment variables

```bash
NODE_ID=dev-node PUB_PORT=5555 SUB_PORT=5556 DASHBOARD_PORT=3001 python -m agent.main
```

---

## 9. Troubleshooting

### Port conflicts

**Symptom:** `Address already in use` or `zmq.error.ZMQError: Address in use`

**Fix:** Another process (or a previous run) is holding the port. Kill it or use different ports:

```bash
# Find what's using port 5555 (Linux/macOS)
lsof -i :5555

# Find what's using port 5555 (Windows)
netstat -ano | findstr :5555

# Use different ports
NODE_ID=dev-node PUB_PORT=7777 SUB_PORT=7778 DASHBOARD_PORT=4001 python -m agent.main
```

### ZMQ socket errors

**Symptom:** `zmq.Again` or `zmq.error.ZMQError: Resource temporarily unavailable`

This usually means a peer is unreachable or the socket timed out. In local testing this is normal during startup -- nodes retry automatically. Wait a few seconds for discovery to complete.

### Missing dependencies

**Symptom:** `ModuleNotFoundError: No module named 'zmq'` (or any other package)

**Fix:**

```bash
pip install -r requirements.txt
```

If you see issues with `winloop` on Windows or `uvloop` on Linux, these are optional performance packages. The agent falls back to the default event loop if they fail to import.

### Demo or benchmark hangs

**Symptom:** Script stalls at "Waiting for peer discovery" or "Waiting for jobs to complete"

**Causes:**
- Firewall blocking localhost connections (rare, but some corporate firewalls do this)
- Another instance running on the same ports

**Fix:** Kill all Python processes and try again with fresh ports. The demo uses ports starting at 6000, the benchmark uses ports starting at 7000.

### pytest hangs or times out

**Fix:** Always use the `--timeout` flag:

```bash
python -m pytest test/ --ignore=test/integration --timeout=30 -v
```

If a specific async test hangs, it is likely waiting on a ZMQ socket. Skip it with `-k "not test_name"`.

### matplotlib not found (simulation charts)

**Symptom:** `matplotlib not installed, skipping charts`

**Fix:**

```bash
pip install matplotlib
```

The simulations (economic, adversarial, online learning) still produce console output without matplotlib -- you just won't get the PNG charts.

### Windows encoding errors

**Symptom:** `UnicodeEncodeError` when printing emoji-style log output

**Fix:** The scripts auto-configure UTF-8 encoding on Windows. If you still see errors, set the environment variable before running:

```bash
set PYTHONIOENCODING=utf-8
```

Or run in Windows Terminal (not the legacy `cmd.exe`), which has better Unicode support.
