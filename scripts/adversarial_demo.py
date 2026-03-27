#!/usr/bin/env python3
"""
MarlOS Adversarial Resistance Demo
Simulates honest + malicious nodes. Shows trust system detecting and
quarantining bad actors. Generates trust score charts.

Usage:
    python scripts/adversarial_demo.py
    python scripts/adversarial_demo.py --honest 10 --malicious 3 --jobs 100
"""

import sys
import os
import random
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class SimNode:
    def __init__(self, node_id, is_malicious=False):
        self.node_id = node_id
        self.is_malicious = is_malicious
        self.trust = 0.5
        self.jobs_assigned = 0
        self.jobs_completed = 0
        self.jobs_failed = 0
        self.quarantined = False
        self.trust_history = [0.5]

    @property
    def label(self):
        return f"{'MAL' if self.is_malicious else 'OK'}-{self.node_id}"


class AdversarialSimulator:
    def __init__(self, num_honest=10, num_malicious=3, num_jobs=100):
        self.num_jobs = num_jobs
        self.quarantine_threshold = 0.2

        # Trust rewards/penalties (from trust config)
        self.success_reward = 0.02
        self.failure_penalty = 0.05
        self.malicious_penalty = 0.50

        self.nodes = []
        for i in range(num_honest):
            self.nodes.append(SimNode(f"honest-{i+1}", is_malicious=False))
        for i in range(num_malicious):
            self.nodes.append(SimNode(f"mal-{i+1}", is_malicious=True))

        random.shuffle(self.nodes)

    def run(self):
        for job_idx in range(self.num_jobs):
            # Pick a random non-quarantined node
            eligible = [n for n in self.nodes if not n.quarantined]
            if not eligible:
                break

            winner = random.choice(eligible)
            winner.jobs_assigned += 1

            if winner.is_malicious:
                # Malicious behavior: 80% chance of failure/garbage
                if random.random() < 0.8:
                    winner.jobs_failed += 1
                    winner.trust = max(0.0, winner.trust - self.failure_penalty)

                    # 30% chance of being caught as malicious (harsher penalty)
                    if random.random() < 0.3:
                        winner.trust = max(0.0, winner.trust - self.malicious_penalty)
                else:
                    # Occasionally succeed to avoid detection
                    winner.jobs_completed += 1
                    winner.trust = min(1.0, winner.trust + self.success_reward)
            else:
                # Honest: 95% success rate
                if random.random() < 0.95:
                    winner.jobs_completed += 1
                    winner.trust = min(1.0, winner.trust + self.success_reward)
                else:
                    winner.jobs_failed += 1
                    winner.trust = max(0.0, winner.trust - self.failure_penalty)

            # Check quarantine
            if winner.trust < self.quarantine_threshold and not winner.quarantined:
                winner.quarantined = True
                print(f"  [QUARANTINE] {winner.label} quarantined at job {job_idx+1} (trust={winner.trust:.3f})")

            # Record trust for all nodes
            for node in self.nodes:
                node.trust_history.append(node.trust)

    def get_results(self):
        honest = [n for n in self.nodes if not n.is_malicious]
        malicious = [n for n in self.nodes if n.is_malicious]

        return {
            "honest_nodes": [{
                "id": n.node_id,
                "trust": n.trust,
                "quarantined": n.quarantined,
                "completed": n.jobs_completed,
                "failed": n.jobs_failed,
                "history": n.trust_history,
            } for n in honest],
            "malicious_nodes": [{
                "id": n.node_id,
                "trust": n.trust,
                "quarantined": n.quarantined,
                "completed": n.jobs_completed,
                "failed": n.jobs_failed,
                "history": n.trust_history,
            } for n in malicious],
            "all_malicious_quarantined": all(n.quarantined for n in malicious),
            "honest_quarantined": sum(1 for n in honest if n.quarantined),
            "detection_rate": sum(1 for n in malicious if n.quarantined) / len(malicious) if malicious else 0,
        }


def plot_results(results, output_dir):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed, skipping charts.")
        return

    os.makedirs(output_dir, exist_ok=True)

    # Trust scores over time
    fig, ax = plt.subplots(figsize=(12, 6))

    for node in results["honest_nodes"]:
        ax.plot(node["history"], color="#2ecc71", alpha=0.4, linewidth=1)
    for node in results["malicious_nodes"]:
        ax.plot(node["history"], color="#e74c3c", linewidth=2,
                label=f"Malicious: {node['id']}" if node == results["malicious_nodes"][0] else "")

    # Quarantine line
    ax.axhline(y=0.2, color="orange", linestyle="--", linewidth=1.5, label="Quarantine threshold (0.2)")

    ax.set_xlabel("Jobs Processed")
    ax.set_ylabel("Trust Score")
    ax.set_title("Trust Scores Over Time: Honest (green) vs Malicious (red)")
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc="lower left")
    ax.grid(True, alpha=0.3)

    # Add honest label manually
    ax.plot([], [], color="#2ecc71", linewidth=2, label="Honest nodes")
    ax.legend(loc="lower left")

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "adversarial_trust.png"), dpi=150)
    plt.close()

    # Final trust bar chart
    fig, ax = plt.subplots(figsize=(12, 5))

    all_nodes = results["honest_nodes"] + results["malicious_nodes"]
    names = [f"{'MAL ' if n in results['malicious_nodes'] else ''}{n['id']}" for n in all_nodes]
    trusts = [n["trust"] for n in all_nodes]
    colors = ["#e74c3c" if n in results["malicious_nodes"] else "#2ecc71" for n in all_nodes]

    bars = ax.bar(range(len(names)), trusts, color=colors)
    ax.axhline(y=0.2, color="orange", linestyle="--", linewidth=1.5, label="Quarantine threshold")
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Final Trust Score")
    ax.set_title("Final Trust Scores: Malicious Nodes Detected and Quarantined")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "adversarial_final_trust.png"), dpi=150)
    plt.close()

    print(f"Adversarial charts saved to {output_dir}/")


def main():
    parser = argparse.ArgumentParser(description="MarlOS Adversarial Resistance Demo")
    parser.add_argument("--honest", type=int, default=10)
    parser.add_argument("--malicious", type=int, default=3)
    parser.add_argument("--jobs", type=int, default=100)
    parser.add_argument("--output", "-o", default="docs/charts")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    print(f"MarlOS Adversarial Resistance Demo")
    print(f"{'=' * 45}")
    print(f"Honest nodes: {args.honest}")
    print(f"Malicious nodes: {args.malicious}")
    print(f"Total jobs: {args.jobs}")
    print()

    sim = AdversarialSimulator(args.honest, args.malicious, args.jobs)
    sim.run()
    results = sim.get_results()

    print(f"\n{'=' * 45}")
    print(f"  Results")
    print(f"{'=' * 45}")

    print(f"\n  Honest nodes:")
    for n in results["honest_nodes"]:
        q = " [QUARANTINED]" if n["quarantined"] else ""
        print(f"    {n['id']}: trust={n['trust']:.3f}, completed={n['completed']}, failed={n['failed']}{q}")

    print(f"\n  Malicious nodes:")
    for n in results["malicious_nodes"]:
        q = " [QUARANTINED]" if n["quarantined"] else " [STILL ACTIVE!]"
        print(f"    {n['id']}: trust={n['trust']:.3f}, completed={n['completed']}, failed={n['failed']}{q}")

    print(f"\n  Detection rate: {results['detection_rate']:.0%}")
    print(f"  All malicious quarantined: {'YES' if results['all_malicious_quarantined'] else 'NO'}")
    print(f"  Honest falsely quarantined: {results['honest_quarantined']}")
    print(f"{'=' * 45}")

    if results['all_malicious_quarantined'] and results['honest_quarantined'] == 0:
        print(f"  RESULT: PERFECT DETECTION - Zero false positives")
    elif results['detection_rate'] > 0.8:
        print(f"  RESULT: STRONG DETECTION")
    else:
        print(f"  RESULT: NEEDS IMPROVEMENT")
    print()

    plot_results(results, args.output)


if __name__ == "__main__":
    main()
