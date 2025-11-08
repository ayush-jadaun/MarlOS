"""
Pattern Detection for Predictive Pre-Execution
Learns job patterns: repeated jobs, sequences, time-based patterns
"""

import time
import hashlib
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional
import numpy as np


IGNORE_KEYS = {
    'job_id', 'payment', 'priority', 'deadline', 'timestamp', 'is_speculative', 
    'fingerprint', 'job_type', 'status', 'output', 'error', 'start_time', 
    'end_time', 'duration', 'node_id', 'message_id', 'signature'
}

class PatternDetector:
    """
    Detects predictable patterns in job submissions

    Pattern Types:
    1. Repeated Jobs - Same job submitted multiple times
    2. Job Sequences - Job B always follows Job A
    3. Time Patterns - Jobs at specific times (hourly, daily)
    """

    def __init__(self, min_occurrences: int = 3):
        """
        Args:
            min_occurrences: Minimum times pattern must occur before prediction
        """
        self.min_occurrences = min_occurrences

        # Pattern 1: Repeated jobs (fingerprint -> timestamps)
        self.job_fingerprints: Dict[str, List[float]] = defaultdict(list)

        # Pattern 2: Job sequences (prev_type -> next_type -> count)
        self.job_sequences: Dict[Tuple[str, str], int] = defaultdict(int)
        self.job_history: deque = deque(maxlen=100)  # Last 100 jobs

        # Pattern 3: Time-based patterns (hour -> job_type -> count)
        self.hourly_patterns: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        # Statistics
        self.total_jobs_seen = 0
        self.patterns_detected = 0

        print(f"[PREDICT] Pattern detector initialized (min_occurrences={min_occurrences})")

    def observe_job(self, job: dict):
            """
            Observe a job submission and update pattern tracking
            Call this every time a job is submitted (before execution)
            """
            global IGNORE_KEYS # Use the list from top of file
            self.total_jobs_seen += 1

            job_type = job.get('job_type', 'unknown')
            timestamp = time.time()

            # Track Pattern 1: Repeated jobs
            fingerprint = self._compute_fingerprint(job)
            self.job_fingerprints[fingerprint].append(timestamp)

            # --- FIX: Find and save the REAL job parameters ---
            params = {}
            for key, value in job.items():
                if key not in IGNORE_KEYS:
                    params[key] = value
            
            # Track Pattern 2: Sequences
            if len(self.job_history) > 0:
                prev_type = self.job_history[-1]['type']
                self.job_sequences[(prev_type, job_type)] += 1

            self.job_history.append({
                'type': job_type,
                'fingerprint': fingerprint,
                'timestamp': timestamp,
                'params': params  # <-- Now saves {'command': '...'}
            })

            # Track Pattern 3: Time patterns
            hour = time.localtime(timestamp).tm_hour
            self.hourly_patterns[hour][job_type] += 1
    def predict_next_jobs(self) -> List[dict]:
        """
        Predict what jobs are likely to be submitted soon

        Returns:
            List of predictions: [{'job': dict, 'confidence': float, 'reason': str}, ...]
        """
        predictions = []

        # Prediction 1: Repeated jobs due soon
        predictions.extend(self._predict_repeated_jobs())

        # Prediction 2: Sequence continuation
        predictions.extend(self._predict_sequences())

        # Prediction 3: Time-based predictions
        predictions.extend(self._predict_time_patterns())

        # Sort by confidence (highest first)
        predictions.sort(key=lambda x: x['confidence'], reverse=True)

        return predictions

    def _predict_repeated_jobs(self) -> List[dict]:
        """Predict jobs that repeat on a schedule"""
        predictions = []
        current_time = time.time()

        for fingerprint, timestamps in self.job_fingerprints.items():
            if len(timestamps) < self.min_occurrences:
                continue  # Not enough history

            # Calculate average interval between submissions
            if len(timestamps) >= 2:
                intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
                avg_interval = np.mean(intervals)
                std_interval = np.std(intervals)

                # Time since last submission
                time_since_last = current_time - timestamps[-1]

                # Is it due soon? (within 90-110% of average interval)
                if avg_interval > 0 and 0.9 * avg_interval <= time_since_last <= 1.1 * avg_interval:
                    # High confidence if pattern is consistent (low std deviation)
                    consistency = 1.0 - min(std_interval / avg_interval, 1.0) if avg_interval > 0 else 0.5
                    confidence = (len(timestamps) / (len(timestamps) + 2)) * consistency

                    if confidence >= 0.75:  # High confidence threshold
                        predictions.append({
                            'fingerprint': fingerprint,
                            'confidence': confidence,
                            'reason': f"repeated_job (seen {len(timestamps)}x, interval={avg_interval:.1f}s)",
                            'expected_in': avg_interval - time_since_last
                        })

        return predictions

    def _predict_sequences(self) -> List[dict]:
        """Predict next job based on sequence patterns"""
        predictions = []

        if len(self.job_history) == 0:
            return predictions

        # What was the last job type?
        last_job_type = self.job_history[-1]['type']

        # What typically follows this job type?
        for (prev_type, next_type), count in self.job_sequences.items():
            if prev_type == last_job_type and count >= self.min_occurrences:
                # Calculate confidence based on frequency
                total_after_prev = sum(
                    c for (p, n), c in self.job_sequences.items()
                    if p == prev_type
                )

                confidence = count / total_after_prev if total_after_prev > 0 else 0

                if confidence >= 0.70:  # 70% of time this sequence happens
                    predictions.append({
                        'job_type': next_type,
                        'confidence': confidence,
                        'reason': f"sequence ({prev_type} → {next_type}, {count}/{total_after_prev})",
                        'expected_in': 30  # Estimate: 30 seconds after previous
                    })

        return predictions

    def _predict_time_patterns(self) -> List[dict]:
        """Predict jobs based on time-of-day patterns"""
        predictions = []
        current_time = time.time()
        current_hour = time.localtime(current_time).tm_hour
        current_minute = time.localtime(current_time).tm_min

        # Check if we're near the start of an hour (last 2 minutes)
        if current_minute >= 58 or current_minute <= 2:
            # Predict what typically happens at this hour
            next_hour = (current_hour + 1) % 24 if current_minute >= 58 else current_hour

            if next_hour in self.hourly_patterns:
                total_jobs_at_hour = sum(self.hourly_patterns[next_hour].values())

                for job_type, count in self.hourly_patterns[next_hour].items():
                    if count >= self.min_occurrences:
                        confidence = count / max(total_jobs_at_hour, 1)

                        if confidence >= 0.60:  # 60% of jobs at this hour are this type
                            seconds_until_hour = 3600 - (current_minute * 60) if current_minute >= 58 else (60 - current_minute) * 60

                            predictions.append({
                                'job_type': job_type,
                                'confidence': confidence,
                                'reason': f"time_pattern (hour={next_hour}, {count}/{total_jobs_at_hour})",
                                'expected_in': seconds_until_hour
                            })

        return predictions

    def _compute_fingerprint(self, job: dict) -> str:
            """
            Compute unique fingerprint for a job
            Jobs with same type and parameters get same fingerprint
            """
            global IGNORE_KEYS # Use the list from top of file
            
            job_type = job.get('job_type', 'unknown')
            
            # Get all *other* keys as the parameters
            params = {}
            for key, value in job.items():
                if key not in IGNORE_KEYS:
                    params[key] = value
            
            param_str = str(sorted(params.items()))
            content = f"{job_type}:{param_str}"

            return hashlib.md5(content.encode()).hexdigest()[:16]

    def get_stats(self) -> dict:
        """Get pattern detection statistics"""
        return {
            'total_jobs_seen': self.total_jobs_seen,
            'unique_fingerprints': len(self.job_fingerprints),
            'sequence_patterns': len(self.job_sequences),
            'hourly_patterns_tracked': len(self.hourly_patterns),
            'patterns_detected': self.patterns_detected
        }
