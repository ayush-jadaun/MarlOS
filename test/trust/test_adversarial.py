"""Tests for adversarial resistance."""

import pytest
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.adversarial_demo import AdversarialSimulator


class TestAdversarialDetection:
    def test_simulator_runs(self):
        random.seed(42)
        sim = AdversarialSimulator(num_honest=5, num_malicious=2, num_jobs=50)
        sim.run()
        results = sim.get_results()
        assert len(results["honest_nodes"]) == 5
        assert len(results["malicious_nodes"]) == 2

    def test_malicious_detected(self):
        """Malicious nodes should be quarantined."""
        random.seed(42)
        sim = AdversarialSimulator(num_honest=10, num_malicious=3, num_jobs=100)
        sim.run()
        results = sim.get_results()
        assert results["detection_rate"] >= 0.66  # At least 2/3 caught

    def test_honest_not_quarantined(self):
        """Honest nodes should not be falsely quarantined."""
        random.seed(42)
        sim = AdversarialSimulator(num_honest=10, num_malicious=3, num_jobs=100)
        sim.run()
        results = sim.get_results()
        assert results["honest_quarantined"] == 0

    def test_malicious_trust_drops(self):
        """Malicious nodes should have lower trust than honest."""
        random.seed(42)
        sim = AdversarialSimulator(num_honest=5, num_malicious=2, num_jobs=80)
        sim.run()
        results = sim.get_results()

        avg_honest_trust = sum(n["trust"] for n in results["honest_nodes"]) / len(results["honest_nodes"])
        avg_mal_trust = sum(n["trust"] for n in results["malicious_nodes"]) / len(results["malicious_nodes"])
        assert avg_mal_trust < avg_honest_trust

    def test_trust_history_recorded(self):
        random.seed(42)
        sim = AdversarialSimulator(num_honest=3, num_malicious=1, num_jobs=20)
        sim.run()
        results = sim.get_results()
        for node in results["honest_nodes"] + results["malicious_nodes"]:
            assert len(node["history"]) > 1

    def test_large_scale_detection(self):
        """Even with many malicious nodes, detection should work."""
        random.seed(42)
        sim = AdversarialSimulator(num_honest=20, num_malicious=10, num_jobs=300)
        sim.run()
        results = sim.get_results()
        assert results["detection_rate"] >= 0.5
        assert results["honest_quarantined"] == 0
