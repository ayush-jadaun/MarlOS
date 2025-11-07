"""
Reputation Gossip Protocol
Byzantine Fault Tolerant reputation sharing across the swarm
"""
import asyncio
import time
from typing import Dict, Set, List
from collections import defaultdict
from ..p2p.protocol import MessageType


class ReputationGossip:
    """
    Implements gossip protocol for reputation sharing
    Includes Byzantine Fault Tolerance
    """
    
    def __init__(self, node_id: str, p2p_node, reputation_system):
        self.node_id = node_id
        self.p2p = p2p_node
        self.reputation = reputation_system
        
        # Reputation reports (peer_id -> {reporter_id: score})
        self.reputation_reports: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Consensus tracking
        self.consensus_threshold = 0.67  # 2/3 majority for BFT
        
        # Gossip config
        self.gossip_interval = 30  # seconds
        self.running = False
    
    async def start(self):
        """Start gossip protocol"""
        self.running = True
        asyncio.create_task(self._gossip_loop())
        print("[GOSSIP] Reputation gossip started")
    
    async def stop(self):
        """Stop gossip protocol"""
        self.running = False
    
    async def _gossip_loop(self):
        """Periodically share reputation updates"""
        while self.running:
            await asyncio.sleep(self.gossip_interval)
            await self._broadcast_reputation_digest()
    
    async def _broadcast_reputation_digest(self):
        """Broadcast reputation digest to peers"""
        # Get all peer trust scores
        peer_scores = self.reputation.peer_trust_scores.copy()
        
        # Include own score
        peer_scores[self.node_id] = self.reputation.get_my_trust_score()
        
        # Broadcast digest
        await self.p2p.broadcast_message(
            MessageType.REPUTATION_UPDATE,
            digest=peer_scores,
            reporter=self.node_id,
            timestamp=time.time()
        )
    
    def receive_reputation_report(self, report: dict):
        """
        Receive reputation report from peer
        
        Implements Byzantine Fault Tolerance:
        - Requires 2/3 consensus before accepting
        - Detects conflicting reports
        - Identifies Byzantine nodes
        """
        reporter_id = report['node_id']
        digest = report.get('digest', {})
        
        # Store reports
        for subject_id, score in digest.items():
            if subject_id not in self.reputation_reports:
                self.reputation_reports[subject_id] = {}
            
            self.reputation_reports[subject_id][reporter_id] = score
        
        # Check for consensus on each peer
        for subject_id in self.reputation_reports.keys():
            consensus_score = self._calculate_consensus(subject_id)
            
            if consensus_score is not None:
                # Update local reputation
                current_score = self.reputation.get_peer_trust(subject_id)
                
                # Only update if significant difference
                if abs(consensus_score - current_score) > 0.05:
                    self.reputation.update_peer_trust(
                        subject_id,
                        consensus_score,
                        "consensus",
                        f"Network consensus: {consensus_score:.3f}"
                    )
    
    def _calculate_consensus(self, subject_id: str) -> float:
        """
        Calculate consensus score using Byzantine Fault Tolerance
        
        Requires 2/3 of reporters to agree (within tolerance)
        """
        reports = self.reputation_reports.get(subject_id, {})
        
        if len(reports) < 3:
            # Need at least 3 reports for BFT
            return None
        
        # Get all scores
        scores = list(reports.values())
        
        # Sort scores
        scores.sort()
        
        # Find median (robust against Byzantine nodes)
        median_idx = len(scores) // 2
        median_score = scores[median_idx]
        
        # Count how many agree with median (within 0.1 tolerance)
        tolerance = 0.1
        agreements = sum(1 for s in scores if abs(s - median_score) < tolerance)
        
        # Check if we have 2/3 consensus
        if agreements / len(scores) >= self.consensus_threshold:
            return median_score
        
        return None
    
    def detect_byzantine_reporters(self) -> Set[str]:
        """
        Detect Byzantine (malicious) reporters
        
        Reporters who consistently give outlier scores
        """
        byzantine_nodes = set()
        
        for subject_id, reports in self.reputation_reports.items():
            if len(reports) < 5:
                continue  # Need enough reports
            
            scores = list(reports.values())
            median_score = sorted(scores)[len(scores) // 2]
            
            # Find reporters with outlier scores
            for reporter_id, score in reports.items():
                if abs(score - median_score) > 0.3:  # Large deviation
                    byzantine_nodes.add(reporter_id)
        
        return byzantine_nodes
    
    async def report_byzantine_node(self, byzantine_id: str):
        """Report detected Byzantine node to swarm"""
        print(f"🚨 [GOSSIP] Byzantine node detected: {byzantine_id}")
        
        await self.p2p.broadcast_message(
            MessageType.REPUTATION_UPDATE,
            subject_node_id=byzantine_id,
            event="byzantine_detected",
            reason="Consistently provides outlier reputation scores",
            reporter=self.node_id
        )
        
        # Quarantine locally
        self.reputation.quarantine_peer(byzantine_id, "Byzantine behavior")