""" Economic Fairness Engine - Research-Level Innovation
Implements novel mechanisms to prevent monopolization and ensure fair resource distribution

INNOVATIONS:
1. Progressive Taxation & Universal Basic Income (UBI) - IMPLEMENTED
2. Diversity Quotas & Affirmative Action Bidding - STUB
3. Trust Decay with Activity Rewards - STUB
4. Job Complexity Analysis for Fair Compensation - STUB
5. Proof of Work Verification
6. Cooperative Rewards for Collaboration
7. Wealth Cap & Redistribution
8. Gini Coefficient for Inequality Measurement
"""
import time
import math
from typing import Dict, List, Tuple, Optional
from collections import deque, defaultdict
from dataclasses import dataclass
from agent.schema.schema import JobDistributionStats # Original external import


# Placeholder class definition (assuming JobDistributionStats is defined here for brevity)
@dataclass
class JobDistributionStats:
    node_id: str
    jobs_won: int = 0
    jobs_lost: int = 0
    total_earnings: float = 0.0
    last_win_time: float = 0.0
    win_rate: float = 0.0


class ProgressiveTaxation:
    """
    Progressive taxation system - rich nodes pay higher tax rates

    INNOVATION: Prevents wealth monopolization through graduated tax brackets.
    This is deliberately simplified (not marginal) for network efficiency.
    """

    def __init__(self):
        # Tax brackets (wealth -> tax_rate)
        self.tax_brackets = [
            (0, 0.00),          # 0-100 AC: 0%
            (100.0001, 0.05),   # 100-500 AC: 5% (Fixed boundary issue)
            (500, 0.10),        # 500-1000 AC: 10%
            (1000, 0.15),       # 1000-2000 AC: 15%
            (2000, 0.20),       # 2000-5000 AC: 20%
            (5000, 0.25),       # 5000-10000 AC: 25%
            (10000, 0.30),      # 10000+ AC: 30%
        ]
        
        # Tax revenue pool (for UBI). Initialized to 0.0, will accumulate.
        self.tax_revenue_pool = 0.0

    def calculate_tax(self, wealth: float, earnings: float) -> float:
        """Calculate tax on earnings based on total wealth"""
        tax_rate = 0.0
        for threshold, rate in reversed(self.tax_brackets):
            if wealth >= threshold:
                tax_rate = rate
                break

        tax = earnings * tax_rate
        self.tax_revenue_pool += tax
        return tax

    def get_tax_rate(self, wealth: float) -> float:
        """Get tax rate for given wealth level (Helper for logging/display)."""
        for threshold, rate in reversed(self.tax_brackets):
            if wealth >= threshold:
                return rate
        return 0.0


class UniversalBasicIncome:
    """
    Universal Basic Income (UBI) system

    INNOVATION: Every active node gets baseline income, preventing starvation
    """

    def __init__(self, ubi_amount: float = 5.0, activity_window: float = 3600.0):
        """
        Args:
            ubi_amount: Base UBI per distribution period
            activity_window: Time window to be considered active (seconds)
        """
        self.ubi_amount = ubi_amount
        self.activity_window = activity_window

        # Track last UBI distribution time per node
        self.last_ubi_distribution: Dict[str, float] = {}

        # Track node activity (last seen time)
        self.node_activity: Dict[str, float] = {}

    def record_activity(self, node_id: str):
        """Record that a node is active"""
        self.node_activity[node_id] = time.time()

    def is_eligible_for_ubi(self, node_id: str) -> bool:
        """Check if node is eligible for UBI"""
        current_time = time.time()

        # Must have been active recently
        last_active = self.node_activity.get(node_id, 0)
        if current_time - last_active > self.activity_window:
            return False

        # Must not have received UBI too recently (once per hour)
        last_ubi = self.last_ubi_distribution.get(node_id, 0)
        if current_time - last_ubi < 3600:  # 1 hour cooldown
            return False

        return True

    def distribute_ubi(self, node_id: str, funding_pool: float) -> Tuple[float, float]:
        """
        Distribute UBI to node

        Returns:
            (ubi_amount, remaining_pool)
        """
        if not self.is_eligible_for_ubi(node_id):
            return 0.0, funding_pool

        # Calculate UBI amount (min of ubi_amount or available pool)
        ubi = min(self.ubi_amount, funding_pool)

        if ubi > 0:
            self.last_ubi_distribution[node_id] = time.time()
            remaining_pool = funding_pool - ubi
            return ubi, remaining_pool

        return 0.0, funding_pool


class DiversityQuotas:
    """Diversity quotas for fair job distribution (Commit 1 Stub)"""
    def __init__(self, window_size: int = 100, max_share: float = 0.30):
        self.window_size = window_size
        self.max_share = max_share
        self.recent_winners: deque = deque(maxlen=window_size)
        self.node_stats: Dict[str, JobDistributionStats] = {}

    def record_job_outcome(self, job_id: str, winner_id: str, losers: List[str], earnings: float): pass
    def calculate_diversity_factor(self, node_id: str) -> float: pass
    def calculate_affirmative_action_bonus(self, node_id: str) -> float: pass
    def calculate_gini_coefficient(self) -> float: pass


class TrustDecay:
    """Trust decay system - trust naturally decays over time (Commit 1 Stub)"""
    def __init__(self, decay_rate: float = 0.01, min_trust: float = 0.1):
        self.decay_rate = decay_rate
        self.min_trust = min_trust
        self.last_decay: Dict[str, float] = {}

    def apply_decay(self, node_id: str, current_trust: float) -> float: pass


class JobComplexityAnalyzer:
    """Analyzes job complexity for fair compensation (Commit 1 Stub)"""
    def __init__(self):
        self.job_type_multipliers = {}

    def analyze_complexity(self, job: dict) -> float: pass


class ProofOfWorkVerification:
    """Proof of work verification system (Commit 1 Stub)"""
    def __init__(self, verification_probability: float = 0.3):
        self.verification_probability = verification_probability
        self.pending_verifications: Dict[str, dict] = {}

    def requires_verification(self, job: dict) -> bool: pass
    def create_verification_challenge(self, job_id: str, result: dict) -> dict: pass
    def record_verification(self, job_id: str, verifier_id: str, verdict: bool): pass
    def get_consensus_verdict(self, job_id: str, min_verifiers: int = 2) -> Optional[bool]: pass
    def _hash_result(self, result: dict) -> str: pass


class CooperativeRewards:
    """Rewards for cooperative behavior (Commit 1 Stub)"""
    def __init__(self):
        self.verifications_performed: Dict[str, int] = defaultdict(int)
        self.help_provided: Dict[str, int] = defaultdict(int)

    def record_verification(self, verifier_id: str): pass
    def calculate_cooperative_bonus(self, node_id: str) -> float: pass


class EconomicFairnessEngine:
    """Master fairness engine - coordinates all fairness mechanisms (Commit 1 Stub)"""

    def __init__(self):
        self.taxation = ProgressiveTaxation()
        self.ubi = UniversalBasicIncome(ubi_amount=5.0)
        self.diversity = DiversityQuotas(window_size=100, max_share=0.30)
        self.trust_decay = TrustDecay(decay_rate=0.01)
        self.complexity = JobComplexityAnalyzer()
        self.verification = ProofOfWorkVerification(verification_probability=0.3)
        self.cooperation = CooperativeRewards()

    def calculate_fair_bid_score(self, base_score: float, node_id: str, trust_score: float) -> float: pass
    def calculate_fair_payment(self, base_payment: float, job: dict, node_id: str, wealth: float, completion_time: float) -> Tuple[float, float, str]: pass
    def distribute_ubi_if_eligible(self, node_id: str) -> float: pass
    def get_gini_coefficient(self) -> float: pass
    def get_fairness_metrics(self) -> dict: pass