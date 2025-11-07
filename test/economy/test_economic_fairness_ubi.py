import pytest
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent.economy.fairness import UniversalBasicIncome 


class TestResourceStarvationPrevention:
    """Tests the Universal Basic Income (UBI) system for eligibility and distribution."""

    def test_ubi_prevents_starvation_and_distributes_correctly(self):
        """Test UBI provides baseline income when eligible and reduces the pool."""
        # UBI amount is 5.0 AC, activity window is 1 hour (3600.0s)
        ubi = UniversalBasicIncome(ubi_amount=5.0, activity_window=3600.0)
        
        initial_pool = 1000.0
        node_id = 'poor-node'

        # 1. Record activity to make the node ELIGIBLE
        ubi.record_activity(node_id)
        
        # 2. Distribute UBI
        ubi_amount, remaining_pool = ubi.distribute_ubi(node_id, funding_pool=initial_pool)

        # Assertions
        assert ubi_amount == 5.0              # UBI amount should match the default
        assert remaining_pool == 995.0        # Pool should be reduced by 5.0
        assert ubi.last_ubi_distribution.get(node_id) is not None # Distribution time should be recorded

        print(f"\n[UBI Check 1] Distributed: {ubi_amount:.2f} AC | Pool: {remaining_pool:.2f} AC")

    def test_ubi_requires_activity(self):
        """Test inactive nodes are ineligible for UBI."""
        # Use a short activity window (10.0s) for easy simulation
        ubi = UniversalBasicIncome(ubi_amount=5.0, activity_window=10.0)  
        node_id = 'inactive-node'
        initial_pool = 1000.0

        # 1. Record activity in the PAST (20s ago > 10s window)
        ubi.node_activity[node_id] = time.time() - 20.0 

        # 2. Try to get UBI
        is_eligible = ubi.is_eligible_for_ubi(node_id)
        ubi_amount, remaining_pool = ubi.distribute_ubi(node_id, funding_pool=initial_pool)

        # Assertions
        assert is_eligible is False             # Node should be ineligible
        assert ubi_amount == 0.0                # No UBI should be distributed
        assert remaining_pool == initial_pool   # Pool should be unchanged

        print(f"[UBI Check 2] Ineligible (Inactive). UBI received: {ubi_amount:.2f} AC")

    def test_ubi_enforces_cooldown(self):
        """Test nodes cannot receive UBI if they received it too recently (3600s cooldown)."""
        ubi = UniversalBasicIncome(ubi_amount=5.0, activity_window=3600.0)
        node_id = 'recent-receiver'
        initial_pool = 1000.0

        # 1. Mark node as recently active (5 minutes ago)
        ubi.record_activity(node_id)
        
        # 2. Mark node as having received UBI recently (5 minutes ago = 300s)
        ubi.last_ubi_distribution[node_id] = time.time() - 300 

        # 3. Try to get UBI again
        is_eligible = ubi.is_eligible_for_ubi(node_id)
        ubi_amount, remaining_pool = ubi.distribute_ubi(node_id, funding_pool=initial_pool)
        
        # Assertions
        assert is_eligible is False             # Cooldown should prevent eligibility
        assert ubi_amount == 0.0
        
        print(f"[UBI Check 3] Ineligible (Cooldown). UBI received: {ubi_amount:.2f} AC")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])