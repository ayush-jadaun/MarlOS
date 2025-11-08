"""
Integration Module for Predictive System
Extends MarlOSAgent with predictive capabilities WITHOUT breaking existing code
"""

import asyncio
from .pattern_detector import PatternDetector
from .cache import ResultCache
from .speculation_engine import SpeculationEngine


class PredictiveExtension:
    """
    Extension that adds predictive pre-execution to an agent

    Usage:
        predictive = PredictiveExtension(agent)
        await predictive.start()
    """

    def __init__(self, agent):
        """
        Args:
            agent: MarlOSAgent instance
        """
        self.agent = agent
        self.config = agent.config.predictive

        if not self.config.enabled:
            print(f"🔮 [PREDICT] Predictive system DISABLED in config")
            self.enabled = False
            return

        self.enabled = True

        # Initialize components
        self.pattern_detector = PatternDetector(
            min_occurrences=self.config.min_occurrences
        )

        self.cache = ResultCache(
            max_size=self.config.max_cache_size,
            ttl=self.config.cache_ttl
        )

        self.speculation_engine = SpeculationEngine(
            agent=self.agent,
            config=self.config,
            executor=agent.executor,
            cache=self.cache,
            pattern_detector=self.pattern_detector
        )

        # Background tasks
        self.running = False
        self.speculation_task = None
        self.cleanup_task = None

        print(f"🔮 [PREDICT] Predictive system initialized")

    async def start(self):
        """Start predictive system background tasks"""
        if not self.enabled:
            return

        self.running = True

        # Start speculation loop (every 10 seconds)
        self.speculation_task = asyncio.create_task(self._speculation_loop())

        # Start cache cleanup loop (every 60 seconds)
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

        print(f"🔮 [PREDICT] Predictive system STARTED")

    async def stop(self):
        """Stop predictive system"""
        if not self.enabled:
            return

        self.running = False

        if self.speculation_task:
            self.speculation_task.cancel()

        if self.cleanup_task:
            self.cleanup_task.cancel()

        print(f"🔮 [PREDICT] Predictive system stopped")

    def observe_job_submission(self, job: dict):
        """
        Call this when a job is submitted to the network

        This trains the pattern detector
        """
        if not self.enabled:
            return

        self.pattern_detector.observe_job(job)

    def check_cache(self, job: dict):
        """
        Check if we have a pre-executed result for this job

        Returns:
            Cached result if available, None otherwise
        """
        if not self.enabled:
            return None

        result = self.cache.get(job)

        if result:
            # CACHE HIT! Report to speculation engine
            fingerprint = self.cache._compute_fingerprint(job)
            self.speculation_engine.report_cache_hit(fingerprint)

        return result

    async def _speculation_loop(self):
        """Background loop for speculation"""
        while self.running:
            try:
                await asyncio.sleep(10)  # Every 10 seconds

                # Try to speculate on predicted jobs
                await self.speculation_engine.speculate()

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ [PREDICT] Speculation loop error: {e}")
                await asyncio.sleep(5)

    async def _cleanup_loop(self):
        """Background loop for cache cleanup"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Every minute

                # Clean up expired cache entries
                self.cache.cleanup_expired()

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ [PREDICT] Cleanup loop error: {e}")
                await asyncio.sleep(30)

    def get_stats(self) -> dict:
        """Get predictive system statistics"""
        if not self.enabled:
            return {'enabled': False}

        stats = {
            'enabled': True,
            'pattern_detector': self.pattern_detector.get_stats(),
            'cache': self.cache.get_stats(),
            'speculation': self.speculation_engine.get_stats()
        }

        # Add RL policy stats if available
        if self.speculation_engine.rl_policy:
            stats['rl_policy'] = self.speculation_engine.rl_policy.get_stats()

        return stats
