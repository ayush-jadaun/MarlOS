# MarlOS — Claude Project Context

## What This Is
Decentralized distributed computing OS built at Hack36. No central orchestrator — every node is autonomous, communicates via ZeroMQ PUB/SUB, uses Ed25519 for auth, and makes bidding decisions via PPO reinforcement learning. Tokens (MarlCredits/AC) power the economy. No Kubernetes, no cloud controller.

## Key Entry Points
- `agent/main.py` — `MarlOSAgent` class, wires everything together
- `cli/main.py` — `marl` CLI entry point
- `agent/config.py` — `AgentConfig` dataclass + `load_config()` (3-tier: defaults → YAML → env vars)
- `rl_trainer/train_policy.py` — PPO training script

## Architecture Layers (in order of data flow)
```
P2P (ZMQ) → Auction/Bidding → RL Decision (PPO) → Executor → Token Economy → Trust/Reputation
```
- `agent/p2p/` — ZMQ gossip, Ed25519 auth, replay protection, quorum consensus, rate limiting
- `agent/rl/` — PPO policy (35-dim state), 3 actions: BID=0 FORWARD=1 DEFER=2
- `agent/bidding/` — auction.py (non-blocking bids), scorer.py, router.py
- `agent/executor/` — shell, docker, security (malware_scan/port_scan/hash_crack/threat_intel), hardware (MQTT)
- `agent/tokens/` — wallet.py (SQLite-backed), ledger.py, economy.py
- `agent/trust/` — reputation.py (0.0–1.0 scores, quarantine < 0.2), watchdog.py
- `agent/predictive/` — speculation cache, pattern learning, pre-execution
- `agent/dashboard/` — WebSocket server on port 3001

## Network Modes
- `PRIVATE` — manual peer list via `BOOTSTRAP_PEERS` env var or `~/.marlos/peers.json`
- `PUBLIC` — DHT-based auto-discovery (partially implemented)

## Config (3-tier precedence, lowest → highest)
1. Dataclass defaults in `agent/config.py`
2. YAML file: `~/.marlos/nodes/{NODE_ID}/config.yaml`
3. Env vars: `NODE_ID`, `PUB_PORT`, `SUB_PORT`, `DASHBOARD_PORT`, `NETWORK_MODE`, `BOOTSTRAP_PEERS`, `ENABLE_HARDWARE_RUNNER`

## Running Tests
```bash
# All tests (skip integration)
python -m pytest test/ --ignore=test/integration -v

# Specific module
python -m pytest test/token/ -v
python -m pytest test/ -k "rl or state or fairness" -v

# With timeout
python -m pytest test/ --ignore=test/integration --timeout=30 -v
```

## Running a Node
```bash
# Single node (development)
NODE_ID=dev-node python -m agent.main

# With bootstrap peers
NODE_ID=node-1 BOOTSTRAP_PEERS="tcp://192.168.1.100:5555" python -m agent.main

# Docker multi-node
docker-compose up -d
```

## Submitting a Job
```bash
# Via CLI
marl execute "ls -la"

# Via Python
python -c "
from cli.marlOS import submit_job
submit_job({'job_type': 'shell', 'payload': {'command': 'echo hello'}, 'payment': 50.0})
"
```

## Key Known Issues (as of 2026-02-22)
- Online learning loop was a no-op (TODO) — being fixed
- Network latency in RL state was hardcoded to 0.1 — being fixed
- Integration tests: only 1/10 pass (skipped for now)
- DHT/Public mode bootstrap is incomplete

## Style Rules
- Python 3.11+, async/await throughout
- No new synchronous blocking calls in agent code paths
- Print with emoji for info-level logs (`[P2P]`, `[RL]`, etc.)
- Use `logging.debug()` for debug-level output (not print)
- Ed25519 on all P2P messages — do not bypass signature verification
- Never hardcode node IDs or IP addresses

## Commit Style
- `feat:` new functionality
- `fix:` bug fix
- `chore:` cleanup, deps, non-code
- `docs:` documentation only
- `test:` test-only changes
