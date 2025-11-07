"""
RL Training Environment
Simulates MarlOS swarm for training the bidding policy

INNOVATION: Integrated with economic fairness engine for fair learning
"""
import gymnasium as gym # pyright: ignore[reportMissingImports]
import numpy as np
from gymnasium import spaces # pyright: ignore[reportMissingImports]
from typing import Dict, List, Tuple, Optional
import random
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import fairness engine
try:
    from agent.economy.fairness import EconomicFairnessEngine
except ImportError:
    EconomicFairnessEngine = None
    print("[ENV] Warning: EconomicFairnessEngine not available")


class MarlOSEnv(gym.Env):
    """
    Gymnasium environment for training MarlOS bidding policy
    
    Simulates a swarm of agents competing for jobs
    """
    
    metadata = {'render_modes': ['human']}
    
    def __init__(self, num_agents: int = 5, max_jobs: int = 20, enable_fairness: bool = True):
        super().__init__()

        self.num_agents = num_agents
        self.max_jobs = max_jobs
        self.node_id = f"agent-train-{random.randint(1000, 9999)}"

        # State space (25 dimensions - includes fairness features)
        # [0-4]   Agent state (CPU, memory, disk, network, active_jobs)
        # [5-9]   Job features (type, priority, deadline_urgency, size, payment)
        # [10-14] Historical (success_rate, avg_time, recent_failures, experience, trust)
        # [15-17] Network (peer_count, competing_bids, wallet_balance)
        # [18-24] Fairness (diversity_factor, tax_rate, gini_coeff, ubi_eligible,
        #                   affirmative_bonus, complexity_mult, cooperative_mult)
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(25,),
            dtype=np.float32
        )

        # Action space: 0=BID, 1=FORWARD, 2=DEFER
        self.action_space = spaces.Discrete(3)

        # Simulation state
        self.current_job = None
        self.agent_state = None
        self.episode_step = 0
        self.max_episode_steps = 100

        # Agent properties
        self.agent_cpu = 0.0
        self.agent_memory = 0.0
        self.agent_disk = 0.0
        self.agent_network_latency = 0.1
        self.active_jobs = 0

        # Historical tracking
        self.jobs_attempted = 0
        self.jobs_succeeded = 0
        self.jobs_failed = 0
        self.total_completion_time = 0.0
        self.trust_score = 0.5
        self.wallet_balance = 100.0

        # Job type experience
        self.job_type_experience = {}

        # Episode tracking
        self.episode_rewards = []
        self.episode_jobs = 0
        self.episode_successes = 0

        # INNOVATION: Economic fairness engine
        if EconomicFairnessEngine and enable_fairness:
            self.fairness_engine = EconomicFairnessEngine()
            print(f"[ENV] Fairness engine enabled for training environment")
        else:
            self.fairness_engine = None

        # Fairness tracking
        self.total_taxes_paid = 0.0
        self.total_ubi_received = 0.0
        self.jobs_won = 0
        self.jobs_lost = 0
    
    def reset(self, seed=None, options=None):
        """Reset environment to initial state"""
        super().reset(seed=seed)
        
        # Reset agent state with some randomness
        self.agent_cpu = random.uniform(0.1, 0.5)
        self.agent_memory = random.uniform(0.1, 0.5)
        self.agent_disk = random.uniform(0.1, 0.3)
        self.agent_network_latency = random.uniform(0.05, 0.2)
        self.active_jobs = random.randint(0, 2)
        
        # Reset episode tracking
        self.episode_step = 0
        self.episode_jobs = 0
        self.episode_successes = 0
        
        # Generate first job
        self.current_job = self._generate_job()
        
        # Get initial observation
        obs = self._get_observation()
        info = self._get_info()
        
        return obs, info
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, dict]:
        """
        Execute action and return result

        Actions:
        0 = BID (compete for job)
        1 = FORWARD (send to better peer)
        2 = DEFER (skip job)
        """
        self.episode_step += 1
        self.episode_jobs += 1

        reward = 0.0
        terminated = False
        truncated = False

        # Process action
        if action == 0:  # BID
            reward = self._execute_bid()

        elif action == 1:  # FORWARD
            reward = self._execute_forward()

        elif action == 2:  # DEFER
            reward = self._execute_defer()

        if self.fairness_engine and self.episode_step % 10 == 0:  # Every 10 steps = 1 "hour"
            ubi_amount = self.fairness_engine.ubi.distribute_ubi_if_eligible(self.node_id)
            if ubi_amount > 0:
                self.wallet_balance += ubi_amount
                self.total_ubi_received += ubi_amount
                reward += 0.05  # Small reward for staying active

        # Update agent state (simulate passage of time)
        self._update_agent_state()

        # Generate next job
        self.current_job = self._generate_job()

        # Check termination
        if self.episode_step >= self.max_episode_steps:
            truncated = True

        if self.trust_score < 0.1:
            # Agent quarantined - episode ends
            terminated = True
            reward -= 5.0  # Large penalty

        # Get new observation
        obs = self._get_observation()
        info = self._get_info()

        return obs, reward, terminated, truncated, info
    
    def _generate_job(self) -> Dict:
        """Generate random job"""
        job_types = ['shell', 'docker_build', 'malware_scan', 'port_scan', 
                     'vuln_scan', 'log_analysis', 'hash_crack', 'threat_intel']
        
        job = {
            'job_id': f'job-{self.episode_step}',
            'job_type': random.choice(job_types),
            'priority': random.uniform(0.3, 1.0),
            'payment': random.uniform(50.0, 300.0),
            'deadline_seconds': random.uniform(30.0, 300.0),
            'size_estimate': random.uniform(0.1, 1.0),
            'complexity': random.uniform(0.3, 0.9)
        }
        
        return job
    
    def _execute_bid(self) -> float:
        """
        Execute BID action
        Returns reward
        """
        job = self.current_job

        # Calculate if we can complete this job
        can_complete = self._can_complete_job(job)

        # Simulate bidding war 
        win_probability = self._calculate_win_probability()
        won_bid = random.random() < win_probability

        if not won_bid:
            # Lost bid - small opportunity cost
            self.jobs_lost += 1

          
            if self.fairness_engine:
                self.fairness_engine.diversity.record_job_outcome(
                    job_id=job['job_id'],
                    winner_id=f"other-agent-{random.randint(1, self.num_agents)}",
                    losers=[self.node_id],
                    earnings=0.0
                )

            return -0.05

        # Won bid - now execute
        self.active_jobs += 1
        self.jobs_attempted += 1
        self.jobs_won += 1

        # Stake tokens
        stake = job['payment'] * 0.1
        if self.wallet_balance < stake:
            # Can't afford stake - big penalty
            self.trust_score = max(0.0, self.trust_score - 0.1)
            return -1.0

        self.wallet_balance -= stake

        # Simulate job execution
        if can_complete:
            # Success!
            completion_time = self._simulate_completion_time(job)
            on_time = completion_time < job['deadline_seconds']

            self.jobs_succeeded += 1
            self.episode_successes += 1
            self.total_completion_time += completion_time

            # Update experience
            job_type = job['job_type']
            self.job_type_experience[job_type] = self.job_type_experience.get(job_type, 0) + 1

           
            if self.fairness_engine:
                # Build job dict for complexity analysis
                job_dict = {
                    'job_type': job['job_type'],
                    'priority': job['priority'],
                    'payload': {'size': job['size_estimate']},
                    'requirements': []
                }

                # Calculate fair payment
                net_payment, tax, reason = self.fairness_engine.calculate_fair_payment(
                    base_payment=job['payment'],
                    job=job_dict,
                    node_id=self.node_id,
                    wealth=self.wallet_balance,
                    completion_time=completion_time
                )

                self.total_taxes_paid += tax

                # Apply on-time bonus
                if on_time:
                    net_payment *= 1.2

                payment = net_payment
            else:
                # Fallback: original payment calculation
                payment = job['payment']
                if on_time:
                    payment *= 1.2

            # Calculate reward
            reward = 1.0  # Base success

            if on_time:
                # On-time bonus
                reward += 0.5

                # Early bonus
                time_efficiency = 1.0 - (completion_time / job['deadline_seconds'])
                reward += time_efficiency * 0.3

                # Trust increase
                self.trust_score = min(1.0, self.trust_score + 0.02)
            else:
                # Late penalty
                reward -= 0.3
                self.trust_score = min(1.0, self.trust_score + 0.01)

            
            if self.fairness_engine:
                gini = self.fairness_engine.get_gini_coefficient()
                if gini < 0.3:  # Low inequality = good
                    reward += 0.1  # Fairness bonus

            self.wallet_balance += payment + stake  # Return stake

            # Token profit reward
            profit = payment - (job['payment'] * 0.1)  # Subtract stake cost
            reward += min(0.5, profit * 0.001)

            
            if self.fairness_engine:
                self.fairness_engine.diversity.record_job_outcome(
                    job_id=job['job_id'],
                    winner_id=self.node_id,
                    losers=[f"agent-{i}" for i in range(self.num_agents) if i != hash(self.node_id) % self.num_agents],
                    earnings=payment
                )

            self.active_jobs = max(0, self.active_jobs - 1)

            return reward

        else:
            # Failure
            self.jobs_failed += 1

            # Lose stake
            # self.wallet_balance stays reduced (stake lost)

            # Trust decrease
            self.trust_score = max(0.0, self.trust_score - 0.05)

            self.active_jobs = max(0, self.active_jobs - 1)

            return -1.0  # Failure penalty
    
    def _execute_forward(self) -> float:
        """
        Execute FORWARD action
        Returns reward
        """
        job = self.current_job
        
        # Check if we can complete
        can_complete = self._can_complete_job(job)
        
        if not can_complete:
            # Good decision to forward
            referral_fee = job['payment'] * 0.05
            self.wallet_balance += referral_fee
            return 0.2 + (referral_fee * 0.001)
        else:
            # Missed opportunity
            return -0.1
    
    def _execute_defer(self) -> float:
        """
        Execute DEFER action
        Returns reward
        """
        job = self.current_job
        
        # Check if we could have completed
        can_complete = self._can_complete_job(job)
        
        if self.active_jobs >= 3:
            # Good defer - we're busy
            return 0.05
        elif not can_complete:
            # Good defer - we couldn't do it anyway
            return 0.05
        elif job['priority'] < 0.5:
            # Acceptable defer - low priority
            return 0.0
        else:
            # Missed good opportunity
            return -0.1
    
    def _can_complete_job(self, job: Dict) -> bool:
        """
        Simulate whether we can complete this job
        Based on current load and job complexity
        """
        # Check resource availability
        resource_score = 1.0 - ((self.agent_cpu + self.agent_memory) / 2.0)
        
        # Check load
        load_score = 1.0 - (self.active_jobs / 5.0)
        
        # Check experience
        job_type = job['job_type']
        experience = self.job_type_experience.get(job_type, 0)
        experience_score = min(1.0, experience / 10.0)
        
        # Check trust (low trust = less capability)
        trust_factor = self.trust_score
        
        # Overall capability
        capability = (
            resource_score * 0.3 +
            load_score * 0.3 +
            experience_score * 0.2 +
            trust_factor * 0.2
        )
        
        # Compare to job complexity
        success_probability = capability / (job['complexity'] + 0.1)
        
        return random.random() < success_probability
    
    def _calculate_win_probability(self) -> float:
        """Calculate probability of winning bid"""
        # Based on trust score and current load
        load_factor = 1.0 - (self.active_jobs / 5.0)
        
        win_prob = (self.trust_score * 0.6 + load_factor * 0.4)
        
        # Compete with other agents
        win_prob /= self.num_agents
        win_prob *= random.uniform(0.8, 1.2)  # Randomness
        
        return min(1.0, win_prob)
    
    def _simulate_completion_time(self, job: Dict) -> float:
        """Simulate job completion time"""
        base_time = job['deadline_seconds'] * 0.6  # Assume we're reasonably fast
        
        # Add variance
        variance = random.uniform(-0.2, 0.3)
        completion_time = base_time * (1.0 + variance)
        
        # Affected by load
        if self.active_jobs > 2:
            completion_time *= 1.3
        
        # Affected by experience
        job_type = job['job_type']
        experience = self.job_type_experience.get(job_type, 0)
        if experience > 5:
            completion_time *= 0.85  # 15% faster with experience
        
        return completion_time
    
    def _update_agent_state(self):
        """Update agent resource state over time"""
        # Simulate resource changes
        self.agent_cpu = max(0.0, min(1.0, self.agent_cpu + random.uniform(-0.1, 0.1)))
        self.agent_memory = max(0.0, min(1.0, self.agent_memory + random.uniform(-0.1, 0.1)))
        
        # Jobs naturally complete over time
        if self.active_jobs > 0 and random.random() < 0.3:
            self.active_jobs -= 1
    
    def _get_observation(self) -> np.ndarray:
        """Get current state observation with FAIRNESS features"""
        job = self.current_job

        # Job type encoding
        job_type_map = {
            'shell': 0.1, 'docker_build': 0.2, 'malware_scan': 0.3,
            'port_scan': 0.4, 'vuln_scan': 0.5, 'log_analysis': 0.6,
            'hash_crack': 0.7, 'threat_intel': 0.8
        }
        job_type_encoded = job_type_map.get(job['job_type'], 0.05)

        # Calculate historical features
        success_rate = self.jobs_succeeded / max(1, self.jobs_attempted)
        avg_completion_time = self.total_completion_time / max(1, self.jobs_succeeded)
        avg_completion_time_normalized = min(1.0, avg_completion_time / 300.0)

        recent_failure_rate = 1.0 - (self.episode_successes / max(1, self.episode_jobs))

        job_type_exp = self.job_type_experience.get(job['job_type'], 0)
        experience_normalized = min(1.0, job_type_exp / 20.0)

        # Deadline urgency
        deadline_urgency = 1.0 - min(1.0, job['deadline_seconds'] / 300.0)

        # Payment normalized
        payment_normalized = min(1.0, job['payment'] / 500.0)

        # Wallet balance normalized
        balance_normalized = min(1.0, self.wallet_balance / 1000.0)

        # Peer count (simulated)
        peer_count_normalized = self.num_agents / 50.0

        # Competition estimate
        competition = peer_count_normalized * 0.8

        # INNOVATION: Calculate fairness features
        fairness_features = self._get_fairness_features(job)

        # Construct observation vector (25D)
        obs = np.array([
            # [0-4] Agent state
            self.agent_cpu,
            self.agent_memory,
            self.agent_disk,
            self.agent_network_latency,
            self.active_jobs / 5.0,

            # [5-9] Job features
            job_type_encoded,
            job['priority'],
            deadline_urgency,
            job['size_estimate'],
            payment_normalized,

            # [10-14] Historical
            success_rate,
            avg_completion_time_normalized,
            recent_failure_rate,
            experience_normalized,
            self.trust_score,

            # [15-17] Network
            peer_count_normalized,
            balance_normalized,
            competition,

            # [18-24] INNOVATION: Fairness features
            fairness_features[0],  # diversity_factor
            fairness_features[1],  # tax_rate
            fairness_features[2],  # gini_coefficient
            fairness_features[3],  # ubi_eligible
            fairness_features[4],  # affirmative_bonus
            fairness_features[5],  # complexity_multiplier
            fairness_features[6],  # cooperative_multiplier
        ], dtype=np.float32)

        return obs

    def _get_fairness_features(self, job: Dict) -> np.ndarray:
        """
        Calculate fairness features for observation

        """
        if not self.fairness_engine:
            # Return neutral values if fairness disabled
            return np.array([0.5, 0.0, 0.5, 0.0, 0.0, 0.5, 0.0])

        try:
            # [0] Diversity factor
            diversity_factor = self.fairness_engine.diversity.calculate_diversity_factor(self.node_id)
            diversity_normalized = (diversity_factor + 0.2) / 0.35

            # [1] Tax rate
            tax = self.fairness_engine.taxation.calculate_tax(
                wealth=self.wallet_balance,
                earnings=100.0
            )
            tax_rate = tax / 100.0

            # [2] Gini coefficient
            gini = self.fairness_engine.get_gini_coefficient()

            # [3] UBI eligibility
            ubi_eligible = 1.0 if self.fairness_engine.ubi.is_eligible_for_ubi(
                node_id=self.node_id
            ) else 0.0

            # [4] Affirmative action bonus
            affirmative_bonus = self.fairness_engine.diversity.calculate_affirmative_action_bonus(
                node_id=self.node_id
            )

            # [5] Job complexity
            job_dict = {
                'job_type': job['job_type'],
                'priority': job['priority'],
                'payload': {'size': job['size_estimate']},
                'requirements': []
            }
            complexity_mult = self.fairness_engine.complexity.analyze_complexity(job_dict)
            complexity_normalized = (complexity_mult - 1.0) / 4.0

            # [6] Cooperative multiplier
            has_cooperation = 'verify' in job['job_type'] or 'collaborative' in job['job_type']
            cooperative_mult = 0.15 if has_cooperation else 0.0

            return np.array([
                diversity_normalized,
                tax_rate,
                gini,
                ubi_eligible,
                affirmative_bonus,
                complexity_normalized,
                cooperative_mult
            ])

        except Exception as e:
            print(f"[ENV] Error calculating fairness features: {e}")
            return np.array([0.5, 0.0, 0.5, 0.0, 0.0, 0.5, 0.0])
    
    def _get_info(self) -> Dict:
        """Get additional info with FAIRNESS metrics"""
        info = {
            'episode_step': self.episode_step,
            'jobs_attempted': self.jobs_attempted,
            'jobs_succeeded': self.jobs_succeeded,
            'success_rate': self.jobs_succeeded / max(1, self.jobs_attempted),
            'trust_score': self.trust_score,
            'wallet_balance': self.wallet_balance,
            'active_jobs': self.active_jobs
        }

        if self.fairness_engine:
            info.update({
                'gini_coefficient': self.fairness_engine.get_gini_coefficient(),
                'total_taxes_paid': self.total_taxes_paid,
                'total_ubi_received': self.total_ubi_received,
                'jobs_won': self.jobs_won,
                'jobs_lost': self.jobs_lost,
                'win_rate': self.jobs_won / max(1, self.jobs_won + self.jobs_lost),
                'diversity_factor': self.fairness_engine.diversity.calculate_diversity_factor(self.node_id)
            })

        return info
    
    def render(self):
        """Render environment state"""
        if self.episode_step % 10 == 0:
            print(f"\n{'='*50}")
            print(f"Step: {self.episode_step}")
            print(f"Trust: {self.trust_score:.3f} | Balance: {self.wallet_balance:.2f} AC")
            print(f"Jobs: {self.jobs_succeeded}/{self.jobs_attempted} succeeded")
            print(f"Active: {self.active_jobs} | CPU: {self.agent_cpu:.2f}")
            print(f"Current Job: {self.current_job['job_type']} "
                  f"(priority: {self.current_job['priority']:.2f}, "
                  f"payment: {self.current_job['payment']:.2f} AC)")
            print(f"{'='*50}")