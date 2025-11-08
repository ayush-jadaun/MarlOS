"""
Result Cache for Pre-Executed Jobs
Stores speculative execution results with TTL
"""

import time
import hashlib
from typing import Optional, Dict
from collections import OrderedDict


class ResultCache:
    """
    LRU cache with TTL for pre-executed job results

    When a job is pre-executed speculatively, the result is stored here.
    If the real job arrives before TTL expires, instant cache hit!
    """

    def __init__(self, max_size: int = 100, ttl: int = 300):
        """
        Args:
            max_size: Maximum number of cached results
            ttl: Time to live for cached results (seconds)
        """
        self.max_size = max_size
        self.ttl = ttl

        # LRU cache: fingerprint -> {result, timestamp, job}
        self.cache: OrderedDict[str, dict] = OrderedDict()

        # Statistics
        self.total_predictions = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.expired_entries = 0

        print(f"[CACHE] Result cache initialized (size={max_size}, ttl={ttl}s)")

    def store(self, job: dict, result: dict, fingerprint: Optional[str] = None):
        """
        Store a pre-executed result in cache

        Args:
            job: The job that was pre-executed
            result: The execution result
            fingerprint: Optional pre-computed fingerprint
        """
        if fingerprint is None:
            fingerprint = self._compute_fingerprint(job)

        # Check cache size limit
        if len(self.cache) >= self.max_size:
            # Remove oldest entry (LRU)
            oldest = next(iter(self.cache))
            self.cache.pop(oldest)
            print(f" [CACHE] Evicted oldest entry (cache full)")

        # Store with timestamp
        self.cache[fingerprint] = {
            'job': job,
            'result': result,
            'stored_at': time.time(),
            'job_id': job.get('job_id', 'unknown')
        }

        # Move to end (most recently used)
        self.cache.move_to_end(fingerprint)

        self.total_predictions += 1

        print(f"[CACHE] Stored prediction for job {job.get('job_type')} (fingerprint={fingerprint[:8]}...)")

    def get(self, job: dict, fingerprint: Optional[str] = None) -> Optional[dict]:
        """
        Try to get cached result for a job

        Returns:
            Cached result dict if found and not expired, None otherwise
        """
        if fingerprint is None:
            fingerprint = self._compute_fingerprint(job)

        if fingerprint not in self.cache:
            self.cache_misses += 1
            return None

        entry = self.cache[fingerprint]
        current_time = time.time()
        age = current_time - entry['stored_at']

        # Check if expired
        if age > self.ttl:
            print(f"[CACHE] Entry expired (age={age:.1f}s)")
            self.cache.pop(fingerprint)
            self.expired_entries += 1
            self.cache_misses += 1
            return None

        # CACHE HIT! 🎉
        self.cache_hits += 1

        # Move to end (most recently used)
        self.cache.move_to_end(fingerprint)

        print(f"*** [CACHE] CACHE HIT! Result ready instantly (saved {age:.1f}s of compute) ***")

        return entry['result']

    def _compute_fingerprint(self, job: dict) -> str:
        """
        Compute fingerprint for job (must match pattern detector)
        """
        job_type = job.get('job_type', 'unknown')
        params = job.get('params', {})

        param_str = str(sorted(params.items()))
        content = f"{job_type}:{param_str}"

        return hashlib.md5(content.encode()).hexdigest()[:16]

    def cleanup_expired(self):
        """Remove all expired entries from cache"""
        current_time = time.time()
        expired_keys = []

        for fingerprint, entry in self.cache.items():
            age = current_time - entry['stored_at']
            if age > self.ttl:
                expired_keys.append(fingerprint)

        for key in expired_keys:
            self.cache.pop(key)
            self.expired_entries += 1

        if expired_keys:
            print(f"[CACHE] Cleaned up {len(expired_keys)} expired entries")

    def get_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total_requests = self.cache_hits + self.cache_misses
        if total_requests == 0:
            return 0.0
        return (self.cache_hits / total_requests) * 100

    def get_stats(self) -> dict:
        """Get cache statistics"""
        return {
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'total_predictions': self.total_predictions,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': self.get_hit_rate(),
            'expired_entries': self.expired_entries
        }
