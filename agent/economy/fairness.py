""" Economic Fairness Engine - Research-Level Innovation
Implements novel mechanisms to prevent monopolization and ensure fair resource distribution

INNOVATIONS:
1. Progressive Taxation & Universal Basic Income (UBI) - IMPLEMENTED (C2 & C3)
2. Diversity Quotas & Affirmative Action Bidding - TRACKING IMPLEMENTED (C5)
3. Trust Decay with Activity Rewards - STUB (C7 pending)
4. Job Complexity Analysis for Fair Compensation - IMPLEMENTED (C4)
5. Proof of Work Verification - STUB
6. Cooperative Rewards for Collaboration - STUB
7. Wealth Cap & Redistribution
8. Gini Coefficient for Inequality Measurement
"""
import time
import math
from typing import Dict, List, Tuple, Optional
from collections import deque, defaultdict
from dataclasses import dataclass
# from agent.schema.schema import JobDistributionStats 


# Placeholder for JobDistributionStats to ensure the file runs independently
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
    (Commit 2 Implementation)
    """

    def __init__(self):
        # Tax brackets (wealth -> tax_rate)
        self.tax_brackets = [
            (0, 0.00),          # 0-100 AC: 0%
            (100.0001, 0.05),   # 100+ AC: 5% (Fixed boundary issue)
            (500, 0.10),        # 500+ AC: 10%
            (1000, 0.15),       # 1000+ AC: 15%
            (2000, 0.20),       # 2000+ AC: 20%
            (5000, 0.25),       # 5000+ AC: 25%
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
    (Commit 3 Implementation)
    """

    def __init__(self, ubi_amount: float = 5.0, activity_window: float = 3600.0):
        self.ubi_amount = ubi_amount
        self.activity_window = activity_window
        self.last_ubi_distribution: Dict[str, float] = {}
        self.node_activity: Dict[str, float] = {}

    def record_activity(self, node_id: str):
        """Record that a node is active"""
        self.node_activity[node_id] = time.time()

    def is_eligible_for_ubi(self, node_id: str) -> bool:
        """Check if node is eligible for UBI"""
        current_time = time.time()
        last_active = self.node_activity.get(node_id, 0)
        if current_time - last_active > self.activity_window:
            return False
        last_ubi = self.last_ubi_distribution.get(node_id, 0)
        if current_time - last_ubi < 3600:  # 1 hour cooldown
            return False
        return True

    def distribute_ubi(self, node_id: str, funding_pool: float) -> Tuple[float, float]:
        """Distribute UBI to node"""
        if not self.is_eligible_for_ubi(node_id):
            return 0.0, funding_pool

        ubi = min(self.ubi_amount, funding_pool)

        if ubi > 0:
            self.last_ubi_distribution[node_id] = time.time()
            remaining_pool = funding_pool - ubi
            return ubi, remaining_pool

        return 0.0, funding_pool


class DiversityQuotas:
    """
    Diversity quotas for fair job distribution
    (Commit 5 Implementation - Tracking & Commit 6 logic added for completeness)
    """

    def __init__(self, window_size: int = 100, max_share: float = 0.30):
        """
        Args:
            window_size: Number of recent jobs to track
            max_share: Maximum percentage of jobs one node should win (0.30 = 30%)
        """
        self.window_size = window_size
        self.max_share = max_share

        # Track recent job winners (circular buffer)
        self.recent_winners: deque = deque(maxlen=window_size)

        # Track wins per node
        self.node_stats: Dict[str, JobDistributionStats] = {}

    def record_job_outcome(self, job_id: str, winner_id: str, losers: List[str], earnings: float):
        """Record job auction outcome and update node statistics."""
        current_time = time.time()

        # Add to recent winners (important for window calculation)
        self.recent_winners.append(winner_id)

        # --- Update winner stats ---
        if winner_id not in self.node_stats:
            self.node_stats[winner_id] = JobDistributionStats(
                node_id=winner_id, jobs_won=0, jobs_lost=0, total_earnings=0.0, last_win_time=0.0, win_rate=0.0
            )

        stats = self.node_stats[winner_id]
        stats.jobs_won += 1
        stats.total_earnings += earnings
        stats.last_win_time = current_time
        # Recalculate win rate (+1 in denominator prevents Division by Zero on first attempt)
        stats.win_rate = stats.jobs_won / (stats.jobs_won + stats.jobs_lost + 1) 

        # --- Update loser stats ---
        for loser_id in losers:
            if loser_id not in self.node_stats:
                self.node_stats[loser_id] = JobDistributionStats(
                    node_id=loser_id, jobs_won=0, jobs_lost=0, total_earnings=0.0, last_win_time=0.0, win_rate=0.0
                )
            
            loser_stats = self.node_stats[loser_id]
            loser_stats.jobs_lost += 1
            # Recalculate win rate for losers
            loser_stats.win_rate = (
                loser_stats.jobs_won /
                (loser_stats.jobs_won + loser_stats.jobs_lost + 1)
            )

    # Note: The following methods are the *implementation* for Commit 6, 
    # but are included here to finalize the class structure in one go.
    def calculate_diversity_factor(self, node_id: str) -> float:
        """Calculate diversity factor for bidding (Penalty/Boost)"""
        if not self.recent_winners:
            return 1.0

        wins_in_window = sum(1 for w in self.recent_winners if w == node_id)
        win_percentage = wins_in_window / len(self.recent_winners)

        if win_percentage > self.max_share:
            penalty = 1.0 - ((win_percentage - self.max_share) * 2)
            return max(0.5, penalty)

        elif win_percentage < self.max_share / 2:
            target = self.max_share / 2
            boost = 1.0 + ((target - win_percentage) / target) * 0.5
            return min(1.5, boost)

        else:
            return 1.0

    def calculate_affirmative_action_bonus(self, node_id: str) -> float:
        """Calculate affirmative action bonus for struggling nodes (Additive Bonus)"""
        if node_id not in self.node_stats:
            return 0.1

        stats = self.node_stats[node_id]

        if stats.win_rate < 0.1:
            return 0.20
        elif stats.win_rate < 0.2:
            return 0.15
        elif stats.win_rate < 0.3:
            return 0.10
        elif stats.win_rate < 0.4:
            return 0.05

        return 0.0

    def calculate_gini_coefficient(self) -> float:
        """Calculate Gini coefficient for job distribution"""
        if not self.node_stats:
            return 0.0

        earnings = sorted([stats.total_earnings for stats in self.node_stats.values()])
        n = len(earnings)

        if n == 0 or sum(earnings) == 0:
            return 0.0

        cumulative_earnings = 0
        gini_sum = 0
        for i, earning in enumerate(earnings):
            cumulative_earnings += earning
            gini_sum += cumulative_earnings

        total_earnings = sum(earnings)
        gini = (2 * gini_sum) / (n * total_earnings) - (n + 1) / n
        return gini


class TrustDecay:
    """Trust decay system - trust naturally decays over time (Commit 1 Stub)"""
    def __init__(self, decay_rate: float = 0.01, min_trust: float = 0.1):
        self.decay_rate = decay_rate
        self.min_trust = min_trust
        self.last_decay: Dict[str, float] = {}

    def apply_decay(self, node_id: str, current_trust: float) -> float: pass


class JobComplexityAnalyzer:
    """
    Analyzes job complexity for fair compensation
    (Commit 4 Implementation)
    """

    def __init__(self):
        self.job_type_multipliers = {
            'shell': 1.0,
            'docker_build': 2.5,
            'malware_scan': 2.0,
            'port_scan': 1.5,
            'vuln_scan': 2.5,
            'log_analysis': 1.8,
            'hash_crack': 3.0,
            'threat_intel': 1.3,
            'forensics': 3.5,
            'ml_inference': 2.8,
            'data_processing': 2.0
        }

    def analyze_complexity(self, job: dict) -> float:
        """Analyze job complexity"""
        base_multiplier = 1.0
        job_type = job.get('job_type', 'unknown')
        type_multiplier = self.job_type_multipliers.get(job_type, 1.0)
        
        # Factor 2: Payload size
        payload = job.get('payload', {})
        payload_size = len(str(payload))
        size_multiplier = 1.0 + min(1.0, payload_size / 1000.0) 

        # Factor 3: Requirements
        requirements = job.get('requirements', [])
        req_multiplier = 1.0 + (len(requirements) * 0.1)

        # Factor 4: Priority
        priority = job.get('priority', 0.5)
        priority_multiplier = 1.0 + (priority * 0.5)

        # Combine factors
        complexity = (
            base_multiplier *
            type_multiplier *
            size_multiplier *
            req_multiplier *
            priority_multiplier
        )

        return min(5.0, complexity) 


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