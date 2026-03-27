#!/usr/bin/env python3
"""
MarlOS Online Learning Proof
Simulates a node processing 200 jobs with online learning ON.
Shows exploration decay, win rate improvement, and reward increase.

Usage:
    python scripts/online_learning_proof.py
"""

import sys
import os
import random
import argparse
import math
from pathlib import Path
from collections import deque

sys.path.insert(0, str(Path(__file__).parent.parent))


class SimRLNode:
    """Simulates an RL agent that learns from experience."""

    def __init__(self, exploration_rate=0.1, exploration_min=0.01, exploration_decay=0.995):
        self.exploration_rate = exploration_rate
        self.exploration_min = exploration_min
        self.exploration_decay = exploration_decay

        # Learned preference weights (start random)
        self.bid_threshold = 0.5   # When to bid vs defer
        self.capability_weight = 0.3
        self.trust_weight = 0.3
        self.load_weight = 0.2

        # Stats
        self.total_bids = 0
        self.wins = 0
        self.total_reward = 0.0
        self.experiences = 0

        # History for plotting
        self.exploration_history = [exploration_rate]
        self.win_rate_history = []
        self.avg_reward_history = []
        self.bid_threshold_history = [0.5]

        # Rolling windows
        self._recent_wins = deque(maxlen=20)
        self._recent_rewards = deque(maxlen=20)

    def decide(self, job_score: float) -> str:
        """Decide whether to BID, FORWARD, or DEFER."""
        if random.random() < self.exploration_rate:
            # Explore: random action
            return random.choice(["BID", "FORWARD", "DEFER"])
        else:
            # Exploit: use learned threshold
            if job_score > self.bid_threshold:
                return "BID"
            elif job_score > self.bid_threshold * 0.5:
                return "FORWARD"
            else:
                return "DEFER"

    def learn(self, action: str, reward: float, job_score: float):
        """Update policy based on experience."""
        self.experiences += 1

        if action == "BID":
            self.total_bids += 1
            won = reward > 0
            if won:
                self.wins += 1
            self._recent_wins.append(1 if won else 0)
            self._recent_rewards.append(reward)
            self.total_reward += reward

            # Simple policy gradient: adjust threshold based on outcome
            learning_rate = 0.01
            if reward > 0:
                # Good bid: lower threshold slightly to bid more aggressively
                self.bid_threshold -= learning_rate * (job_score - self.bid_threshold) * 0.1
            else:
                # Bad bid: raise threshold slightly
                self.bid_threshold += learning_rate * 0.1

            self.bid_threshold = max(0.1, min(0.9, self.bid_threshold))

        # Decay exploration
        self.exploration_rate = max(
            self.exploration_min,
            self.exploration_rate * self.exploration_decay
        )

        # Record history
        self.exploration_history.append(self.exploration_rate)
        self.bid_threshold_history.append(self.bid_threshold)

        if self._recent_wins:
            self.win_rate_history.append(sum(self._recent_wins) / len(self._recent_wins))
        if self._recent_rewards:
            self.avg_reward_history.append(sum(self._recent_rewards) / len(self._recent_rewards))


def run_simulation(num_jobs=200, seed=42):
    random.seed(seed)
    node = SimRLNode(exploration_rate=0.1, exploration_min=0.01, exploration_decay=0.995)

    # Simulate competing against 2 other nodes
    for i in range(num_jobs):
        # Random job with a score this node would compute
        job_score = random.uniform(0.2, 0.9)

        action = node.decide(job_score)

        if action == "BID":
            # Compete against 2 random opponents
            opponent_scores = [random.uniform(0.3, 0.8) for _ in range(2)]
            my_score = job_score * (0.8 + node.bid_threshold * 0.2)

            if my_score > max(opponent_scores):
                # Won auction
                payment = random.uniform(30, 80)
                success = random.random() < 0.9  # 90% success rate
                reward = payment * 1.2 if success else -payment * 0.25
            else:
                # Lost auction
                reward = -0.5  # Small penalty for wasted bid computation
        elif action == "FORWARD":
            reward = 0.1  # Small reward for useful forwarding
        else:
            reward = 0.0  # Defer = neutral

        node.learn(action, reward, job_score)

    return node


def plot_results(node, output_dir):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed, skipping charts.")
        return

    os.makedirs(output_dir, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1. Exploration rate decay
    ax = axes[0][0]
    ax.plot(node.exploration_history, color="#3498db", linewidth=2)
    ax.set_title("Exploration Rate Decay")
    ax.set_xlabel("Jobs Processed")
    ax.set_ylabel("Exploration Rate")
    ax.set_ylim(0, max(node.exploration_history) * 1.1)
    ax.axhline(y=0.01, color="gray", linestyle="--", alpha=0.5, label="Min (0.01)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 2. Win rate improvement
    ax = axes[0][1]
    if node.win_rate_history:
        ax.plot(node.win_rate_history, color="#2ecc71", linewidth=2)
        # Trend line
        x = range(len(node.win_rate_history))
        z = [sum(node.win_rate_history[max(0, i-30):i+1]) / min(i+1, 30)
             for i in range(len(node.win_rate_history))]
        ax.plot(z, color="#27ae60", linewidth=2, linestyle="--", label="30-job moving avg")
    ax.set_title("Win Rate Over Time")
    ax.set_xlabel("Bid #")
    ax.set_ylabel("Win Rate (rolling 20)")
    ax.set_ylim(0, 1)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 3. Average reward
    ax = axes[1][0]
    if node.avg_reward_history:
        ax.plot(node.avg_reward_history, color="#e67e22", linewidth=2)
    ax.set_title("Average Reward Over Time")
    ax.set_xlabel("Bid #")
    ax.set_ylabel("Avg Reward (rolling 20)")
    ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    ax.grid(True, alpha=0.3)

    # 4. Bid threshold evolution
    ax = axes[1][1]
    ax.plot(node.bid_threshold_history, color="#9b59b6", linewidth=2)
    ax.set_title("Bid Threshold Evolution (Learned)")
    ax.set_xlabel("Jobs Processed")
    ax.set_ylabel("Bid Threshold")
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)

    plt.suptitle("MarlOS: Online Learning Teaches Itself To Bid Better", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "online_learning_proof.png"), dpi=150)
    plt.close()

    print(f"Online learning chart saved to {output_dir}/online_learning_proof.png")


def main():
    parser = argparse.ArgumentParser(description="MarlOS Online Learning Proof")
    parser.add_argument("--jobs", "-j", type=int, default=200)
    parser.add_argument("--output", "-o", default="docs/charts")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print(f"MarlOS Online Learning Proof")
    print(f"{'=' * 40}")
    print(f"Jobs: {args.jobs}")
    print()

    node = run_simulation(args.jobs, args.seed)

    print(f"Results:")
    print(f"  Total bids: {node.total_bids}")
    print(f"  Wins: {node.wins}")
    print(f"  Win rate: {node.wins/node.total_bids:.1%}" if node.total_bids else "  No bids placed")
    print(f"  Total reward: {node.total_reward:.1f}")
    print(f"  Final exploration: {node.exploration_rate:.4f}")
    print(f"  Final bid threshold: {node.bid_threshold:.3f}")
    print(f"  Experiences: {node.experiences}")

    # Show early vs late performance
    if len(node.win_rate_history) > 40:
        early = sum(node.win_rate_history[:20]) / 20
        late = sum(node.win_rate_history[-20:]) / 20
        print(f"\n  Early win rate (first 20): {early:.1%}")
        print(f"  Late win rate (last 20):   {late:.1%}")
        if late > early:
            print(f"  Improvement: +{(late-early)*100:.1f}pp")

    plot_results(node, args.output)


if __name__ == "__main__":
    main()
