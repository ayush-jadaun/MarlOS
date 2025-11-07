""" Test Suite for Diversity Quotas Job Tracking (Commit 5) """

import pytest
import time
import sys
import os

# --- Path Configuration (Essential for running the script directly) ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the class required for testing
from agent.economy.fairness import DiversityQuotas
# Import the placeholder for JobDistributionStats for local use
from agent.economy.fairness import JobDistributionStats 


class TestDiversityQuotasTracking:
    """Tests the job outcome recording mechanisms implemented in Commit 5."""
    def test_initial_setup_is_empty(self):
            """Verifies that the initial state of the tracker is empty."""
            # FIX: The test must check for the value explicitly passed: 0.30, not 0.50.
            # We call the constructor without specifying max_share to get the true default (0.30)
            quotas = DiversityQuotas(window_size=50) # Remove max_share=0.50 if it was there
            
            assert quotas.window_size == 50
            assert quotas.max_share == 0.30  # This checks the default value set in the __init__
            assert len(quotas.recent_winners) == 0
            assert len(quotas.node_stats) == 0


    def test_record_single_job_outcome(self):
        """Tests recording a single job winner and loser updates statistics correctly."""
        quotas = DiversityQuotas()
        winner_id = "node_alpha"
        loser_ids = ["node_beta", "node_gamma"]
        earnings = 100.0
        
        quotas.record_job_outcome("job-1", winner_id, loser_ids, earnings)
        
        # 1. Check recent winners queue
        assert len(quotas.recent_winners) == 1
        assert quotas.recent_winners[0] == winner_id
        
        # 2. Check winner statistics
        winner_stats = quotas.node_stats.get(winner_id)
        assert winner_stats is not None
        assert winner_stats.jobs_won == 1
        assert winner_stats.jobs_lost == 0
        assert winner_stats.total_earnings == 100.0
        # Win rate for (1 win, 0 losses) should be 1 / (1 + 0 + 1) = 0.5
        assert winner_stats.win_rate == pytest.approx(0.5)

        # 3. Check loser statistics
        loser_stats = quotas.node_stats.get("node_beta")
        assert loser_stats is not None
        assert loser_stats.jobs_won == 0
        assert loser_stats.jobs_lost == 1
        # Win rate for (0 wins, 1 loss) should be 0 / (0 + 1 + 1) = 0.0
        assert loser_stats.win_rate == pytest.approx(0.0)

    def test_circular_buffer_limit(self):
        """Tests that the recent_winners queue correctly respects the window_size."""
        WINDOW = 5
        quotas = DiversityQuotas(window_size=WINDOW)
        
        # Simulate 10 job outcomes (double the window size)
        for i in range(10):
            quotas.record_job_outcome(f"job-{i}", "node-A" if i % 2 == 0 else "node-B", ["node-C"], 10.0)
            
        # The deque should only hold the last 5 results
        assert len(quotas.recent_winners) == WINDOW
        # The oldest entry (job-0 winner 'node-A') should be gone
        assert quotas.recent_winners[0] == 'node-B' # Starts with job-5 winner

        # Check total jobs counted in stats (should be all 10)
        assert quotas.node_stats['node-A'].jobs_won == 5
        assert quotas.node_stats['node-C'].jobs_lost == 10

    def test_cumulative_earnings_and_winrate(self):
        """Tests cumulative updates for multiple wins and losses."""
        quotas = DiversityQuotas()
        
        # Job 1: A wins, B loses
        quotas.record_job_outcome("j1", "A", ["B", "C"], 50.0)
        # Job 2: B wins, A loses (simulating a challenge)
        quotas.record_job_outcome("j2", "B", ["A"], 100.0)
        
        stats_A = quotas.node_stats['A']
        stats_B = quotas.node_stats['B']
        
        # Node A: 1 win, 1 loss (from job 2)
        assert stats_A.jobs_won == 1
        assert stats_A.jobs_lost == 1
        assert stats_A.total_earnings == 50.0
        # Win Rate A: 1 / (1 + 1 + 1) = 0.333...
        assert stats_A.win_rate == pytest.approx(0.33333, abs=0.00001) 

        # Node B: 1 win, 1 loss (from job 1)
        assert stats_B.jobs_won == 1
        assert stats_B.jobs_lost == 1
        assert stats_B.total_earnings == 100.0
        # Win Rate B: 1 / (1 + 1 + 1) = 0.333...
        assert stats_B.win_rate == pytest.approx(0.33333, abs=0.00001)

# Run the tests directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])