""" Test Suite for Proof of Work Verification (Commit 8) """

import pytest
import time
import sys
import os
import random
import json
import hashlib

# Adjust path to find the fairness module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the ProofOfWorkVerification class (assuming Commit 8 implementation is ready)
from agent.economy.fairness import ProofOfWorkVerification


class TestProofOfWorkVerification:
    """Tests the mechanisms for creating and achieving consensus on job verification."""

    def test_high_value_jobs_always_require_verification(self):
        """Verifies that jobs above the $200 payment threshold always require verification."""
        # Set random sampling low, but high-value jobs should override it.
        pov = ProofOfWorkVerification(verification_probability=0.01) 
        
        high_value_job = {'payment': 500.0}
        
        # Test 100 times to ensure it's not random
        verifications = sum(1 for _ in range(100) if pov.requires_verification(high_value_job))
        
        assert verifications == 100
        print(f"\n[Test 1] High-value job verification rate: {verifications}% (100% required)")

    def test_low_value_jobs_use_random_sampling(self):
        """Verifies that low-value jobs rely on the configured random probability."""
        PROBABILITY = 0.30  # 30% verification probability
        pov = ProofOfWorkVerification(verification_probability=PROBABILITY)
        
        low_value_job = {'payment': 50.0}
        
        # We need a large sample to check randomness (1000 trials)
        random.seed(42) # Ensure reproducibility of the random sample
        trials = 1000
        verifications = sum(1 for _ in range(trials) if pov.requires_verification(low_value_job))
        
        # Assert the result is statistically close to 30% (within 5%)
        assert verifications / trials == pytest.approx(PROBABILITY, abs=0.05)
        print(f"[Test 2] Low-value job verification rate: {verifications/trials:.3f} (Statistically near {PROBABILITY})")

    def test_consensus_requires_minimum_and_majority(self):
        """Verifies that verification requires both a minimum count and a majority vote."""
        pov = ProofOfWorkVerification()
        job_id = 'verify-job-1'
        result_data = {'output': 'successful', 'status': 'completed'}
        
        # 1. Create Challenge
        challenge = pov.create_verification_challenge(job_id, result_data)
        
        # 2. Case: Not enough verifiers (min_verifiers=2)
        pov.record_verification(job_id, 'v1', True)
        verdict_incomplete = pov.get_consensus_verdict(job_id, min_verifiers=3) # Require 3, only 1 recorded
        assert verdict_incomplete is None
        
        # 3. Case: Majority Approval
        pov.record_verification(job_id, 'v2', True) # 2 Approvals
        pov.record_verification(job_id, 'v3', False) # 1 Rejection
        verdict_pass = pov.get_consensus_verdict(job_id, min_verifiers=3)
        assert verdict_pass is True
        print(f"[Test 3] Consensus Check: PASS (3 verifiers: 2 approved, 1 rejected)")
        
        # 4. Case: Majority Rejection
        job_id_fail = 'verify-job-2'
        pov.create_verification_challenge(job_id_fail, result_data)
        pov.record_verification(job_id_fail, 'v4', False) # Reject
        pov.record_verification(job_id_fail, 'v5', False) # Reject
        pov.record_verification(job_id_fail, 'v6', True) # Approve
        verdict_fail = pov.get_consensus_verdict(job_id_fail, min_verifiers=3)
        assert verdict_fail is False
        print(f"[Test 4] Consensus Check: FAIL (3 verifiers: 1 approved, 2 rejected)")

# Run the tests directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])