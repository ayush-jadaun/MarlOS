"""Tests for the economic simulation."""

import pytest
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.economic_simulation import EconomicSimulator, gini_coefficient


class TestGiniCoefficient:
    def test_perfect_equality(self):
        assert gini_coefficient([100, 100, 100, 100]) == 0.0

    def test_total_inequality(self):
        # One person has everything
        g = gini_coefficient([0, 0, 0, 1000])
        assert g > 0.7

    def test_moderate_inequality(self):
        g = gini_coefficient([50, 100, 150, 200])
        assert 0.0 < g < 0.5

    def test_empty(self):
        assert gini_coefficient([]) == 0.0

    def test_all_zeros(self):
        assert gini_coefficient([0, 0, 0]) == 0.0


class TestEconomicSimulator:
    def test_simulator_runs(self):
        random.seed(42)
        sim = EconomicSimulator(num_nodes=10, num_jobs=50, fairness_enabled=True)
        sim.run()
        results = sim.get_results()
        assert "final_gini" in results
        assert "final_balances" in results
        assert len(results["final_balances"]) == 10

    def test_fairness_improves_participation(self):
        """With fairness, more nodes should participate."""
        random.seed(42)
        sim_fair = EconomicSimulator(num_nodes=20, num_jobs=200, fairness_enabled=True)
        sim_fair.run()
        fair_results = sim_fair.get_results()

        random.seed(42)
        sim_unfair = EconomicSimulator(num_nodes=20, num_jobs=200, fairness_enabled=False)
        sim_unfair.run()
        unfair_results = sim_unfair.get_results()

        assert fair_results["participation_rate"] >= unfair_results["participation_rate"]

    def test_fairness_reduces_gini(self):
        """With fairness, Gini should be lower (more equal)."""
        random.seed(42)
        sim_fair = EconomicSimulator(num_nodes=30, num_jobs=300, fairness_enabled=True)
        sim_fair.run()

        random.seed(42)
        sim_unfair = EconomicSimulator(num_nodes=30, num_jobs=300, fairness_enabled=False)
        sim_unfair.run()

        assert sim_fair.get_results()["final_gini"] <= sim_unfair.get_results()["final_gini"]

    def test_no_node_goes_bankrupt_with_fairness(self):
        """With fairness (UBI), no node should drop below starting balance too far."""
        random.seed(42)
        sim = EconomicSimulator(num_nodes=20, num_jobs=200, fairness_enabled=True)
        sim.run()
        results = sim.get_results()
        # No node should be at 0
        assert all(b > 0 for b in results["final_balances"])

    def test_gini_history_tracked(self):
        random.seed(42)
        sim = EconomicSimulator(num_nodes=10, num_jobs=100, fairness_enabled=True)
        sim.run()
        results = sim.get_results()
        assert len(results["gini_history"]) > 0

    def test_ubi_distribution(self):
        """UBI should be distributed periodically."""
        random.seed(42)
        sim = EconomicSimulator(num_nodes=10, num_jobs=100, fairness_enabled=True)
        sim.run()
        # Tax pool should have been partially distributed
        # (can't be exact since it depends on simulation dynamics)
        results = sim.get_results()
        assert len(results["tax_revenue_history"]) > 0

    def test_large_simulation(self):
        """Full-scale simulation should complete without errors."""
        random.seed(42)
        sim = EconomicSimulator(num_nodes=100, num_jobs=1000, fairness_enabled=True)
        sim.run()
        results = sim.get_results()
        assert len(results["final_balances"]) == 100
        assert results["final_gini"] < 1.0
        assert results["participation_rate"] > 0.5  # Majority participates
