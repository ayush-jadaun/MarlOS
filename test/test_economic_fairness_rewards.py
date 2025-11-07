import pytest
import sys
import os
from collections import defaultdict

# Adjust path to find the fairness module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the CooperativeRewards class (assuming Commit 9 implementation is ready)
from agent.economy.fairness import CooperativeRewards


class TestCooperativeRewards:
    """Tests the system for incentivizing and rewarding cooperative behavior."""

    # Define the expected tiered rewards based on the implementation structure
    TIERED_REWARDS = [
        (0, 1.00),     # Default: 0 verifications
        (1, 1.05),     # Tier 1: > 0 verifications
        (6, 1.10),     # Tier 2: > 5 verifications
        (21, 1.15),    # Tier 3: > 20 verifications
        (51, 1.20),    # Tier 4: > 50 verifications (Maximum boost)
    ]

    def test_new_node_gets_no_bonus(self):
        """Verifies a node with zero activity gets the neutral (1.0x) factor."""
        coop = CooperativeRewards()
        node_id = 'new-node'
        
        bonus_factor = coop.calculate_cooperative_bonus(node_id)
        
        assert bonus_factor == 1.00
        print(f"\n[Test 1] New Node Bonus: {bonus_factor:.2f}x (Neutral)")

    @pytest.mark.parametrize("verifications, expected_factor", TIERED_REWARDS)
    def test_tiered_rewards_apply_correctly(self, verifications, expected_factor):
        """Verifies that the multiplicative bonus increases at each defined tier."""
        coop = CooperativeRewards()
        node_id = 'verifier-node'
        
        # Simulate recording the required number of verifications *just above the threshold*
        # (Subtract 1 to account for the first iteration, and ensure we test the boundary)
        
        # For the 0-verification case, we skip the loop
        if verifications > 0:
            for i in range(verifications):
                coop.record_verification(node_id)
        
        bonus_factor = coop.calculate_cooperative_bonus(node_id)
        
        # Check against the expected factor (1.05x, 1.10x, 1.15x, 1.20x)
        assert bonus_factor == pytest.approx(expected_factor, abs=0.001)
        print(f"[Test 2] Verifications: {verifications} -> Factor: {bonus_factor:.2f}x")

    def test_max_bonus_is_enforced(self):
        """Verifies the bonus is capped at 1.20x even for excessive activity."""
        coop = CooperativeRewards()
        node_id = 'super-helpful-node'
        
        # Simulate 1000 verifications (far above the max tier of 50)
        for i in range(1000):
            coop.record_verification(node_id)
            
        bonus_factor = coop.calculate_cooperative_bonus(node_id)
        
        # Assertions
        assert bonus_factor == 1.20
        assert coop.verifications_performed[node_id] == 1000
        print(f"[Test 3] Max Bonus Cap: {bonus_factor:.2f}x")

# Run the tests directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])