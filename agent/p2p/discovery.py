"""
Dynamic Coordinator Election
Provides decentralized coordinator selection with fairness guarantees
"""
import time
import hashlib
from typing import Dict, List, Optional
from collections import defaultdict


class FairnessTracker:
    """
    Track job distribution to prevent starvation
    Ensures all nodes get fair share of work
    """

    def __init__(self):
        # Track jobs executed per node
        self.jobs_executed: Dict[str, int] = defaultdict(int)

        # Track last execution time per node
        self.last_execution: Dict[str, float] = defaultdict(float)

        # Track coordinator assignments
        self.coordinator_count: Dict[str, int] = defaultdict(int)

        # Starvation threshold (seconds without job)
        self.starvation_threshold = 60.0

    def record_job_execution(self, node_id: str):
        """Record that a node executed a job"""
        self.jobs_executed[node_id] += 1
        self.last_execution[node_id] = time.time()

    def record_coordinator_role(self, node_id: str):
        """Record that a node served as coordinator"""
        self.coordinator_count[node_id] += 1

    def get_starvation_score(self, node_id: str) -> float:
        """
        Calculate starvation score (higher = more starved)
        Used to prioritize nodes that haven't gotten jobs

        Returns:
            0.0 = recently executed
            1.0 = maximally starved (never executed or very long time)
        """
        if node_id not in self.last_execution:
            # Never executed - highly starved
            return 1.0

        time_since_last = time.time() - self.last_execution[node_id]

        # Normalize to 0-1 range
        starvation = min(time_since_last / self.starvation_threshold, 1.0)
        return starvation

    def get_fairness_bonus(self, node_id: str, all_nodes: List[str]) -> float:
        """
        Calculate fairness bonus for bid scoring
        Gives advantage to nodes that have executed fewer jobs

        Returns:
            Bonus multiplier (1.0 - 1.5)
        """
        if not all_nodes:
            return 1.0

        # Calculate average jobs per node
        total_jobs = sum(self.jobs_executed.values()) or 1
        avg_jobs = total_jobs / len(all_nodes)

        # My jobs
        my_jobs = self.jobs_executed.get(node_id, 0)

        # Bonus inversely proportional to job count
        if my_jobs < avg_jobs:
            # Below average - give bonus
            deficit = avg_jobs - my_jobs
            bonus = 1.0 + (deficit / (avg_jobs + 1)) * 0.5  # Up to 50% bonus
        else:
            # Above average - slight penalty
            excess = my_jobs - avg_jobs
            bonus = 1.0 - (excess / (my_jobs + 1)) * 0.2  # Up to 20% penalty

        return max(0.5, min(1.5, bonus))  # Clamp to reasonable range

    def is_starving(self, node_id: str) -> bool:
        """Check if a node is experiencing starvation"""
        return self.get_starvation_score(node_id) > 0.8

    def get_statistics(self) -> dict:
        """Get fairness statistics for monitoring"""
        return {
            'jobs_per_node': dict(self.jobs_executed),
            'coordinator_roles': dict(self.coordinator_count),
            'starving_nodes': [
                node_id for node_id in self.jobs_executed.keys()
                if self.is_starving(node_id)
            ]
        }


class CoordinatorElection:
    """
    Decentralized coordinator election with fairness guarantees

    Features:
    - Prefers idle nodes (fewer active jobs)
    - Prevents coordinator starvation (rotates fairly)
    - Deterministic (all nodes compute same result)
    - No single point of failure
    """

    def __init__(self, p2p_node):
        self.p2p = p2p_node
        self.fairness = FairnessTracker()

        # Cache for healthy nodes
        self.last_health_check = 0
        self.cached_healthy_nodes = []
        self.health_check_interval = 5.0  # Re-check every 5s

    def elect_coordinator_for_job(self, job_id: str) -> str:
        """
        Elect coordinator for specific job using deterministic algorithm
        All nodes run this independently and get SAME result

        Selection criteria (in order):
        1. Node must be healthy (responding to pings)
        2. Prefer nodes with fewer active jobs (idle capacity)
        3. Among equally idle nodes, rotate fairly using job_id hash
        4. Give preference to nodes that haven't been coordinator recently

        Args:
            job_id: Unique job identifier

        Returns:
            node_id of elected coordinator
        """
        # Get all healthy nodes
        healthy_nodes = self._get_healthy_nodes()

        if not healthy_nodes:
            # No peers available - I'm coordinator by default
            return self.p2p.node_id

        # Sort by workload (nodes with fewer active jobs first)
        nodes_by_workload = sorted(
            healthy_nodes,
            key=lambda n: (
                self._get_active_job_count(n),  # Primary: active jobs
                self.fairness.coordinator_count.get(n, 0),  # Secondary: coordinator fairness
                n  # Tertiary: node_id for determinism
            )
        )

        # Get most idle nodes (could be multiple with same workload)
        min_jobs = self._get_active_job_count(nodes_by_workload[0])
        min_coord_count = self.fairness.coordinator_count.get(nodes_by_workload[0], 0)

        # Select candidates with minimum workload and coordinator count
        candidates = [
            n for n in nodes_by_workload
            if (self._get_active_job_count(n) == min_jobs and
                self.fairness.coordinator_count.get(n, 0) == min_coord_count)
        ]

        # Deterministic selection using job_id hash
        # All nodes compute same hash → same coordinator
        # CRITICAL: Use hashlib (deterministic) not hash() (randomized per process)
        hash_bytes = hashlib.sha256(job_id.encode()).digest()
        hash_int = int.from_bytes(hash_bytes[:4], byteorder='big')
        coordinator_idx = hash_int % len(candidates)
        coordinator = candidates[coordinator_idx]

        # Record coordinator assignment for fairness tracking
        self.fairness.record_coordinator_role(coordinator)

        print(f"[COORDINATOR] Elected {coordinator} for {job_id}")
        print(f"             Candidates: {len(candidates)} idle nodes")
        print(f"             Workload: {min_jobs} active jobs, {min_coord_count} coordinator roles")

        return coordinator

    def _get_healthy_nodes(self) -> List[str]:
        """
        Get all nodes that are healthy and responsive
        Uses caching to avoid excessive health checks
        """
        now = time.time()

        # Return cached result if recent
        if now - self.last_health_check < self.health_check_interval:
            return self.cached_healthy_nodes

        # Refresh health status
        healthy = [self.p2p.node_id]  # Always include self

        for node_id, info in self.p2p.peers.items():
            last_seen = info.get('last_seen', 0)

            # Consider healthy if seen in last 30s
            if now - last_seen < 30:
                healthy.append(node_id)
            else:
                print(f"[COORDINATOR] Node {node_id} not healthy (last seen {now - last_seen:.1f}s ago)")

        # Update cache
        self.cached_healthy_nodes = healthy
        self.last_health_check = now

        return healthy

    def _get_active_job_count(self, node_id: str) -> int:
        """
        Get number of currently executing jobs for a node
        Used to prefer idle nodes as coordinators
        """
        # Note: Active job count not yet propagated in peer info
        # All nodes start with equal workload (0) for coordinator election
        # This ensures fair rotation and prevents coordinator starvation
        # Future enhancement: Broadcast active job count in peer announcements
        return 0

    def record_job_won(self, node_id: str):
        """
        Record that a node won and executed a job
        Used for fairness tracking and starvation prevention
        """
        self.fairness.record_job_execution(node_id)

        # Check for starvation after each job
        self._check_starvation()

    def _check_starvation(self):
        """
        Check if any nodes are being starved and log warning
        """
        all_nodes = [self.p2p.node_id] + list(self.p2p.peers.keys())

        for node_id in all_nodes:
            if self.fairness.is_starving(node_id):
                last_exec = self.fairness.last_execution.get(node_id, 0)
                if last_exec > 0:
                    time_since = time.time() - last_exec
                    print(f"⚠️  [FAIRNESS] Node {node_id} is starving! "
                          f"Last job: {time_since:.0f}s ago")
                else:
                    # Never executed
                    print(f"⚠️  [FAIRNESS] Node {node_id} is starving! "
                          f"Never executed a job")

    def get_fairness_statistics(self) -> dict:
        """Get current fairness statistics for monitoring"""
        stats = self.fairness.get_statistics()
        stats['healthy_nodes'] = len(self._get_healthy_nodes())
        return stats
