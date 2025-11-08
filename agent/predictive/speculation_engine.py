"""
Speculation Engine - Decides What to Pre-Execute
Uses RL policy + economic game theory to balance speculation vs waste
"""

import asyncio
from collections import defaultdict
from typing import Optional, List
from ..config import PredictiveConfig
from .rl_speculation import RLSpeculationPolicy
import time

class SpeculationEngine:
    """
    Intelligent speculation engine with economic constraints

    Key insight: Only speculate when expected value > 0
    Expected value = (confidence * reward) - ((1 - confidence) * penalty)
    """

    def __init__(
        self,
        agent,
        config: PredictiveConfig,
        executor,
        cache,
        pattern_detector,
        wallet=None
    ):
        """
        Args:
            config: Predictive configuration
            executor: Job executor for pre-execution
            cache: Result cache
            pattern_detector: Pattern detector
            wallet: Wallet for balance tracking (optional)
        """
        self.agent = agent
        self.config = config
        self.executor = executor
        self.cache = cache
        self.pattern_detector = pattern_detector
        self.wallet = wallet

        # Track active speculations
        self.active_speculations = 0
        self.max_speculations = 3  # Max concurrent speculations
        
        # Add lock for thread-safe speculation tracking
        self._speculation_lock = asyncio.Lock()

        # Statistics
        self.speculations_attempted = 0
        self.speculations_successful = 0  # Led to cache hit
        self.speculations_wasted = 0  # No cache hit

        # RL Policy for speculation decisions
        self.rl_policy = None
        if config.rl_speculation_enabled:
            self.rl_policy = RLSpeculationPolicy(
                model_path=config.rl_model_path,
                enabled=True
            )
            print(f"[SPECULATE] Using RL policy for speculation decisions")
        else:
            print(f"[SPECULATE] Using heuristic policy (RL disabled)")

        print(f"[SPECULATE] Speculation engine initialized")

    async def speculate(self):
        """
        Main speculation loop

        Periodically:
        1. Get predictions from pattern detector
        2. Evaluate economics of each prediction
        3. Pre-execute profitable predictions
        """
        try:
            # Check if agent is idle
            active_jobs = self.executor.get_active_job_count()
            max_jobs = getattr(self.executor.config, 'max_concurrent_jobs', 3)

            if active_jobs >= max_jobs:
                # Too busy with real jobs, don't speculate
                return

            # Check speculation ratio
            speculation_ratio = self.active_speculations / max(max_jobs, 1)
            if speculation_ratio >= self.config.max_speculation_ratio:
                # Already speculating too much
                return

            # Get predictions from pattern detector
            predictions = self.pattern_detector.predict_next_jobs()

            if not predictions:
                return  # No patterns detected yet

            # Evaluate each prediction
            for prediction in predictions[:3]:  # Top 3 predictions only
                if await self._should_speculate(prediction):
                    await self._execute_speculation(prediction)
        
        except Exception as e:
            # Catch any errors to prevent loop from crashing
            print(f"❌ [SPECULATE] Error in speculation loop: {e}")

    async def _should_speculate(self, prediction: dict) -> bool:
        """
        Decide whether to speculate on this prediction

        Uses RL policy if available, otherwise falls back to heuristic

        Returns:
            True if should speculate
        """
        async with self._speculation_lock:
            # Check if we're at speculation limit
            if self.active_speculations >= self.max_speculations:
                return False

            # Don't speculate on same job twice
            fingerprint = prediction.get('fingerprint')
            if fingerprint:
                # Check if this fingerprint is already in cache
                # Pass empty dict as job, with fingerprint parameter
                cached = self.cache.get({}, fingerprint=fingerprint)
                if cached:
                    return False  # Already cached

            # Build context for decision
            context = self._get_agent_context()

            if self.rl_policy:
                # Use RL policy
                should_speculate, confidence, state = self.rl_policy.decide(
                    prediction,
                    context
                )
                return should_speculate
            else:
                # Fallback to heuristic
                return self._heuristic_should_speculate(prediction)

    def _heuristic_should_speculate(self, prediction: dict) -> bool:
        """
        Fallback heuristic when RL not available

        Simple rule: Speculate if expected value > threshold
        """
        confidence = prediction['confidence']

        # Calculate expected value
        expected_reward = confidence * self.config.correct_prediction_reward
        expected_penalty = (1 - confidence) * self.config.wrong_prediction_penalty
        expected_value = expected_reward - expected_penalty

        # Only speculate if profitable
        return expected_value >= self.config.min_expected_value

    def _get_agent_context(self) -> dict:
        """
        Get current agent context for RL policy

        Returns dict with features like CPU idle, balance, cache state, etc.
        """
        try:
            import psutil

            # Get CPU idle
            cpu_idle = 100.0 - psutil.cpu_percent(interval=None)
            cpu_idle_pct = cpu_idle / 100.0

            # Get cache utilization
            cache_stats = self.cache.get_stats()
            cache_utilization = cache_stats['cache_size'] / cache_stats['max_size']

            # Get recent hit rate
            recent_hit_rate = cache_stats['hit_rate'] / 100.0 if cache_stats['total_predictions'] > 0 else 0.0

            # Get balance
            balance = self.wallet.balance if self.wallet else 100.0

            # Get active jobs
            active_jobs = self.executor.get_active_job_count()

            return {
                'cpu_idle_pct': cpu_idle_pct,
                'cache_utilization': cache_utilization,
                'recent_hit_rate': recent_hit_rate,
                'balance': balance,
                'active_jobs': active_jobs
            }
        except Exception as e:
            print(f"⚠️  [SPECULATE] Error getting agent context: {e}")
            # Return default context
            return {
                'cpu_idle_pct': 0.5,
                'cache_utilization': 0.0,
                'recent_hit_rate': 0.0,
                'balance': 100.0,
                'active_jobs': 0
            }

    async def _execute_speculation(self, prediction: dict):
            """
            Pre-execute a predicted job
            """
            async with self._speculation_lock:
                self.active_speculations += 1
                self.speculations_attempted += 1
            
            # --- NEW: Define the stake amount ---
            # This is the 2.5 AC from your error log.
            # You should make this a configurable setting.
            speculative_stake = 2.5 
            job_id = None # Define job_id in the outer scope

            try:
                # Reconstruct job from prediction
                job = self._reconstruct_job(prediction)

                if job is None:
                    print(f"⚠️  [SPECULATE] Cannot reconstruct job from prediction")
                    return

                # --- FIX 1: Get the actual job_id from the job object ---
                job_id = job.get('job_id')
                if not job_id:
                    print(f"⚠️  [SPECULATE] Reconstructed job has no job_id. Aborting.")
                    return

                # --- NEW: You MUST stake the tokens first! ---
                if not self.agent.wallet.stake(speculative_stake, job_id):
                    print(f"❌ [SPECULATE] Wallet failed to stake {speculative_stake} AC. Aborting.")
                    # We return here, the 'finally' block will still run
                    return

                fingerprint = prediction.get('fingerprint')
                
                # --- FIX 2: Use the correct variables from above ---
                self.agent.active_job_metadata[job_id] = {
                    'payment': 0, # Speculative, so no payment
                    'deadline': time.time() + 30, # Short deadline
                    'stake': speculative_stake, # The ACTUAL amount staked
                    'job_type': job.get('job_type', 'shell'), # Get type from job
                    'priority': 0.1,
                    'start_time': time.time()
                }

                print(f"🔮 [SPECULATE] Pre-executing job (confidence={prediction['confidence']:.0%}, reason={prediction['reason']})")
                print(f"   Expected in: {prediction.get('expected_in', '?')}s")

                # Execute the job speculatively
                result = await self.executor.execute_job(job)

                # Store result in cache
                self.cache.store(job, result, fingerprint=fingerprint)

                print(f"✅ [SPECULATE] Speculation complete, result cached")

            except Exception as e:
                print(f"❌ [SPECULATE] Speculation failed: {e}")

            finally:
                async with self._speculation_lock:
                    self.active_speculations -= 1
                
                # --- NOTE ---
                # You do NOT need to unstake here.
                # The executor's 'result_callback' (which is _handle_job_result)
                # will run automatically and handle unstaking/slashing 
                # based on the metadata we just added.
    def _reconstruct_job(self, prediction: dict) -> Optional[dict]:
            """
            Reconstruct a job dict from a prediction
            """
            try:
                params = {}
                job_type = prediction.get('job_type')
                fingerprint = prediction.get('fingerprint')

                # Case 1: Repeated job (best case, we have exact params)
                if fingerprint and fingerprint in self.pattern_detector.job_fingerprints:
                    for job_record in reversed(self.pattern_detector.job_history):
                        if job_record['fingerprint'] == fingerprint:
                            job_type = job_record['type']
                            params = job_record.get('params', {})
                            break
                
                # Case 2: Sequence or Time pattern (guess params)
                elif job_type:
                    # Find the most common params for this job_type from history
                    param_counts = defaultdict(int)
                    for job_record in self.pattern_detector.job_history:
                        if job_record['type'] == job_type:
                            param_str = str(sorted(job_record.get('params', {}).items()))
                            param_counts[param_str] += 1
                    
                    if param_counts:
                        most_common_param_str = max(param_counts, key=param_counts.get)
                        try:
                            # Convert '[('command', 'echo hello')]' back to a dict
                            params = dict(eval(most_common_param_str))
                        except:
                            print(f"⚠️  [SPECULATE] Could not eval params: {most_common_param_str}")
                            params = {} # Fallback to empty

                if not job_type:
                    return None
                
                # --- FIX: Reconstruct the job with params at the top level ---
                reconstructed_job = {
                    'job_id': f"speculative-{job_type}-{int(asyncio.get_event_loop().time())}",
                    'job_type': job_type,
                    'payment': 0,
                    'is_speculative': True
                }
                # This adds {'command': '...'} back to the job
                reconstructed_job.update(params) 
                
                return reconstructed_job

            except Exception as e:
                print(f"⚠️  [SPECULATE] Error reconstructing job: {e}")
                return None

    def report_cache_hit(self, fingerprint: str):
        """Report that a speculation led to a cache hit"""
        self.speculations_successful += 1
        print(f"💰 [SPECULATE] Speculation SUCCESS! Cache hit saved compute time")

    def report_cache_miss_expiry(self, fingerprint: str):
        """Report that a speculation was wasted (expired without use)"""
        self.speculations_wasted += 1

    def get_stats(self) -> dict:
        """Get speculation statistics"""
        success_rate = 0
        if self.speculations_attempted > 0:
            success_rate = (self.speculations_successful / self.speculations_attempted) * 100

        stats = {
            'speculations_attempted': self.speculations_attempted,
            'speculations_successful': self.speculations_successful,
            'speculations_wasted': self.speculations_wasted,
            'success_rate': success_rate,
            'active_speculations': self.active_speculations,
            'using_rl_policy': self.rl_policy is not None
        }

        # Add RL policy stats if available
        if self.rl_policy:
            stats['rl_policy'] = self.rl_policy.get_stats()

        return stats