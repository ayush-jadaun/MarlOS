#!/usr/bin/env python3
"""
MarlOS Benchmark Script
Runs N nodes, submits M jobs, and reports performance metrics.

Usage:
    python scripts/benchmark.py
    python scripts/benchmark.py --nodes 5 --jobs 20
"""

import asyncio
import sys
import os
import time
import shutil
import argparse
import statistics
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from agent.config import (
    AgentConfig, NetworkConfig, RLConfig, DashboardConfig,
    TokenConfig, TrustConfig, ExecutorConfig, PredictiveConfig
)
from agent.main import MarlOSAgent
from agent.p2p.protocol import MessageType


def make_node_config(index: int, total_nodes: int, data_dir: str) -> AgentConfig:
    node_id = f"bench-node-{index + 1}"
    base_port = 7000 + (index * 10)
    dashboard_port = 5001 + index

    bootstrap_peers = []
    for j in range(total_nodes):
        if j != index:
            bootstrap_peers.append(f"tcp://127.0.0.1:{7000 + (j * 10)}")

    return AgentConfig(
        node_id=node_id,
        node_name=f"Bench-{index + 1}",
        network=NetworkConfig(
            pub_port=base_port,
            sub_port=base_port + 1,
            bootstrap_peers=bootstrap_peers,
            discovery_interval=2,
            heartbeat_interval=2,
        ),
        dashboard=DashboardConfig(port=dashboard_port),
        token=TokenConfig(starting_balance=500.0),
        trust=TrustConfig(),
        rl=RLConfig(online_learning=True, exploration_rate=0.1),
        executor=ExecutorConfig(max_concurrent_jobs=5, docker_enabled=False),
        predictive=PredictiveConfig(enabled=False),
        data_dir=os.path.join(data_dir, node_id),
    )


async def run_benchmark(num_nodes: int = 3, num_jobs: int = 10, verbose: bool = False):
    data_dir = os.path.join(os.path.dirname(__file__), ".bench_data")
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir, ignore_errors=True)

    agents: list[MarlOSAgent] = []
    job_submit_times: dict[str, float] = {}
    job_auction_times: dict[str, float] = {}
    job_complete_times: dict[str, float] = {}

    try:
        # ── Start nodes ──────────────────────────────────────────
        print(f"Starting {num_nodes} nodes...", end="", flush=True)
        for i in range(num_nodes):
            config = make_node_config(i, num_nodes, data_dir)
            agent = MarlOSAgent(config)
            await agent.start()
            agents.append(agent)
            await asyncio.sleep(0.3)
        print(" done")

        # ── Wait for discovery ───────────────────────────────────
        print("Waiting for peer discovery...", end="", flush=True)
        max_wait = 15
        start = time.time()
        while time.time() - start < max_wait:
            if all(a.p2p.get_peer_count() >= num_nodes - 1 for a in agents):
                break
            await asyncio.sleep(0.5)
        print(" done")

        all_connected = all(a.p2p.get_peer_count() >= num_nodes - 1 for a in agents)

        # ── Submit jobs ──────────────────────────────────────────
        print(f"Submitting {num_jobs} jobs...", end="", flush=True)

        # Distribute submissions across nodes (round-robin)
        for j in range(num_jobs):
            job_id = f"bench-job-{j + 1:04d}"
            submitter = agents[j % num_nodes]

            job = {
                'job_id': job_id,
                'job_type': 'shell',
                'payload': {'command': f'echo "bench {j + 1}"'},
                'payment': 20.0,
                'priority': 0.5,
                'deadline': time.time() + 120,
            }

            job_submit_times[job_id] = time.time()
            await submitter.p2p.broadcast_message(MessageType.JOB_BROADCAST, **job)

            # Small delay between submissions to avoid flooding
            await asyncio.sleep(0.2)

        print(" done")

        # ── Wait for completion ──────────────────────────────────
        print(f"Waiting for jobs to complete...", end="", flush=True)
        max_wait = max(60, num_jobs * 5)
        start = time.time()
        while time.time() - start < max_wait:
            total_completed = sum(a.jobs_completed for a in agents)
            total_failed = sum(a.jobs_failed for a in agents)
            if total_completed + total_failed >= num_jobs:
                break
            await asyncio.sleep(0.5)
        elapsed = time.time() - start
        print(f" done ({elapsed:.1f}s)")

        # ── Collect metrics ──────────────────────────────────────
        total_completed = sum(a.jobs_completed for a in agents)
        total_failed = sum(a.jobs_failed for a in agents)
        total_processed = total_completed + total_failed
        completion_rate = (total_completed / num_jobs * 100) if num_jobs > 0 else 0
        throughput = (total_completed / elapsed * 60) if elapsed > 0 else 0

        # Token metrics
        balances = [a.wallet.balance for a in agents]
        initial_balance = 500.0
        earnings = [b - initial_balance for b in balances]

        # Gini coefficient
        def gini(values):
            if not values or all(v == 0 for v in values):
                return 0.0
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            total = sum(sorted_vals)
            if total == 0:
                return 0.0
            cumulative = sum((2 * (i + 1) - n - 1) * v for i, v in enumerate(sorted_vals))
            return cumulative / (n * total)

        # Use absolute earnings for Gini (shift so min is 0)
        min_earning = min(earnings)
        shifted = [e - min_earning for e in earnings]
        gini_coeff = gini(shifted)

        # Trust metrics
        trust_scores = [a.reputation.get_my_trust_score() for a in agents]

        # Bid metrics
        total_won = sum(len(a.won_bids) for a in agents)
        total_lost = sum(len(a.lost_bids) for a in agents)

        # Jobs per node
        jobs_per_node = [a.jobs_completed for a in agents]

        # RL stats
        total_experiences = sum(a.online_learner.get_learning_stats()['buffer_size'] for a in agents)

        # ── Print results ────────────────────────────────────────
        print(f"\n{'=' * 50}")
        print(f"  MarlOS Benchmark Results")
        print(f"{'=' * 50}")
        print()
        print(f"  Network")
        print(f"  {'Nodes:':<25} {num_nodes}")
        print(f"  {'All connected:':<25} {'Yes' if all_connected else 'No'}")
        print(f"  {'Discovery time:':<25} < {min(15, elapsed):.1f}s")
        print()
        print(f"  Jobs")
        print(f"  {'Submitted:':<25} {num_jobs}")
        print(f"  {'Completed:':<25} {total_completed} ({completion_rate:.0f}%)")
        print(f"  {'Failed:':<25} {total_failed}")
        print(f"  {'Total time:':<25} {elapsed:.1f}s")
        print(f"  {'Throughput:':<25} {throughput:.1f} jobs/min")
        print()
        print(f"  Distribution")
        for i, agent in enumerate(agents):
            print(f"  {'  ' + agent.node_name + ':':<25} {agent.jobs_completed} jobs, {len(agent.won_bids)} wins, {len(agent.lost_bids)} losses")
        print(f"  {'Jobs per node (stddev):':<25} {statistics.stdev(jobs_per_node):.2f}" if len(jobs_per_node) > 1 else "")
        print()
        print(f"  Economy")
        for i, agent in enumerate(agents):
            print(f"  {'  ' + agent.node_name + ':':<25} {agent.wallet.balance:.2f} AC ({earnings[i]:+.2f})")
        print(f"  {'Gini coefficient:':<25} {gini_coeff:.3f} ({'fair' if gini_coeff < 0.3 else 'moderate' if gini_coeff < 0.5 else 'unfair'})")
        print()
        print(f"  Trust")
        print(f"  {'Min trust:':<25} {min(trust_scores):.3f}")
        print(f"  {'Max trust:':<25} {max(trust_scores):.3f}")
        print(f"  {'Avg trust:':<25} {statistics.mean(trust_scores):.3f}")
        print()
        print(f"  RL / Learning")
        print(f"  {'Online learning:':<25} ON")
        print(f"  {'Total experiences:':<25} {total_experiences}")
        print(f"  {'Bids placed:':<25} {total_won + total_lost}")
        print(f"  {'Auctions won:':<25} {total_won}")
        print()
        print(f"{'=' * 50}")

        if completion_rate >= 90 and gini_coeff < 0.5:
            print(f"  BENCHMARK: PASS")
        elif completion_rate >= 50:
            print(f"  BENCHMARK: PARTIAL")
        else:
            print(f"  BENCHMARK: FAIL")
        print(f"{'=' * 50}\n")

        return 0 if completion_rate >= 90 else 1

    except Exception as e:
        print(f"\nBenchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return 2

    finally:
        print("Shutting down...", end="", flush=True)
        for agent in agents:
            try:
                await agent.stop()
            except Exception:
                pass
        print(" done")

        if os.path.exists(data_dir):
            shutil.rmtree(data_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="MarlOS Benchmark")
    parser.add_argument("--nodes", "-n", type=int, default=3, help="Number of nodes (default: 3)")
    parser.add_argument("--jobs", "-j", type=int, default=10, help="Number of jobs (default: 10)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    exit_code = asyncio.run(run_benchmark(
        num_nodes=args.nodes,
        num_jobs=args.jobs,
        verbose=args.verbose
    ))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
