"""
Job Router - Forward jobs to better peers
Implements intelligent job forwarding when node can't handle a job
"""
import asyncio
import time
from typing import Optional, List, Dict
from ..p2p.protocol import MessageType


class JobRouter:
    """
    Routes jobs to better-suited peers
    """
    
    def __init__(self, node_id: str, p2p_node):
        self.node_id = node_id
        self.p2p = p2p_node
        
        # Peer capabilities cache
        self.peer_capabilities: Dict[str, List[str]] = {}
        self.peer_scores: Dict[str, float] = {}
        
        # Forwarding stats
        self.jobs_forwarded = 0
        self.successful_forwards = 0
    
    async def forward_job(self, job: dict, reason: str) -> Optional[str]:
        """
        Forward job to a better-suited peer
        
        Returns: peer_id if forwarded successfully, None otherwise
        """
        job_id = job['job_id']
        job_type = job['job_type']
        
        print(f"[ROUTER] Forwarding job {job_id} ({job_type}): {reason}")
        
        # Find best peer
        best_peer = await self._find_best_peer(job)
        
        if not best_peer:
            print(f"[ROUTER] No suitable peer found for {job_id}")
            return None
        
        # Broadcast forward message
        await self.p2p.broadcast_message(
            MessageType.JOB_FORWARD,
            job_id=job_id,
            from_node=self.node_id,
            to_node=best_peer,
            job=job,
            reason=reason
        )
        
        self.jobs_forwarded += 1
        
        print(f"[ROUTER] Forwarded {job_id} to {best_peer}")
        
        return best_peer
    
    async def _find_best_peer(self, job: dict) -> Optional[str]:
        """
        Find the best peer to handle this job
        
        Criteria:
        - Has required capabilities
        - High trust score
        - Low current load
        - Fast response time
        """
        job_type = job['job_type']
        requirements = job.get('requirements', [])
        
        # Get all connected peers
        peers = self.p2p.get_peers()
        
        if not peers:
            return None
        
        # Score each peer
        peer_scores = {}
        
        for peer_id, peer_info in peers.items():
            # Skip self
            if peer_id == self.node_id:
                continue
            
            score = 0.0
            
            # 1. Capability match (50% weight)
            capabilities = peer_info.get('capabilities', [])
            
            if job_type not in capabilities:
                continue  # Can't do this job type
            
            capability_score = 1.0
            
            # Check requirements
            for req in requirements:
                if req not in capabilities:
                    capability_score *= 0.5
            
            score += capability_score * 0.5
            
            # 2. Trust score (30% weight)
            trust = peer_info.get('trust_score', 0.5)
            score += trust * 0.3
            
            # 3. Load (20% weight) - estimate from last announcement
            # Lower is better
            last_seen = peer_info.get('last_seen', 0)
            freshness = max(0, 1.0 - (time.time() - last_seen) / 60.0)
            score += freshness * 0.2
            
            peer_scores[peer_id] = score
        
        if not peer_scores:
            return None
        
        # Return peer with highest score
        best_peer = max(peer_scores.items(), key=lambda x: x[1])
        
        return best_peer[0]
    
    def update_peer_capabilities(self, peer_id: str, capabilities: List[str]):
        """Update cached peer capabilities"""
        self.peer_capabilities[peer_id] = capabilities
    
    def record_forward_success(self, peer_id: str):
        """Record successful forward"""
        self.successful_forwards += 1
        self.peer_scores[peer_id] = self.peer_scores.get(peer_id, 0.5) + 0.1
    
    def record_forward_failure(self, peer_id: str):
        """Record failed forward"""
        self.peer_scores[peer_id] = self.peer_scores.get(peer_id, 0.5) - 0.2
    
    def get_forwarding_stats(self) -> dict:
        """Get forwarding statistics"""
        success_rate = (
            self.successful_forwards / self.jobs_forwarded 
            if self.jobs_forwarded > 0 else 0.0
        )
        
        return {
            'jobs_forwarded': self.jobs_forwarded,
            'successful_forwards': self.successful_forwards,
            'success_rate': success_rate,
            'known_peers': len(self.peer_capabilities)
        }


# Integration with main agent
# In agent/main.py, add this to _handle_new_job():

"""
elif action == Action.FORWARD:
    # Forward to better peer
    best_peer = await self.router.forward_job(job_message, "RL decided to forward")
    
    if best_peer:
        # Record for RL learning
        self.rl_policy.record_transition(
            state=current_state,
            action=Action.FORWARD,
            reward=0.2,  # Small reward for smart forwarding
            next_state=next_state,
            done=False
        )
"""