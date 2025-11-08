"""
Reputation and Trust System
Manages trust scores, self-reward, self-punishment with decay
"""
import time
import json
from pathlib import Path
from typing import Dict, List, Optional
from ..schema.schema import ReputationEvent
from ..config import TrustConfig

# Import trust decay
try:
    from ..economy.fairness import TrustDecay
except ImportError:
    TrustDecay = None


class ReputationSystem:
    """
    Manages node's own reputation and tracks peer reputations
    """
    
    def __init__(self, node_id: str, config: TrustConfig, data_dir: str = "./data", enable_decay: bool = True):
        self.node_id = node_id
        self.config = config

        # Own reputation
        self.my_trust_score = config.starting_trust
        self.reputation_history: List[ReputationEvent] = []

        # INNOVATION: Trust decay
        if TrustDecay and enable_decay:
            self.trust_decay = TrustDecay(decay_rate=0.01, min_trust=config.min_trust)
            print(f"[REPUTATION] Trust decay enabled for {node_id}")
        else:
            self.trust_decay = None
        
        # Peer reputations (node_id -> trust_score)
        self.peer_trust_scores: Dict[str, float] = {}
        self.peer_history: Dict[str, List[ReputationEvent]] = {}
        
        # Quarantine
        self.quarantined_nodes: set = set()
        self.rehabilitation_progress: Dict[str, int] = {}  # node_id -> successful_jobs
        
        # Storage
        self.data_dir = Path(data_dir)
        self.reputation_file = self.data_dir / f"reputation_{node_id}.json"
        
        self._load_reputation()
    
    # ==================== OWN REPUTATION ====================
    
    def reward_success(self, job_id: str, on_time: bool = True) -> float:
        """
        Reward self for successful job completion
        Returns new trust score
        """
        if on_time:
            delta = self.config.success_reward
            reason = "Job completed on time"
        else:
            delta = self.config.late_reward
            reason = "Job completed (late)"
        
        self.my_trust_score = min(self.config.max_trust, self.my_trust_score + delta)
        
        event = ReputationEvent(
            timestamp=time.time(),
            event_type="success" if on_time else "late_success",
            trust_delta=delta,
            trust_after=self.my_trust_score,
            reason=reason,
            job_id=job_id
        )
        
        self.reputation_history.append(event)
        self._save_reputation()
        
        print(f"✅ [TRUST] Self-reward: +{delta:.3f} → Trust: {self.my_trust_score:.3f} ({reason})")
        return self.my_trust_score
    
    def punish_failure(self, job_id: str, reason: str = "Job failed") -> float:
        """
        Punish self for job failure
        Returns new trust score
        """
        delta = -self.config.failure_penalty
        
        self.my_trust_score = max(self.config.min_trust, self.my_trust_score + delta)
        
        event = ReputationEvent(
            timestamp=time.time(),
            event_type="failure",
            trust_delta=delta,
            trust_after=self.my_trust_score,
            reason=reason,
            job_id=job_id
        )
        
        self.reputation_history.append(event)
        self._save_reputation()
        
        print(f"❌ [TRUST] Self-punishment: {delta:.3f} → Trust: {self.my_trust_score:.3f} ({reason})")
        return self.my_trust_score
    
    def punish_malicious(self, reason: str) -> float:
        """
        Severe punishment for malicious behavior
        """
        delta = -self.config.malicious_penalty
        
        self.my_trust_score = max(self.config.min_trust, self.my_trust_score + delta)
        
        event = ReputationEvent(
            timestamp=time.time(),
            event_type="malicious",
            trust_delta=delta,
            trust_after=self.my_trust_score,
            reason=reason,
            job_id=None
        )
        
        self.reputation_history.append(event)
        self._save_reputation()
        
        print(f"🚨 [TRUST] Malicious activity: {delta:.3f} → Trust: {self.my_trust_score:.3f}")
        return self.my_trust_score
    
    def get_my_trust_score(self) -> float:
        """
        Get current trust score with decay applied

        INNOVATION: Trust naturally decays - must stay active to maintain
        """
        # Apply decay if enabled
        if self.trust_decay:
            self.my_trust_score = self.trust_decay.apply_decay(
                node_id=self.node_id,
                current_trust=self.my_trust_score
            )
            self._save_reputation()

        return self.my_trust_score
    
    def am_i_quarantined(self) -> bool:
        """Check if I'm quarantined"""
        return self.my_trust_score < self.config.quarantine_threshold
    
    # ==================== PEER REPUTATION ====================
    
    def update_peer_trust(self, peer_id: str, new_score: float, event_type: str, reason: str):
        """
        Update peer's trust score based on gossip or observation
        """
        old_score = self.peer_trust_scores.get(peer_id, self.config.starting_trust)
        self.peer_trust_scores[peer_id] = new_score
        
        # Record event
        if peer_id not in self.peer_history:
            self.peer_history[peer_id] = []
        
        event = ReputationEvent(
            timestamp=time.time(),
            event_type=event_type,
            trust_delta=new_score - old_score,
            trust_after=new_score,
            reason=reason
        )
        
        self.peer_history[peer_id].append(event)
        
        # Check for quarantine
        if new_score < self.config.quarantine_threshold:
            self.quarantine_peer(peer_id, reason)
        
        self._save_reputation()
    
    def get_peer_trust(self, peer_id: str) -> float:
        """Get peer's trust score"""
        return self.peer_trust_scores.get(peer_id, self.config.starting_trust)
    
    def is_peer_quarantined(self, peer_id: str) -> bool:
        """Check if peer is quarantined"""
        return peer_id in self.quarantined_nodes
    
    def quarantine_peer(self, peer_id: str, reason: str):
        """Quarantine a peer"""
        if peer_id not in self.quarantined_nodes:
            self.quarantined_nodes.add(peer_id)
            self.rehabilitation_progress[peer_id] = 0
            print(f"🚨 [TRUST] Quarantined peer {peer_id}: {reason}")
    
    def unquarantine_peer(self, peer_id: str):
        """Remove peer from quarantine"""
        if peer_id in self.quarantined_nodes:
            self.quarantined_nodes.remove(peer_id)
            self.rehabilitation_progress.pop(peer_id, None)
            print(f"✅ [TRUST] Unquarantined peer {peer_id}")
    
    def record_rehabilitation_progress(self, peer_id: str, success: bool):
        """
        Record rehabilitation job result
        Returns True if peer should be unquarantined
        """
        if peer_id not in self.rehabilitation_progress:
            self.rehabilitation_progress[peer_id] = 0
        
        if success:
            self.rehabilitation_progress[peer_id] += 1
            
            # Check if rehabilitation complete
            if self.rehabilitation_progress[peer_id] >= self.config.rehabilitation_jobs:
                # Increase trust
                new_trust = self.get_peer_trust(peer_id) + 0.15
                self.update_peer_trust(peer_id, new_trust, "rehabilitation", "Completed rehabilitation")
                
                # Unquarantine if above threshold
                if new_trust >= self.config.rehabilitation_threshold:
                    self.unquarantine_peer(peer_id)
                    return True
        else:
            # Failed rehabilitation job - reset progress
            self.rehabilitation_progress[peer_id] = max(0, self.rehabilitation_progress[peer_id] - 1)
        
        return False
    
    def get_trusted_peers(self, min_trust: float = 0.5) -> List[str]:
        """Get list of trusted peers"""
        return [
            peer_id for peer_id, trust in self.peer_trust_scores.items()
            if trust >= min_trust and peer_id not in self.quarantined_nodes
        ]
    
    def get_reputation_stats(self) -> dict:
        """Get reputation statistics"""
        # Count success and failure events
        success_count = sum(1 for e in self.reputation_history if e.event_type in ['success', 'late_success'])
        failure_count = sum(1 for e in self.reputation_history if e.event_type in ['failure', 'timeout'])
        
        return {
            'my_trust': self.my_trust_score,
            'am_i_quarantined': self.am_i_quarantined(),
            'total_peers': len(self.peer_trust_scores),
            'trusted_peers': len(self.get_trusted_peers()),
            'quarantined_peers': len(self.quarantined_nodes),
            'reputation_events': len(self.reputation_history),
            'success_count': success_count,
            'failure_count': failure_count,
            'total_events': len(self.reputation_history)
        }
    
    # ==================== STORAGE ====================
    
    def _save_reputation(self):
        """Save reputation state to disk"""
        data = {
            'node_id': self.node_id,
            'my_trust_score': self.my_trust_score,
            'reputation_history': [e.to_dict() for e in self.reputation_history],
            'peer_trust_scores': self.peer_trust_scores,
            'quarantined_nodes': list(self.quarantined_nodes),
            'rehabilitation_progress': self.rehabilitation_progress
        }
        
        self.reputation_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.reputation_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_reputation(self):
        """Load reputation state from disk"""
        if self.reputation_file.exists():
            try:
                with open(self.reputation_file, 'r') as f:
                    data = json.load(f)
                
                self.my_trust_score = data.get('my_trust_score', self.config.starting_trust)
                self.peer_trust_scores = data.get('peer_trust_scores', {})
                self.quarantined_nodes = set(data.get('quarantined_nodes', []))
                self.rehabilitation_progress = data.get('rehabilitation_progress', {})
                
                # Load history
                self.reputation_history = [
                    ReputationEvent(**e) for e in data.get('reputation_history', [])
                ]
                
                print(f"📊 [TRUST] Loaded reputation: Trust={self.my_trust_score:.3f}")
            except Exception as e:
                print(f"⚠️  [TRUST] Error loading reputation: {e}")