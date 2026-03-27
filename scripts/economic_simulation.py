#!/usr/bin/env python3
"""
MarlOS Economic Simulation
Simulates 100 nodes, 1000 jobs, measures fairness metrics over time.
Compares fairness ON vs OFF. Outputs charts as PNG files.

Usage:
    python scripts/economic_simulation.py
    python scripts/economic_simulation.py --nodes 50 --jobs 500
"""

import sys
import os
import random
import argparse
import math
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))


def gini_coefficient(values):
    """Calculate Gini coefficient (0 = perfect equality, 1 = max inequality)."""
    if not values or all(v == 0 for v in values):
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    total = sum(sorted_vals)
    if total == 0:
        return 0.0
    cumulative = sum((2 * (i + 1) - n - 1) * v for i, v in enumerate(sorted_vals))
    return cumulative / (n * total)


class SimNode:
    """Simulated node in the economy."""
    def __init__(self, node_id: str, capability: float):
        self.node_id = node_id
        self.capability = capability  # 0-1, how good at executing jobs
        self.balance = 100.0
        self.staked = 0.0
        self.jobs_won = 0
        self.jobs_completed = 0
        self.trust = 0.5
        self.lifetime_earned = 0.0


class EconomicSimulator:
    def __init__(self, num_nodes=100, num_jobs=1000, fairness_enabled=True):
        self.num_nodes = num_nodes
        self.num_jobs = num_jobs
        self.fairness_enabled = fairness_enabled

        # Create nodes with varying capabilities
        self.nodes = []
        for i in range(num_nodes):
            # Normal-ish distribution centered around 0.5 — most nodes are competitive
            capability = max(0.1, min(0.95, random.gauss(0.5, 0.15)))
            self.nodes.append(SimNode(f"node-{i+1}", capability))

        # Tax brackets (from fairness.py)
        self.tax_brackets = [
            (0, 0.00), (100, 0.05), (500, 0.10),
            (1000, 0.15), (2000, 0.20), (5000, 0.25), (10000, 0.30),
        ]
        self.tax_pool = 0.0
        self.ubi_interval = 50  # Distribute UBI every 50 jobs

        # Metrics over time
        self.gini_history = []
        self.wealth_snapshots = []
        self.participation_history = []
        self.tax_revenue_history = []

    def get_tax_rate(self, wealth):
        for threshold, rate in reversed(self.tax_brackets):
            if wealth >= threshold:
                return rate
        return 0.0

    def run(self):
        """Run the full simulation."""
        for job_idx in range(self.num_jobs):
            payment = random.uniform(20, 100)
            priority = random.uniform(0.3, 0.9)

            # All nodes "bid" — score based on capability + trust + randomness
            scores = []
            for node in self.nodes:
                if node.balance < 5:  # Can't afford stake
                    scores.append(-1)
                    continue
                base = node.capability * 0.4 + node.trust * 0.2 + random.uniform(0, 0.4)

                # Fairness boost: starving nodes get a boost
                if self.fairness_enabled:
                    if node.jobs_won == 0 and job_idx > 10:
                        base += 0.2  # Affirmative action boost
                    # Low-wealth nodes get a small boost
                    if node.balance < 150:
                        base += 0.1

                scores.append(base)

            # Winner = highest score
            if max(scores) < 0:
                continue  # No one can bid

            winner_idx = scores.index(max(scores))
            winner = self.nodes[winner_idx]

            # Stake
            stake = payment * 0.25
            winner.balance -= stake
            winner.staked += stake

            # Execute (success based on capability)
            success = random.random() < (0.7 + winner.capability * 0.3)

            if success:
                # Return stake + payment + bonus
                earnings = payment * 1.2  # 20% bonus
                winner.staked -= stake
                winner.balance += stake + earnings
                winner.lifetime_earned += earnings
                winner.jobs_completed += 1
                winner.trust = min(1.0, winner.trust + 0.02)

                # Tax
                if self.fairness_enabled:
                    tax_rate = self.get_tax_rate(winner.balance)
                    tax = earnings * tax_rate
                    winner.balance -= tax
                    self.tax_pool += tax
            else:
                # Lose stake
                winner.staked -= stake
                self.tax_pool += stake  # Stake goes to pool
                winner.trust = max(0.0, winner.trust - 0.05)

            winner.jobs_won += 1

            # UBI distribution
            if self.fairness_enabled and (job_idx + 1) % self.ubi_interval == 0:
                self._distribute_ubi()

            # Record metrics periodically
            if (job_idx + 1) % 10 == 0:
                balances = [n.balance for n in self.nodes]
                self.gini_history.append(gini_coefficient(balances))
                self.wealth_snapshots.append(list(balances))

                active = sum(1 for n in self.nodes if n.jobs_won > 0)
                self.participation_history.append(active / self.num_nodes)
                self.tax_revenue_history.append(self.tax_pool)

    def _distribute_ubi(self):
        """Distribute UBI from tax pool to low-wealth nodes."""
        if self.tax_pool < 10:
            return

        # Eligible: nodes below median wealth
        balances = sorted(n.balance for n in self.nodes)
        median = balances[len(balances) // 2]

        eligible = [n for n in self.nodes if n.balance < median]
        if not eligible:
            return

        per_node = min(self.tax_pool * 0.5, self.tax_pool / len(eligible))
        for node in eligible:
            node.balance += per_node
            self.tax_pool -= per_node

    def get_results(self):
        balances = [n.balance for n in self.nodes]
        jobs_won = [n.jobs_won for n in self.nodes]
        return {
            "final_gini": gini_coefficient(balances),
            "final_balances": balances,
            "jobs_won": jobs_won,
            "participation_rate": sum(1 for n in self.nodes if n.jobs_won > 0) / self.num_nodes,
            "gini_history": self.gini_history,
            "participation_history": self.participation_history,
            "tax_revenue_history": self.tax_revenue_history,
            "wealth_snapshots": self.wealth_snapshots,
        }


def plot_results(fair_results, unfair_results, output_dir):
    """Generate comparison charts."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("matplotlib not installed, skipping charts. Install with: pip install matplotlib")
        return

    os.makedirs(output_dir, exist_ok=True)

    # 1. Gini coefficient over time
    fig, ax = plt.subplots(figsize=(10, 5))
    x_fair = range(len(fair_results["gini_history"]))
    x_unfair = range(len(unfair_results["gini_history"]))
    ax.plot(x_fair, fair_results["gini_history"], label="Fairness ON", color="#2ecc71", linewidth=2)
    ax.plot(x_unfair, unfair_results["gini_history"], label="Fairness OFF", color="#e74c3c", linewidth=2)
    ax.set_xlabel("Time (every 10 jobs)")
    ax.set_ylabel("Gini Coefficient")
    ax.set_title("Wealth Inequality Over Time")
    ax.legend()
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "gini_over_time.png"), dpi=150)
    plt.close()

    # 2. Wealth distribution (final)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.hist(fair_results["final_balances"], bins=30, color="#2ecc71", alpha=0.8, edgecolor="white")
    ax1.set_title(f"Fairness ON (Gini={fair_results['final_gini']:.3f})")
    ax1.set_xlabel("Balance (AC)")
    ax1.set_ylabel("Number of Nodes")
    ax1.axvline(np.median(fair_results["final_balances"]), color="black", linestyle="--", label="Median")
    ax1.legend()

    ax2.hist(unfair_results["final_balances"], bins=30, color="#e74c3c", alpha=0.8, edgecolor="white")
    ax2.set_title(f"Fairness OFF (Gini={unfair_results['final_gini']:.3f})")
    ax2.set_xlabel("Balance (AC)")
    ax2.set_ylabel("Number of Nodes")
    ax2.axvline(np.median(unfair_results["final_balances"]), color="black", linestyle="--", label="Median")
    ax2.legend()

    plt.suptitle("Final Wealth Distribution", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "wealth_distribution.png"), dpi=150)
    plt.close()

    # 3. Participation rate over time
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(fair_results["participation_history"], label="Fairness ON", color="#2ecc71", linewidth=2)
    ax.plot(unfair_results["participation_history"], label="Fairness OFF", color="#e74c3c", linewidth=2)
    ax.set_xlabel("Time (every 10 jobs)")
    ax.set_ylabel("Participation Rate")
    ax.set_title("Node Participation Over Time")
    ax.legend()
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "participation.png"), dpi=150)
    plt.close()

    # 4. Jobs won distribution
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.hist(fair_results["jobs_won"], bins=30, color="#2ecc71", alpha=0.8, edgecolor="white")
    ax1.set_title("Fairness ON")
    ax1.set_xlabel("Jobs Won")
    ax1.set_ylabel("Number of Nodes")

    ax2.hist(unfair_results["jobs_won"], bins=30, color="#e74c3c", alpha=0.8, edgecolor="white")
    ax2.set_title("Fairness OFF")
    ax2.set_xlabel("Jobs Won")
    ax2.set_ylabel("Number of Nodes")

    plt.suptitle("Job Distribution Across Nodes", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "job_distribution.png"), dpi=150)
    plt.close()

    print(f"Charts saved to {output_dir}/")


def main():
    parser = argparse.ArgumentParser(description="MarlOS Economic Simulation")
    parser.add_argument("--nodes", "-n", type=int, default=100)
    parser.add_argument("--jobs", "-j", type=int, default=1000)
    parser.add_argument("--output", "-o", default="docs/charts")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print(f"MarlOS Economic Simulation")
    print(f"{'=' * 40}")
    print(f"Nodes: {args.nodes}, Jobs: {args.jobs}")
    print()

    # Run with fairness ON
    random.seed(args.seed)
    print("Running with fairness ON...", end="", flush=True)
    sim_fair = EconomicSimulator(args.nodes, args.jobs, fairness_enabled=True)
    sim_fair.run()
    fair_results = sim_fair.get_results()
    print(" done")

    # Run with fairness OFF
    random.seed(args.seed)
    print("Running with fairness OFF...", end="", flush=True)
    sim_unfair = EconomicSimulator(args.nodes, args.jobs, fairness_enabled=False)
    sim_unfair.run()
    unfair_results = sim_unfair.get_results()
    print(" done")

    # Print comparison
    print(f"\n{'=' * 50}")
    print(f"  Results Comparison")
    print(f"{'=' * 50}")
    print(f"  {'Metric':<30} {'Fair':>8} {'Unfair':>8}")
    print(f"  {'-'*46}")
    print(f"  {'Gini Coefficient':<30} {fair_results['final_gini']:>8.3f} {unfair_results['final_gini']:>8.3f}")
    print(f"  {'Participation Rate':<30} {fair_results['participation_rate']:>7.0%} {unfair_results['participation_rate']:>7.0%}")

    fair_bal = fair_results['final_balances']
    unfair_bal = unfair_results['final_balances']
    print(f"  {'Min Balance':<30} {min(fair_bal):>8.1f} {min(unfair_bal):>8.1f}")
    print(f"  {'Max Balance':<30} {max(fair_bal):>8.1f} {max(unfair_bal):>8.1f}")
    print(f"  {'Median Balance':<30} {sorted(fair_bal)[len(fair_bal)//2]:>8.1f} {sorted(unfair_bal)[len(unfair_bal)//2]:>8.1f}")

    fair_zero = sum(1 for b in fair_bal if b < 10)
    unfair_zero = sum(1 for b in unfair_bal if b < 10)
    print(f"  {'Nodes < 10 AC':<30} {fair_zero:>8} {unfair_zero:>8}")
    print(f"{'=' * 50}")

    if fair_results['final_gini'] < unfair_results['final_gini']:
        print(f"  Fairness reduces inequality by {(1 - fair_results['final_gini']/unfair_results['final_gini'])*100:.0f}%")
    print()

    # Generate charts
    plot_results(fair_results, unfair_results, args.output)


if __name__ == "__main__":
    main()
