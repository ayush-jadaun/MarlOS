"""
Economic Fairness Engine - Research-Level Innovation
Implements novel mechanisms to prevent monopolization and ensure fair resource distribution

INNOVATIONS:
1. Progressive Taxation & Universal Basic Income (UBI)
2. Diversity Quotas & Affirmative Action Bidding
3. Trust Decay with Activity Rewards
4. Job Complexity Analysis for Fair Compensation
5. Proof of Work Verification
6. Cooperative Rewards for Collaboration
7. Wealth Cap & Redistribution
8. Gini Coefficient for Inequality Measurement
"""
import time
import math
from typing import Dict, List, Tuple, Optional
from collections import deque, defaultdict
from ..schema.schema import JobDistributionStats


class ProgressiveTaxation:
    """
    Progressive taxation system - rich nodes pay higher tax rates

    INNOVATION: Prevents wealth monopolization through graduated tax brackets
    """

    def __init__(self):
        # Tax brackets (wealth -> tax_rate)
        self.tax_brackets = [
            (0, 0.00),          # 0-100 AC: 0%
            (100, 0.05),        # 100-500 AC: 5%
            (500, 0.10),        # 500-1000 AC: 10%
            (1000, 0.15),       # 1000-2000 AC: 15%
            (2000, 0.20),       # 2000-5000 AC: 20%
            (5000, 0.25),       # 5000-10000 AC: 25%
            (10000, 0.30),      # 10000+ AC: 30%
        ]

        # Tax revenue pool (for UBI)
        self.tax_revenue_pool = 0.0

    def calculate_tax(self, wealth: float, earnings: float) -> float:
        """
        Calculate tax on earnings based on total wealth

        Args:
            wealth: Total wealth (balance + staked)
            earnings: New earnings to tax

        Returns:
            Tax amount
        """
        # Find applicable tax bracket
        tax_rate = 0.0
        for threshold, rate in reversed(self.tax_brackets):
            if wealth >= threshold:
                tax_rate = rate
                break

        tax = earnings * tax_rate

        # Add to tax pool
        self.tax_revenue_pool += tax

        return tax

    def get_tax_rate(self, wealth: float) -> float:
        """Get tax rate for given wealth level"""
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
    """
    Diversity quotas for fair job distribution

    INNOVATION: Tracks job distribution and applies affirmative action to underutilized nodes
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
        """Record job auction outcome"""
        current_time = time.time()

        # Add to recent winners
        self.recent_winners.append(winner_id)

        # Update winner stats
        if winner_id not in self.node_stats:
            self.node_stats[winner_id] = JobDistributionStats(
                node_id=winner_id,
                jobs_won=0,
                jobs_lost=0,
                total_earnings=0.0,
                last_win_time=0.0,
                win_rate=0.0
            )

        stats = self.node_stats[winner_id]
        stats.jobs_won += 1
        stats.total_earnings += earnings
        stats.last_win_time = current_time
        stats.win_rate = stats.jobs_won / (stats.jobs_won + stats.jobs_lost + 1)

        # Update loser stats
        for loser_id in losers:
            if loser_id not in self.node_stats:
                self.node_stats[loser_id] = JobDistributionStats(
                    node_id=loser_id,
                    jobs_won=0,
                    jobs_lost=0,
                    total_earnings=0.0,
                    last_win_time=0.0,
                    win_rate=0.0
                )
            self.node_stats[loser_id].jobs_lost += 1
            self.node_stats[loser_id].win_rate = (
                self.node_stats[loser_id].jobs_won /
                (self.node_stats[loser_id].jobs_won + self.node_stats[loser_id].jobs_lost + 1)
            )

    def calculate_diversity_factor(self, node_id: str) -> float:
        """
        Calculate diversity factor for bidding

        Returns:
            Multiplier for bid score (0.5 to 1.5)
            - <1.0: Penalty for over-utilized nodes
            - >1.0: Boost for under-utilized nodes
        """
        if not self.recent_winners:
            return 1.0  # No data yet

        # Count this node's wins in recent window
        wins_in_window = sum(1 for w in self.recent_winners if w == node_id)
        win_percentage = wins_in_window / len(self.recent_winners)

        # Calculate diversity factor
        if win_percentage > self.max_share:
            # Penalty for over-utilized (e.g., 40% wins -> 0.75x multiplier)
            penalty = 1.0 - ((win_percentage - self.max_share) * 2)
            return max(0.5, penalty)

        elif win_percentage < self.max_share / 2:
            # Boost for under-utilized (e.g., 5% wins -> 1.3x multiplier)
            target = self.max_share / 2
            boost = 1.0 + ((target - win_percentage) / target) * 0.5
            return min(1.5, boost)

        else:
            # Fair share - no adjustment
            return 1.0

    def calculate_affirmative_action_bonus(self, node_id: str) -> float:
        """
        Calculate affirmative action bonus for struggling nodes

        Returns:
            Bonus score (0.0 to 0.2)
        """
        if node_id not in self.node_stats:
            return 0.1  # New nodes get moderate bonus

        stats = self.node_stats[node_id]

        # Bonus based on low win rate
        if stats.win_rate < 0.1:
            return 0.20  # Struggling nodes get big boost
        elif stats.win_rate < 0.2:
            return 0.15
        elif stats.win_rate < 0.3:
            return 0.10
        elif stats.win_rate < 0.4:
            return 0.05

        return 0.0

    def calculate_gini_coefficient(self) -> float:
        """
        Calculate Gini coefficient for job distribution

        Returns:
            Gini coefficient (0 = perfect equality, 1 = perfect inequality)
            Target: <0.3 for fair system
        """
        if not self.node_stats:
            return 0.0

        # Get all earnings sorted
        earnings = sorted([stats.total_earnings for stats in self.node_stats.values()])
        n = len(earnings)

        if n == 0 or sum(earnings) == 0:
            return 0.0

        # Calculate Gini coefficient
        cumulative_earnings = 0
        gini_sum = 0

        for i, earning in enumerate(earnings):
            cumulative_earnings += earning
            gini_sum += cumulative_earnings

        total_earnings = sum(earnings)
        gini = (2 * gini_sum) / (n * total_earnings) - (n + 1) / n

        return gini


class TrustDecay:
    """
    Trust decay system - trust naturally decays over time

    INNOVATION: Prevents nodes from coasting on old reputation
    """

    def __init__(self, decay_rate: float = 0.01, min_trust: float = 0.1):
        """
        Args:
            decay_rate: Trust decay per day
            min_trust: Minimum trust score
        """
        self.decay_rate = decay_rate
        self.min_trust = min_trust

        # Track last decay time per node
        self.last_decay: Dict[str, float] = {}

    def apply_decay(self, node_id: str, current_trust: float) -> float:
        """
        Apply trust decay based on time elapsed

        Returns:
            New trust score
        """
        current_time = time.time()
        last_decay_time = self.last_decay.get(node_id, current_time)

        # Calculate days elapsed
        seconds_elapsed = current_time - last_decay_time
        days_elapsed = seconds_elapsed / 86400.0

        # Apply decay
        decay_amount = self.decay_rate * days_elapsed
        new_trust = max(self.min_trust, current_trust - decay_amount)

        # Update last decay time
        self.last_decay[node_id] = current_time

        return new_trust


class JobComplexityAnalyzer:
    """
    Analyzes job complexity for fair compensation

    INNOVATION: Harder jobs pay more, not just fixed rates
    """

    def __init__(self):
        # Complexity multipliers by job type
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
        """
        Analyze job complexity

        Returns:
            Complexity multiplier (1.0 to 5.0)
        """
        base_multiplier = 1.0

        # Factor 1: Job type
        job_type = job.get('job_type', 'unknown')
        type_multiplier = self.job_type_multipliers.get(job_type, 1.0)

        # Factor 2: Payload size (larger payloads = more complex)
        payload = job.get('payload', {})
        payload_size = len(str(payload))
        size_multiplier = 1.0 + min(1.0, payload_size / 1000.0)  # Up to 2x for large payloads

        # Factor 3: Number of requirements
        requirements = job.get('requirements', [])
        req_multiplier = 1.0 + (len(requirements) * 0.1)  # +10% per requirement

        # Factor 4: Priority (higher priority = more valuable)
        priority = job.get('priority', 0.5)
        priority_multiplier = 1.0 + (priority * 0.5)  # Up to 1.5x

        # Combine factors
        complexity = (
            base_multiplier *
            type_multiplier *
            size_multiplier *
            req_multiplier *
            priority_multiplier
        )

        return min(5.0, complexity)  # Cap at 5x


class ProofOfWorkVerification:
    """
    Proof of work verification system

    INNOVATION: Winners must prove they did the work, random nodes verify
    """

    def __init__(self, verification_probability: float = 0.3):
        """
        Args:
            verification_probability: Probability a job requires verification (0.3 = 30%)
        """
        self.verification_probability = verification_probability

        # Track pending verifications
        self.pending_verifications: Dict[str, dict] = {}  # job_id -> verification_data

    def requires_verification(self, job: dict) -> bool:
        """
        Determine if job requires verification

        High-value jobs always require verification
        Others randomly
        """
        payment = job.get('payment', 0)

        # High-value jobs always verified
        if payment > 200:
            return True

        # Otherwise, random sampling
        import random
        return random.random() < self.verification_probability

    def create_verification_challenge(self, job_id: str, result: dict) -> dict:
        """
        Create verification challenge for job result

        Returns:
            Challenge data for verifiers
        """
        challenge = {
            'job_id': job_id,
            'result_hash': self._hash_result(result),
            'timestamp': time.time(),
            'verifier_count': 0,
            'verifications': []  # List of (verifier_id, verdict)
        }

        self.pending_verifications[job_id] = challenge
        return challenge

    def record_verification(self, job_id: str, verifier_id: str, verdict: bool):
        """
        Record a verification

        Args:
            verdict: True if result is correct, False otherwise
        """
        if job_id in self.pending_verifications:
            challenge = self.pending_verifications[job_id]
            challenge['verifications'].append((verifier_id, verdict))
            challenge['verifier_count'] += 1

    def get_consensus_verdict(self, job_id: str, min_verifiers: int = 2) -> Optional[bool]:
        """
        Get consensus verdict on verification

        Returns:
            True if verified, False if rejected, None if not enough verifiers
        """
        if job_id not in self.pending_verifications:
            return None

        challenge = self.pending_verifications[job_id]

        if challenge['verifier_count'] < min_verifiers:
            return None

        # Count votes
        approvals = sum(1 for _, verdict in challenge['verifications'] if verdict)
        rejections = challenge['verifier_count'] - approvals

        # Majority wins
        return approvals > rejections

    def _hash_result(self, result: dict) -> str:
        """Hash job result for verification"""
        import hashlib
        import json
        result_str = json.dumps(result, sort_keys=True)
        return hashlib.sha256(result_str.encode()).hexdigest()


class CooperativeRewards:
    """
    Rewards for cooperative behavior

    INNOVATION: Nodes that help others get bonuses
    """

    def __init__(self):
        # Track cooperative actions
        self.verifications_performed: Dict[str, int] = defaultdict(int)
        self.help_provided: Dict[str, int] = defaultdict(int)

    def record_verification(self, verifier_id: str):
        """Record that node performed verification"""
        self.verifications_performed[verifier_id] += 1

    def calculate_cooperative_bonus(self, node_id: str) -> float:
        """
        Calculate bonus for cooperative behavior

        Returns:
            Bonus multiplier (1.0 to 1.2)
        """
        verifications = self.verifications_performed.get(node_id, 0)

        # Bonus for active verifiers
        if verifications > 50:
            return 1.20
        elif verifications > 20:
            return 1.15
        elif verifications > 5:
            return 1.10
        elif verifications > 0:
            return 1.05

        return 1.0


class EconomicFairnessEngine:
    """
    Master fairness engine - coordinates all fairness mechanisms
    """

    def __init__(self):
        self.taxation = ProgressiveTaxation()
        self.ubi = UniversalBasicIncome(ubi_amount=5.0)
        self.diversity = DiversityQuotas(window_size=100, max_share=0.30)
        self.trust_decay = TrustDecay(decay_rate=0.01)
        self.complexity = JobComplexityAnalyzer()
        self.verification = ProofOfWorkVerification(verification_probability=0.3)
        self.cooperation = CooperativeRewards()

    def calculate_fair_bid_score(self,
                                  base_score: float,
                                  node_id: str,
                                  trust_score: float) -> float:
        """
        Calculate fair bid score with all fairness mechanisms

        Args:
            base_score: Original bid score
            node_id: Bidding node ID
            trust_score: Node's trust score

        Returns:
            Adjusted score with fairness
        """
        # Apply diversity factor
        diversity_factor = self.diversity.calculate_diversity_factor(node_id)

        # Apply affirmative action bonus
        affirmative_bonus = self.diversity.calculate_affirmative_action_bonus(node_id)

        # Apply cooperative bonus
        cooperative_factor = self.cooperation.calculate_cooperative_bonus(node_id)

        # Combine all factors
        fair_score = base_score * diversity_factor * cooperative_factor + affirmative_bonus

        return min(1.0, max(0.0, fair_score))

    def calculate_fair_payment(self,
                               base_payment: float,
                               job: dict,
                               node_id: str,
                               wealth: float,
                               completion_time: float) -> Tuple[float, float, str]:
        """
        Calculate fair payment with complexity and taxation

        Returns:
            (net_payment, tax_amount, reason)
        """
        # Calculate complexity multiplier
        complexity = self.complexity.analyze_complexity(job)

        # Adjusted payment
        adjusted_payment = base_payment * complexity

        # Apply progressive taxation
        tax = self.taxation.calculate_tax(wealth, adjusted_payment)

        # Net payment
        net_payment = adjusted_payment - tax

        reason = f"Complexity: {complexity:.2f}x, Tax: {tax:.2f} AC ({self.taxation.get_tax_rate(wealth)*100:.1f}%)"

        return net_payment, tax, reason

    def distribute_ubi_if_eligible(self, node_id: str) -> float:
        """
        Distribute UBI to node if eligible

        Returns:
            UBI amount received
        """
        # Record activity
        self.ubi.record_activity(node_id)

        # Try to distribute
        ubi_amount, remaining_pool = self.ubi.distribute_ubi(
            node_id,
            self.taxation.tax_revenue_pool
        )

        if ubi_amount > 0:
            self.taxation.tax_revenue_pool = remaining_pool
            return ubi_amount

        return 0.0

    def get_gini_coefficient(self) -> float:
        """
        Get Gini coefficient for economic inequality

        Returns:
            Gini coefficient (0 = perfect equality, 1 = perfect inequality)
        """
        return self.diversity.calculate_gini_coefficient()

    def get_fairness_metrics(self) -> dict:
        """
        Get comprehensive fairness metrics

        Returns:
            Dictionary of fairness indicators
        """
        gini = self.diversity.calculate_gini_coefficient()

        return {
            'gini_coefficient': gini,
            'inequality_status': 'low' if gini < 0.3 else ('medium' if gini < 0.5 else 'high'),
            'tax_revenue_pool': self.taxation.tax_revenue_pool,
            'ubi_distributed': len(self.ubi.last_ubi_distribution),
            'total_jobs_tracked': len(self.diversity.recent_winners),
            'total_nodes_tracked': len(self.diversity.node_stats)
        }


# Example usage
if __name__ == "__main__":
    engine = EconomicFairnessEngine()

    # Test case: Rich node vs poor node
    rich_score = engine.calculate_fair_bid_score(
        base_score=0.9,
        node_id='rich-node',
        trust_score=0.95
    )

    poor_score = engine.calculate_fair_bid_score(
        base_score=0.6,
        node_id='poor-node',
        trust_score=0.3
    )

    print(f"Rich node score: {rich_score:.3f}")
    print(f"Poor node score: {poor_score:.3f}")

    # Test payment
    job = {
        'job_type': 'malware_scan',
        'payment': 100.0,
        'priority': 0.8,
        'payload': {'file': 'test.exe' * 100}  # Large payload
    }

    net_payment, tax, reason = engine.calculate_fair_payment(
        base_payment=100.0,
        job=job,
        node_id='rich-node',
        wealth=5000.0,  # Rich
        completion_time=time.time()
    )

    print(f"\nPayment calculation: {net_payment:.2f} AC (tax: {tax:.2f})")
    print(f"Reason: {reason}")

    # Metrics
    metrics = engine.get_fairness_metrics()
    print(f"\nFairness metrics: {metrics}")
