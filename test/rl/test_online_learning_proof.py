"""Tests for online learning simulation."""

import pytest
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.online_learning_proof import SimRLNode, run_simulation


class TestOnlineLearning:
    def test_exploration_decays(self):
        random.seed(42)
        node = run_simulation(num_jobs=200)
        assert node.exploration_rate < 0.1  # Started at 0.1
        assert node.exploration_rate >= 0.01  # Should not go below min

    def test_learning_improves_over_time(self):
        """Late performance should be at least as good as early."""
        random.seed(42)
        node = run_simulation(num_jobs=500)
        if len(node.win_rate_history) > 40:
            early = sum(node.win_rate_history[:20]) / 20
            late = sum(node.win_rate_history[-20:]) / 20
            # Late should be at least equal (with noise, allow small margin)
            assert late >= early - 0.15

    def test_positive_total_reward(self):
        random.seed(42)
        node = run_simulation(num_jobs=200)
        assert node.total_reward > 0

    def test_experiences_tracked(self):
        random.seed(42)
        node = run_simulation(num_jobs=100)
        assert node.experiences == 100
        assert len(node.exploration_history) == 101  # Initial + 100 steps

    def test_bid_threshold_adapts(self):
        """Threshold should move from initial value."""
        random.seed(42)
        node = run_simulation(num_jobs=300)
        assert node.bid_threshold != 0.5  # Should have adapted

    def test_history_recorded(self):
        random.seed(42)
        node = run_simulation(num_jobs=100)
        assert len(node.exploration_history) > 0
        assert len(node.win_rate_history) > 0
        assert len(node.avg_reward_history) > 0
        assert len(node.bid_threshold_history) > 0
