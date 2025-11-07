"""
Trust Watchdog - Auto-Quarantine System
Monitors peer behavior and automatically kicks bad actors
"""
import asyncio
import time
from typing import Dict, Set
from collections import defaultdict

from ..config import TrustConfig
from .reputation import ReputationSystem


class TrustWatchdog:
    """
    Monitors the network and automatically quarantines malicious nodes
    """
    
    def __init__(self, reputation_system: ReputationSystem, config: TrustConfig):
        self.reputation = reputation_system
        self.config = config
        
        # Behavior tracking
        self.peer_failures: Dict[str, int] = defaultdict(int)
        self.peer_timeouts: Dict[str, int] = defaultdict(int)
        self.peer_malicious_attempts: Dict[str, int] = defaultdict(int)
        
        # Monitoring
        self.running = False
        self.check_interval = 10  # seconds
    
    async def start(self):
        """Start watchdog monitoring"""
        self.running = True
        print("[WATCHDOG] Started trust monitoring")
        asyncio.create_task(self._monitoring_loop())
    
    async def stop(self):
        """Stop watchdog"""
        self.running = False
    
    async def _monitoring_loop(self):
        """Periodic check of all peers"""
        while self.running:
            await asyncio.sleep(self.check_interval)
            await self._check_all_peers()
    
    async def _check_all_peers(self):
        """Check all peers and quarantine if needed"""
        for peer_id in list(self.reputation.peer_trust_scores.keys()):
            trust = self.reputation.get_peer_trust(peer_id)
            
            # Auto-quarantine if trust too low
            if trust < self.config.quarantine_threshold:
                if not self.reputation.is_peer_quarantined(peer_id):
                    self.reputation.quarantine_peer(peer_id, f"Trust score too low: {trust:.3f}")
                    print(f"🚨 [WATCHDOG] Auto-quarantined {peer_id} (trust={trust:.3f})")
    
    def report_job_failure(self, peer_id: str, job_id: str, reason: str):
        """
        Report that a peer failed a job
        """
        self.peer_failures[peer_id] += 1
        
        # Calculate trust penalty
        current_trust = self.reputation.get_peer_trust(peer_id)
        new_trust = max(0.0, current_trust - self.config.failure_penalty)
        
        self.reputation.update_peer_trust(
            peer_id, 
            new_trust, 
            "failure", 
            f"Job {job_id} failed: {reason}"
        )
        
        print(f"⚠️  [WATCHDOG] Peer {peer_id} failed job: {reason} (failures={self.peer_failures[peer_id]})")
        
        # Escalate if too many failures
        if self.peer_failures[peer_id] >= 3:
            self.reputation.quarantine_peer(peer_id, f"Too many failures: {self.peer_failures[peer_id]}")
    
    def report_job_timeout(self, peer_id: str, job_id: str):
        """
        Report that a peer timed out on a job
        """
        self.peer_timeouts[peer_id] += 1
        
        # Smaller penalty for timeouts
        current_trust = self.reputation.get_peer_trust(peer_id)
        new_trust = max(0.0, current_trust - 0.02)
        
        self.reputation.update_peer_trust(
            peer_id,
            new_trust,
            "timeout",
            f"Job {job_id} timeout"
        )
        
        print(f"⏱️  [WATCHDOG] Peer {peer_id} timeout (timeouts={self.peer_timeouts[peer_id]})")
    
    def report_malicious_activity(self, peer_id: str, activity: str):
        """
        Report malicious behavior (invalid signatures, spam, etc.)
        """
        self.peer_malicious_attempts[peer_id] += 1
        
        # Severe penalty
        current_trust = self.reputation.get_peer_trust(peer_id)
        new_trust = max(0.0, current_trust - self.config.malicious_penalty)
        
        self.reputation.update_peer_trust(
            peer_id,
            new_trust,
            "malicious",
            activity
        )
        
        # Immediate quarantine
        self.reputation.quarantine_peer(peer_id, f"Malicious activity: {activity}")
        
        print(f"🚨 [WATCHDOG] MALICIOUS ACTIVITY from {peer_id}: {activity}")
    
    def report_job_success(self, peer_id: str, job_id: str, on_time: bool = True):
        """
        Report successful job completion by peer
        """
        # Reward peer
        current_trust = self.reputation.get_peer_trust(peer_id)
        delta = self.config.success_reward if on_time else self.config.late_reward
        new_trust = min(1.0, current_trust + delta)
        
        self.reputation.update_peer_trust(
            peer_id,
            new_trust,
            "success",
            f"Job {job_id} completed {'on time' if on_time else '(late)'}"
        )
        
        # Reset failure counters on success
        if self.peer_failures[peer_id] > 0:
            self.peer_failures[peer_id] = max(0, self.peer_failures[peer_id] - 1)
    
    def can_trust_peer(self, peer_id: str, min_trust: float = 0.3) -> bool:
        """
        Check if a peer can be trusted for a job
        """
        if self.reputation.is_peer_quarantined(peer_id):
            return False
        
        trust = self.reputation.get_peer_trust(peer_id)
        return trust >= min_trust
    
    def get_watchdog_stats(self) -> dict:
        """Get watchdog statistics"""
        return {
            'monitored_peers': len(self.reputation.peer_trust_scores),
            'quarantined_peers': len(self.reputation.quarantined_nodes),
            'total_failures_tracked': sum(self.peer_failures.values()),
            'total_timeouts_tracked': sum(self.peer_timeouts.values()),
            'malicious_attempts_blocked': sum(self.peer_malicious_attempts.values())
        }
