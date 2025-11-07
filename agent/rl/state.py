"""
RL State Representation
Converts agent and job context into RL state vector

 Enhanced with economic fairness features for fair learning
"""
import numpy as np
import psutil
import time
from typing import Dict, Any, Optional

try:
    from ..economy.fairness import EconomicFairnessEngine
except ImportError:
    EconomicFairnessEngine = None


class StateCalculator:
    """
    Calculates RL state vector from current context
    """
    
    def __init__(self, node_id: str, enable_fairness: bool = True):
        self.node_id = node_id

        # Historical tracking
        self.job_type_history: Dict[str, int] = {}  # job_type -> count completed
        self.job_type_success: Dict[str, int] = {}  # job_type -> count successful
        self.recent_completion_times: list = []  # Last 10 completion times

        # Job type encoding (for state vector)
        self.job_type_map = {
            'shell': 0.1,
            'docker_build': 0.2,
            'malware_scan': 0.3,
            'port_scan': 0.4,
            'vuln_scan': 0.5,
            'log_analysis': 0.6,
            'hash_crack': 0.7,
            'threat_intel': 0.8,
            'forensics': 0.9,
            'other': 0.05
        }

        # Initialize psutil CPU monitoring (first call primes the interval)
        psutil.cpu_percent(interval=None)

        # INNOVATION: Economic fairness engine for state features
        if EconomicFairnessEngine and enable_fairness:
            self.fairness_engine = EconomicFairnessEngine()
            print(f"[STATE] Fairness-aware state calculator enabled for {node_id}")
        else:
            self.fairness_engine = None
    
    def calculate_state(self, job: dict, wallet_balance: float,
                       trust_score: float, peer_count: int,
                       active_jobs: int,
                       job_obj: Optional[dict] = None) -> np.ndarray:
        """
        Calculate state vector for RL policy

    

        Returns 25-dimensional state:
        [0-4]   Agent state (CPU, memory, disk, network, active_jobs)
        [5-9]   Job features (type, priority, deadline_urgency, size, payment)
        [10-14] Historical (success_rate, avg_time, recent_failures, experience, trust)
        [15-17] Network (peer_count, competing_bids, wallet_balance)
        [18-24] Fairness (diversity_factor, tax_rate, gini_coeff, ubi_eligible,
                         affirmative_bonus, complexity_mult, cooperative_mult)
        """

        # [0-4] Agent state
        agent_state = self._get_agent_state(active_jobs)

        # [5-9] Job features
        job_features = self._get_job_features(job)

        # [10-14] Historical performance
        historical = self._get_historical_features(job, trust_score)

        # [15-17] Network context
        network = self._get_network_features(peer_count, wallet_balance)

        # [18-24] INNOVATION: Fairness features
        fairness = self._get_fairness_features(job_obj or job, wallet_balance, trust_score)

        # Concatenate all features
        state = np.concatenate([agent_state, job_features, historical, network, fairness])

        return state.astype(np.float32)
    
    def _get_agent_state(self, active_jobs: int) -> np.ndarray:
        """Get current agent resource state [5 features]"""
        try:
            # Use interval=None for non-blocking CPU measurement (returns since last call)
            cpu = psutil.cpu_percent(interval=None) / 100.0  # 0-1
            memory = psutil.virtual_memory().percent / 100.0  # 0-1
            disk = psutil.disk_usage('/').percent / 100.0  # 0-1

            network_latency = 0.1  # TODO: Implement actual network measurement

            # Normalize active jobs (assume max 10 concurrent)
            jobs_normalized = min(1.0, active_jobs / 10.0)

            return np.array([cpu, memory, disk, network_latency, jobs_normalized])

        except Exception as e:
            print(f"[STATE] Error getting agent state: {e}")
            return np.array([0.5, 0.5, 0.5, 0.1, 0.0])  # Default values
    
    def _get_job_features(self, job: dict) -> np.ndarray:
        """Get job characteristics [5 features]"""
        # Job type encoding
        job_type = job.get('job_type', 'other')
        job_type_encoded = self.job_type_map.get(job_type, 0.05)
        
        # Priority (0-1)
        priority = job.get('priority', 0.5)
        
        # Deadline urgency (time until deadline, normalized)
        deadline = job.get('deadline', time.time() + 300)
        time_until_deadline = max(0, deadline - time.time())
        deadline_urgency = 1.0 - min(1.0, time_until_deadline / 300.0)  # Normalize to 5 min
        
        # Estimated job size (normalized)
        # Use payload size or complexity hints
        payload = job.get('payload', {})
        size_estimate = min(1.0, len(str(payload)) / 10000.0)  # Rough estimate
        
        # Payment (normalized to typical range 0-500 AC)
        payment = job.get('payment', 100.0)
        payment_normalized = min(1.0, payment / 500.0)
        
        return np.array([
            job_type_encoded,
            priority,
            deadline_urgency,
            size_estimate,
            payment_normalized
        ])
    
    def _get_historical_features(self, job: dict, trust_score: float) -> np.ndarray:
        """Get historical performance [5 features]"""
        job_type = job.get('job_type', 'other')
        
        # Success rate for this job type
        total = self.job_type_history.get(job_type, 0)
        successes = self.job_type_success.get(job_type, 0)
        success_rate = successes / total if total > 0 else 0.5  # Default 0.5 if no history
        
        # Average completion time (normalized to 0-300 seconds)
        if self.recent_completion_times:
            avg_time = np.mean(self.recent_completion_times) / 300.0
            avg_time = min(1.0, avg_time)
        else:
            avg_time = 0.5  # Default
        
        # Recent failures (last 5 jobs)
        recent_jobs = min(5, len(self.recent_completion_times))
        recent_successes = sum(1 for t in self.recent_completion_times[-5:] if t < 300)
        recent_failure_rate = 1.0 - (recent_successes / recent_jobs if recent_jobs > 0 else 0.5)
        
        # Experience with this job type (normalized)
        experience = min(1.0, total / 20.0)  # 20 jobs = full experience
        
        # Trust score (already 0-1)
        trust = trust_score
        
        return np.array([
            success_rate,
            avg_time,
            recent_failure_rate,
            experience,
            trust
        ])
    
    def _get_network_features(self, peer_count: int, wallet_balance: float) -> np.ndarray:
        """Get network context [3 features]"""
        # Peer count (normalized, assume max 50 peers)
        peers_normalized = min(1.0, peer_count / 50.0)

        # Wallet balance (normalized to 0-1000 AC)
        balance_normalized = min(1.0, wallet_balance / 1000.0)

        # Competing bids estimate (based on peer count)
        # Higher peer count = more competition
        competition = peers_normalized * 0.8  # Rough estimate

        return np.array([
            peers_normalized,
            balance_normalized,
            competition
        ])

    def _get_fairness_features(self, job: dict, wallet_balance: float, trust_score: float) -> np.ndarray:
        """
        Get economic fairness features [7 features]


        Returns:
            [0] diversity_factor: How much this node is winning (0-1, 0.5=balanced)
            [1] tax_rate: Progressive tax based on wealth (0-0.3)
            [2] gini_coefficient: System-wide inequality (0-1, lower=fairer)
            [3] ubi_eligible: Is node eligible for UBI (0 or 1)
            [4] affirmative_bonus: Bonus for helping struggling node (0-0.2)
            [5] complexity_multiplier: Job complexity factor (0.2-1.0 normalized from 1-5x)
            [6] cooperative_multiplier: Cooperative reward factor (0-0.3)
        """
        if not self.fairness_engine:
            # Return neutral values if fairness engine disabled
            return np.array([0.5, 0.0, 0.5, 0.0, 0.0, 0.5, 0.0])

        try:

            diversity_factor = self.fairness_engine.diversity.calculate_diversity_factor(self.node_id)
            # Diversity factor is -0.2 to +0.15, normalize to 0-1
            diversity_normalized = (diversity_factor + 0.2) / 0.35  # Map to 0-1 range

            # [1] Tax rate - progressive taxation based on wealth
            tax = self.fairness_engine.taxation.calculate_tax(
                wealth=wallet_balance,
                earnings=100.0  # Use representative earnings for state
            )
            tax_rate = tax / 100.0  # Normalized tax rate (0-0.3)

            # [2] Gini coefficient - system-wide inequality measure
            gini = self.fairness_engine.get_gini_coefficient()

            # [3] UBI eligibility - binary feature
            ubi_eligible = 1.0 if self.fairness_engine.ubi.is_eligible_for_ubi(
                node_id=self.node_id
            ) else 0.0

            # [4] Affirmative action bonus
            affirmative_bonus = self.fairness_engine.diversity.calculate_affirmative_action_bonus(
                node_id=self.node_id
            )
            affirmative_normalized = affirmative_bonus  # Already 0-0.2

            # [5] Job complexity multiplier
            complexity_mult = self.fairness_engine.complexity.analyze_complexity(job)
            # Complexity is 1-5x, normalize to 0-1
            complexity_normalized = (complexity_mult - 1.0) / 4.0

            # [6] Cooperative reward multiplier
            # Check if job involves cooperation (simplified for state calculation)
            job_type = job.get('job_type', '')
            has_cooperation = 'verify' in job_type or 'collaborative' in job_type
            cooperative_mult = 0.15 if has_cooperation else 0.0

            return np.array([
                diversity_normalized,
                tax_rate,
                gini,
                ubi_eligible,
                affirmative_normalized,
                complexity_normalized,
                cooperative_mult
            ])

        except Exception as e:
            print(f"[STATE] Error calculating fairness features: {e}")
            # Return neutral values on error
            return np.array([0.5, 0.0, 0.5, 0.0, 0.0, 0.5, 0.0])
    
    def update_job_history(self, job_type: str, success: bool, completion_time: float):
        """Update historical tracking after job completion"""
        # Update job type history
        if job_type not in self.job_type_history:
            self.job_type_history[job_type] = 0
            self.job_type_success[job_type] = 0
        
        self.job_type_history[job_type] += 1
        if success:
            self.job_type_success[job_type] += 1
        
        # Update recent completion times
        self.recent_completion_times.append(completion_time)
        if len(self.recent_completion_times) > 10:
            self.recent_completion_times.pop(0)
    
    def get_state_dim(self) -> int:
        """Get state vector dimension (INNOVATION: extended from 18 to 25)"""
        return 25


# Example usage
if __name__ == "__main__":
    calc = StateCalculator("test-node")
    
    job = {
        'job_type': 'malware_scan',
        'priority': 0.8,
        'deadline': time.time() + 120,
        'payment': 150.0,
        'payload': {'file': 'suspicious.exe'}
    }
    
    state = calc.calculate_state(
        job=job,
        wallet_balance=250.0,
        trust_score=0.75,
        peer_count=8,
        active_jobs=2
    )
    
    print(f"State vector shape: {state.shape}")
    print(f"State vector: {state}")
