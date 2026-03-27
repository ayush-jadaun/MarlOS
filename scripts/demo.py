#!/usr/bin/env python3
"""
MarlOS End-to-End Demo
Starts 3 nodes on localhost, submits a job, shows the full lifecycle:
  peer discovery -> auction -> RL decision -> execution -> token transfer -> trust update

Usage:
    python scripts/demo.py
    python scripts/demo.py --nodes 5 --jobs 3
"""

import asyncio
import sys
import os
import time
import json
import uuid
import shutil
import argparse
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fix Windows encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from agent.config import AgentConfig, NetworkConfig, RLConfig, DashboardConfig, TokenConfig, TrustConfig, ExecutorConfig, PredictiveConfig
from agent.main import MarlOSAgent


# ── Styles ──────────────────────────────────────────────────────────
BOLD = "\033[1m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
DIM = "\033[2m"
RESET = "\033[0m"

def banner(msg):
    width = 60
    print(f"\n{CYAN}{BOLD}{'=' * width}")
    print(f"  {msg}")
    print(f"{'=' * width}{RESET}\n")

def step(msg):
    print(f"{GREEN}{BOLD}>> {msg}{RESET}")

def info(msg):
    print(f"   {DIM}{msg}{RESET}")

def result(msg):
    print(f"   {YELLOW}{msg}{RESET}")

def error(msg):
    print(f"   {RED}{msg}{RESET}")


# ── Node Config Factory ────────────────────────────────────────────
def make_node_config(index: int, total_nodes: int, data_dir: str) -> AgentConfig:
    """Create config for node at given index, wired to connect to all other nodes."""
    node_id = f"demo-node-{index + 1}"
    base_port = 6000 + (index * 10)
    pub_port = base_port
    sub_port = base_port + 1
    dashboard_port = 4001 + index

    # Build bootstrap peers: connect to all other nodes' PUB ports
    bootstrap_peers = []
    for j in range(total_nodes):
        if j != index:
            peer_pub_port = 6000 + (j * 10)
            bootstrap_peers.append(f"tcp://127.0.0.1:{peer_pub_port}")

    node_data_dir = os.path.join(data_dir, node_id)

    return AgentConfig(
        node_id=node_id,
        node_name=f"Node-{index + 1}",
        network=NetworkConfig(
            pub_port=pub_port,
            sub_port=sub_port,
            bootstrap_peers=bootstrap_peers,
            discovery_interval=2,
            heartbeat_interval=2,
        ),
        dashboard=DashboardConfig(port=dashboard_port),
        token=TokenConfig(starting_balance=100.0),
        trust=TrustConfig(),
        rl=RLConfig(online_learning=True, exploration_rate=0.15),
        executor=ExecutorConfig(max_concurrent_jobs=3, docker_enabled=False),
        predictive=PredictiveConfig(enabled=False),
        data_dir=node_data_dir,
    )


# ── Demo Runner ────────────────────────────────────────────────────
async def run_demo(num_nodes: int = 3, num_jobs: int = 2):
    data_dir = os.path.join(os.path.dirname(__file__), ".demo_data")

    # Clean up previous demo data
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir, ignore_errors=True)

    agents: list[MarlOSAgent] = []

    try:
        # ── Step 1: Start nodes ──────────────────────────────────
        banner("STEP 1: Starting MarlOS Nodes")

        for i in range(num_nodes):
            config = make_node_config(i, num_nodes, data_dir)
            step(f"Starting {config.node_name} (pub={config.network.pub_port}, dashboard={config.dashboard.port})")
            agent = MarlOSAgent(config)
            await agent.start()
            agents.append(agent)
            await asyncio.sleep(0.5)

        step(f"All {num_nodes} nodes started!")

        # ── Step 2: Wait for peer discovery ──────────────────────
        banner("STEP 2: Peer Discovery")
        step("Waiting for nodes to discover each other...")

        max_wait = 15
        start = time.time()
        while time.time() - start < max_wait:
            peer_counts = [a.p2p.get_peer_count() for a in agents]
            info(f"Peer counts: {peer_counts}")
            if all(c >= num_nodes - 1 for c in peer_counts):
                break
            await asyncio.sleep(1)

        for agent in agents:
            pc = agent.p2p.get_peer_count()
            result(f"{agent.node_name}: {pc} peers connected")

        if all(a.p2p.get_peer_count() >= num_nodes - 1 for a in agents):
            step("All nodes fully connected!")
        else:
            error("Some nodes didn't fully connect (continuing anyway)")

        # ── Step 3: Show initial state ───────────────────────────
        banner("STEP 3: Initial Network State")
        for agent in agents:
            result(
                f"{agent.node_name}: "
                f"balance={agent.wallet.balance:.2f} AC, "
                f"trust={agent.reputation.get_my_trust_score():.3f}, "
                f"caps={agent.executor.get_capabilities()}"
            )

        # ── Step 4: Submit jobs ──────────────────────────────────
        banner("STEP 4: Submitting Jobs")

        jobs_submitted = []
        for j in range(num_jobs):
            job_id = f"demo-job-{j + 1}"
            job = {
                'job_id': job_id,
                'job_type': 'shell',
                'payload': {
                    'command': f'echo "Hello from MarlOS job {j + 1}!"'
                },
                'payment': 50.0 + (j * 10),
                'priority': 0.5 + (j * 0.1),
                'deadline': time.time() + 120,
            }
            jobs_submitted.append(job_id)

            # Submit via the first node's P2P broadcast
            submitter = agents[0]
            step(f"Submitting job '{job_id}' (payment={job['payment']} AC, priority={job['priority']:.1f})")
            from agent.p2p.protocol import MessageType
            await submitter.p2p.broadcast_message(
                MessageType.JOB_BROADCAST,
                **job
            )
            await asyncio.sleep(1)

        # ── Step 5: Wait for auction & execution ─────────────────
        banner("STEP 5: Auction & Execution")
        step("Waiting for auctions to complete and jobs to execute...")

        max_wait = 30
        start = time.time()
        while time.time() - start < max_wait:
            total_completed = sum(a.jobs_completed for a in agents)
            total_failed = sum(a.jobs_failed for a in agents)
            info(f"Completed: {total_completed}, Failed: {total_failed}, Elapsed: {time.time() - start:.1f}s")
            if total_completed + total_failed >= num_jobs:
                break
            await asyncio.sleep(1)

        total_completed = sum(a.jobs_completed for a in agents)
        total_failed = sum(a.jobs_failed for a in agents)
        result(f"Jobs completed: {total_completed}/{num_jobs}")
        if total_failed > 0:
            result(f"Jobs failed: {total_failed}")

        # ── Step 6: Show results ─────────────────────────────────
        banner("STEP 6: Final Network State")

        for agent in agents:
            trust = agent.reputation.get_my_trust_score()
            balance = agent.wallet.balance
            completed = agent.jobs_completed
            won = len(agent.won_bids)
            lost = len(agent.lost_bids)

            result(
                f"{agent.node_name}: "
                f"balance={balance:.2f} AC, "
                f"trust={trust:.3f}, "
                f"completed={completed}, "
                f"bids won={won}, lost={lost}"
            )

        # ── Step 7: Show token movement ──────────────────────────
        banner("STEP 7: Token Economy Summary")
        initial_balance = 100.0
        for agent in agents:
            delta = agent.wallet.balance - initial_balance
            direction = "+" if delta >= 0 else ""
            result(f"{agent.node_name}: {initial_balance:.2f} -> {agent.wallet.balance:.2f} AC ({direction}{delta:.2f})")

        # ── Step 8: Show RL learning stats ───────────────────────
        banner("STEP 8: RL & Online Learning")
        for agent in agents:
            stats = agent.online_learner.get_learning_stats()
            result(
                f"{agent.node_name}: "
                f"learning={'ON' if stats['learning_enabled'] else 'OFF'}, "
                f"buffer={stats['buffer_size']} experiences, "
                f"updates={stats['updates_performed']}"
            )

        # ── Summary ──────────────────────────────────────────────
        banner("DEMO COMPLETE")
        step(f"Nodes: {num_nodes}")
        step(f"Jobs submitted: {num_jobs}")
        step(f"Jobs completed: {total_completed}")
        step(f"Jobs failed: {total_failed}")

        all_connected = all(a.p2p.get_peer_count() >= num_nodes - 1 for a in agents)
        step(f"All peers connected: {'YES' if all_connected else 'NO'}")
        step(f"Token economy active: YES")
        step(f"Online learning: ON")

        if total_completed >= num_jobs and all_connected:
            print(f"\n{GREEN}{BOLD}  RESULT: ALL SYSTEMS OPERATIONAL{RESET}\n")
            return 0
        else:
            print(f"\n{YELLOW}{BOLD}  RESULT: PARTIAL SUCCESS (check logs above){RESET}\n")
            return 1

    except Exception as e:
        error(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 2

    finally:
        # ── Cleanup ──────────────────────────────────────────────
        banner("Shutting Down")
        for agent in agents:
            try:
                await agent.stop()
                info(f"{agent.node_name} stopped")
            except Exception as e:
                error(f"Error stopping {agent.node_name}: {e}")

        # Clean up demo data
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir, ignore_errors=True)
            info("Demo data cleaned up")


def main():
    parser = argparse.ArgumentParser(description="MarlOS End-to-End Demo")
    parser.add_argument("--nodes", "-n", type=int, default=3, help="Number of nodes (default: 3)")
    parser.add_argument("--jobs", "-j", type=int, default=2, help="Number of jobs to submit (default: 2)")
    args = parser.parse_args()

    banner("MarlOS End-to-End Demo")
    info(f"Nodes: {args.nodes}, Jobs: {args.jobs}")
    info("This demo starts a local MarlOS network, submits jobs, and shows the full lifecycle.")

    exit_code = asyncio.run(run_demo(num_nodes=args.nodes, num_jobs=args.jobs))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
