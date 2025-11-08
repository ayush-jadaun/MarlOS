"""
Bid Score Calculator
Calculates competitive score for job bidding with economic fairness
"""
import psutil
import time
import random
from typing import Dict, Any, Optional

# Import fairness engine
try:
    from ..economy.fairness import EconomicFairnessEngine
except ImportError:
    EconomicFairnessEngine = None


class BidScorer:
    """
    Calculates bid score for jobs
    Score determines bidding priority (0.0 to 1.0)

    DECENTRALIZED FAIRNESS:
    - Reduced trust weight to prevent monopoly
    - Fairness jitter for randomization
    - Idle bonus for agents who haven't won recently
    """

    def __init__(self, node_id: str = "unknown", enable_fairness: bool = True, coordinator=None):
        self.node_id = node_id
        self.enable_fairness = enable_fairness
        self.coordinator = coordinator  # Reference to CoordinatorElection for fairness tracking

        # Scoring weights (decentralized fairness)
        self.CAPABILITY_WEIGHT = 0.35
        self.LOAD_WEIGHT = 0.30
        self.TRUST_WEIGHT = 0.15  # Reduced from 0.25 to prevent monopoly
        self.URGENCY_WEIGHT = 0.10
        self.PRIORITY_WEIGHT = 0.10

        # Fairness parameters
        self.FAIRNESS_JITTER = 0.05  # ±5% random jitter
        self.IDLE_BONUS_MAX = 0.15   # Up to +15% for idle agents
        self.jobs_since_last_win = 0  # Track idle time

        # INNOVATION: Economic fairness engine
        if EconomicFairnessEngine and enable_fairness:
            self.fairness_engine = EconomicFairnessEngine()
            print(f"[SCORER] Fairness engine enabled for {node_id}")
        else:
            self.fairness_engine = None
    
    def calculate_score(self,
                    job: dict,
                    capabilities: list,
                    trust_score: float,
                    active_jobs: int,
                    job_history: Dict[str, int]) -> float:
        """
        Calculate bid score for a job with DECENTRALIZED FAIRNESS

        Higher score = more likely to win
        """
        # 1. Capability match
        capability_score = self._score_capability(job, capabilities, job_history)

        # 2. Current load
        load_score = self._score_load(active_jobs)

        # 3. Trust score with PROGRESSIVE SCALING (diminishing returns)
        trust = trust_score ** 0.7

        # 4. Urgency (deadline proximity)
        urgency_score = self._score_urgency(job)

        # 5. Priority
        priority = job.get('priority', 0.5)

        # Weighted sum
        base_score = (
            capability_score * self.CAPABILITY_WEIGHT +
            load_score * self.LOAD_WEIGHT +
            trust * self.TRUST_WEIGHT +
            urgency_score * self.URGENCY_WEIGHT +
            priority * self.PRIORITY_WEIGHT
        )

        # DEBUG: Log base score components
        print(f"[SCORE DEBUG] {self.node_id} - Job {job.get('job_id', 'unknown')}")
        print(f"  Base Score: {base_score:.4f}")
        print(f"    - Capability: {capability_score:.3f} × {self.CAPABILITY_WEIGHT} = {capability_score * self.CAPABILITY_WEIGHT:.3f}")
        print(f"    - Load:       {load_score:.3f} × {self.LOAD_WEIGHT} = {load_score * self.LOAD_WEIGHT:.3f}")
        print(f"    - Trust:      {trust:.3f} × {self.TRUST_WEIGHT} = {trust * self.TRUST_WEIGHT:.3f}")
        print(f"    - Urgency:    {urgency_score:.3f} × {self.URGENCY_WEIGHT} = {urgency_score * self.URGENCY_WEIGHT:.3f}")
        print(f"    - Priority:   {priority:.3f} × {self.PRIORITY_WEIGHT} = {priority * self.PRIORITY_WEIGHT:.3f}")

        # DECENTRALIZED FAIRNESS MECHANISMS (MULTIPLICATIVE):

        # 1. Idle Multiplier
        idle_multiplier = 1.0 + min(0.10, self.jobs_since_last_win * 0.02)

        # 2. Coordinator-based fairness multiplier
        starvation_multiplier = 1.0
        if self.coordinator:
            starvation_score = self.coordinator.fairness.get_starvation_score(self.node_id)
            starvation_multiplier = 1.0 + (starvation_score * 0.15)

            if starvation_score > 0.5:
                print(f"[FAIRNESS] Applying starvation boost: {starvation_multiplier:.2f}x (score: {starvation_score:.2f})")

        # 3. Fairness Jitter
        jitter_multiplier = 1.0 + random.uniform(-0.03, 0.03)

        # Final score with fairness
        final_score = base_score * idle_multiplier * starvation_multiplier * jitter_multiplier

        # DEBUG: Log fairness adjustments
        print(f"  Fairness Multipliers:")
        print(f"    - Idle:       {idle_multiplier:.4f}x (jobs since win: {self.jobs_since_last_win})")
        print(f"    - Starvation: {starvation_multiplier:.4f}x")
        print(f"    - Jitter:     {jitter_multiplier:.4f}x")
        print(f"  Score after fairness: {final_score:.4f}")

        # INNOVATION: Apply economic fairness mechanisms
        if self.fairness_engine:
            pre_engine_score = final_score
            final_score = self.fairness_engine.calculate_fair_bid_score(
                base_score=final_score,
                node_id=self.node_id,
                trust_score=trust_score
            )
            print(f"  Score after fairness engine: {final_score:.4f} (change: {final_score - pre_engine_score:+.4f})")

        clamped_score = min(1.0, max(0.0, final_score))
        if clamped_score != final_score:
            print(f"  ⚠️  Score clamped: {final_score:.4f} → {clamped_score:.4f}")
        
        print(f"  ✅ Final Score: {clamped_score:.4f}")
        print()

        return clamped_score

    def mark_won_auction(self, job_id: str = None, earnings: float = 0.0):
        """Call this when agent wins an auction"""
        self.jobs_since_last_win = 0

        # Record in fairness engine
        if self.fairness_engine and job_id:
            # Will be called with losers list separately
            pass

    def mark_lost_auction(self, job_id: str = None):
        """Call this when agent loses/skips an auction"""
        self.jobs_since_last_win += 1

    def record_job_outcome(self, job_id: str, winner_id: str, loser_ids: list, earnings: float):
        """
        Record job outcome in fairness engine

        Args:
            job_id: Job ID
            winner_id: Node that won
            loser_ids: Nodes that lost
            earnings: Amount earned by winner
        """
        if self.fairness_engine:
            self.fairness_engine.diversity.record_job_outcome(
                job_id=job_id,
                winner_id=winner_id,
                losers=loser_ids,
                earnings=earnings
            )

    def get_fairness_metrics(self) -> dict:
        """Get fairness metrics from engine"""
        if self.fairness_engine:
            return self.fairness_engine.get_fairness_metrics()
        return {}
    
    def _score_capability(self, job: dict, capabilities: list,
                         job_history: Dict[str, int]) -> float:
        """
        Score capability match
        1.0 = perfect match, 0.0 = can't do it
        """
        job_type = job.get('job_type', 'unknown')
        requirements = job.get('requirements') or []  # Handle None case

        # Check if job type in capabilities
        if job_type not in capabilities:
            return 0.0

        score = 1.0

        # Check requirements
        for req in requirements:
            if req not in capabilities:
                score *= 0.7  # Penalty for missing requirement
        
        # Bonus for experience with this job type
        experience = job_history.get(job_type, 0)
        experience_bonus = min(0.2, experience * 0.02)  # Up to +0.2
        score += experience_bonus
        
        return min(1.0, score)
    
    def _score_load(self, active_jobs: int) -> float:
        """
        Score based on current load
        1.0 = idle, 0.0 = maxed out
        """
        max_concurrent = 5
        
        if active_jobs >= max_concurrent:
            return 0.0
        
        # Linear decrease
        load_factor = 1.0 - (active_jobs / max_concurrent)
        
        # Consider system resources
        try:
            cpu = psutil.cpu_percent(interval=0.1) / 100.0
            memory = psutil.virtual_memory().percent / 100.0
            
            # Average resource usage
            resource_factor = 1.0 - ((cpu + memory) / 2.0)
            
            # Combine load factors
            return (load_factor * 0.6) + (resource_factor * 0.4)
        
        except:
            return load_factor
    
    def _score_urgency(self, job: dict) -> float:
        """
        Score based on deadline urgency
        1.0 = very urgent, 0.0 = lots of time
        """
        deadline = job.get('deadline', time.time() + 300)
        time_left = deadline - time.time()
        
        if time_left <= 0:
            return 1.0  # Already past deadline!
        
        # Normalize to 0-5 minutes
        max_time = 300  # 5 minutes
        urgency = 1.0 - min(1.0, time_left / max_time)
        
        return urgency
    
    def estimate_completion_time(self, job: dict, 
                                job_history: Dict[str, float]) -> float:
        """
        Estimate how long this job will take
        Returns time in seconds
        """
        job_type = job.get('job_type', 'unknown')
        
        # Use historical average if available
        if job_type in job_history and job_history[job_type] > 0:
            # Assume we tracked average times
            return job_history.get(f"{job_type}_avg_time", 60.0)
        
        # Default estimates by job type
        default_times = {
            'shell': 10.0,
            'docker_build': 120.0,
            'malware_scan': 30.0,
            'port_scan': 60.0,
            'vuln_scan': 90.0,
            'log_analysis': 45.0,
            'hash_crack': 180.0,
            'threat_intel': 15.0,
            'forensics': 200.0
        }
        
        return default_times.get(job_type, 60.0)