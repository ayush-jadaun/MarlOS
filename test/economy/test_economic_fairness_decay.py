""" Test Suite for Trust Decay Mechanism (Commit 7) """

import pytest
import time
import sys
import os

# Adjust path to find the fairness module (essential for local testing setup)
# This assumes the TrustDecay implementation is located up one directory relative to the test file.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the TrustDecay class
# NOTE: This import assumes the TrustDecay class is defined in agent.economy.fairness
from agent.economy.fairness import TrustDecay


class TestTrustDecay:
    """Tests the time-based decay of a node's trust score."""

    # Set constants for the simulation (seconds in a day)
    SECONDS_IN_DAY = 86400.0

    def test_decay_applies_over_multiple_days(self):
        """Verifies trust decays linearly based on the time elapsed."""
        DECAY_RATE = 0.10  # 10% decay per day
        MIN_TRUST = 0.1
        decay = TrustDecay(decay_rate=DECAY_RATE, min_trust=MIN_TRUST)
        node_id = 'lazy-node'
        
        initial_trust = 0.8
        days_elapsed = 5.0
        
        # 1. Simulate setting the last decay time 5 days ago
        decay.last_decay[node_id] = time.time() - (days_elapsed * self.SECONDS_IN_DAY)

        # 2. Apply decay
        new_trust = decay.apply_decay(node_id, initial_trust)
        
        # Expected decay: 0.10 * 5 days = 0.50
        expected_trust = initial_trust - 0.50
        
        # Assertions
        assert new_trust == pytest.approx(expected_trust, abs=0.001)
        assert new_trust < initial_trust
        print(f"\n[Test 1] Trust decayed from {initial_trust:.2f} to {new_trust:.3f} over {days_elapsed} days.")

    def test_trust_never_falls_below_minimum(self):
        """Verifies trust hits the defined minimum floor (0.2 in this simulation)."""
        DECAY_RATE = 0.05  # 5% decay per day
        MIN_TRUST = 0.2
        decay = TrustDecay(decay_rate=DECAY_RATE, min_trust=MIN_TRUST)
        node_id = 'very-inactive-node'
        
        initial_trust = 0.3
        # 10 days elapsed results in 0.50 decay, pushing trust below 0.2 MIN_TRUST
        days_elapsed = 10.0 
        
        # Simulate time passing
        decay.last_decay[node_id] = time.time() - (days_elapsed * self.SECONDS_IN_DAY)

        # Apply decay
        new_trust = decay.apply_decay(node_id, initial_trust)
        
        # Assertions
        assert new_trust == MIN_TRUST
        print(f"[Test 2] Trust hit minimum floor: {new_trust:.2f}")

    def test_no_decay_if_time_hasnt_passed(self):
        """Verifies no decay occurs if the last update was recent or instantaneous (FIXED for precision)."""
        DECAY_RATE = 0.10
        decay = TrustDecay(decay_rate=DECAY_RATE, min_trust=0.1)
        node_id = 'active-node'
        
        initial_trust = 0.75
        
        # 1. Set last decay time to NOW
        decay.last_decay[node_id] = time.time()
        
        # 2. Apply decay immediately
        new_trust = decay.apply_decay(node_id, initial_trust)
        
        # FIX: Uses pytest.approx() to allow for microsecond discrepancies, ensuring the test PASSES.
        assert new_trust == pytest.approx(initial_trust) 
        print(f"[Test 3] Active node trust remains: {new_trust:.2f}")

# Run the tests directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])