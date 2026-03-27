# Contributing to MarlOS

Thanks for your interest in contributing to MarlOS! This guide will help you get started.

## Development Setup

```bash
# Clone and install
git clone https://github.com/ayush-jadaun/MarlOS.git
cd MarlOS
pip install -r requirements.txt
pip install -e .

# Run tests
python -m pytest test/ --ignore=test/integration -v

# Run the demo
python scripts/demo.py
```

## Project Structure

```
agent/           # Core agent code
  p2p/           # ZeroMQ PUB/SUB networking, Ed25519 auth
  rl/            # PPO policy, online learner, state calculator
  bidding/       # Auction system, bid scoring, job routing
  executor/      # Job runners (shell, docker, security)
  tokens/        # Wallet, ledger, token economy
  trust/         # Reputation system, watchdog
  predictive/    # Speculation cache, pattern learning
  dashboard/     # WebSocket server
cli/             # CLI entry point (`marl` command)
rl_trainer/      # PPO training scripts
scripts/         # Demo, benchmarks, utilities
test/            # Test suite (209+ tests)
dashboard/       # React frontend
docs/            # Architecture documentation
```

## Code Style

- Python 3.11+, async/await throughout
- No synchronous blocking calls in agent code paths
- Ed25519 on all P2P messages — never bypass signature verification
- Never hardcode node IDs or IP addresses
- Use emoji prefixes for info-level logs: `[P2P]`, `[RL]`, `[WALLET]`, etc.
- Use `logging.debug()` for debug-level output (not print)

## Commit Messages

```
feat: new functionality
fix: bug fix
chore: cleanup, deps, non-code
docs: documentation only
test: test-only changes
```

Keep messages concise and focused on the "why" not the "what".

## Pull Request Process

1. Fork the repo and create a branch from `main`
2. Make your changes
3. Run the test suite: `python -m pytest test/ --ignore=test/integration -v`
4. Run the demo to verify nothing broke: `python scripts/demo.py`
5. Open a PR with a clear description

## Writing a New Runner

The easiest way to contribute is adding a new job runner:

```python
# In agent/executor/your_runner.py
class YourRunner:
    async def run(self, job: dict) -> dict:
        payload = job.get('payload', {})
        # ... do work ...
        return {'status': 'success', 'result': output}
```

Then register it in `agent/main.py`:

```python
your_runner = YourRunner()
self.executor.register_runner('your_type', your_runner.run)
```

## Architecture Decisions

Before making significant architecture changes, please:

1. Read the relevant docs in `docs/` (especially `ARCHITECTURE_RL.md` and `NETWORK_DESIGN.md`)
2. Open an issue to discuss the change
3. Consider impact on the RL state space (currently 25D)
4. Ensure backward compatibility with existing P2P protocol

## Questions?

Open an issue on [GitHub](https://github.com/ayush-jadaun/MarlOS/issues).
