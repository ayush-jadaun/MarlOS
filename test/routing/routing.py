"""
Test suite for JobRouter
Tests job forwarding logic and peer selection
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List
import sys
sys.path.insert(0, '../')


from agent.bidding.router import JobRouter
from agent.p2p.protocol import MessageType

class MockP2PNode:
    """Mock P2P node for testing"""
    
    def __init__(self):
        self.peers = {}
        self.broadcast_calls = []
    
    def get_peers(self) -> Dict:
        """Return mock peers"""
        return self.peers
    
    async def broadcast_message(self, msg_type: MessageType, **kwargs):
        """Record broadcast calls"""
        self.broadcast_calls.append({
            'type': msg_type,
            'data': kwargs
        })
    
    def add_peer(self, peer_id: str, capabilities: List[str], 
                 trust_score: float = 0.5, last_seen: float = None):
        """Add a mock peer"""
        if last_seen is None:
            last_seen = time.time()
        
        self.peers[peer_id] = {
            'capabilities': capabilities,
            'trust_score': trust_score,
            'last_seen': last_seen
        }


@pytest.fixture
def mock_p2p():
    """Fixture for mock P2P node"""
    return MockP2PNode()


@pytest.fixture
def router(mock_p2p):
    """Fixture for JobRouter"""
    return JobRouter(node_id="test-node-1", p2p_node=mock_p2p)


@pytest.fixture
def sample_job():
    """Fixture for sample job"""
    return {
        'job_id': 'job-123',
        'job_type': 'data_processing',
        'requirements': ['fast_cpu', 'large_memory'],
        'priority': 0.8,
        'payload': {'data': 'test'}
    }


class TestJobRouter:
    """Test JobRouter functionality"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, router):
        """Test router initialization"""
        assert router.node_id == "test-node-1"
        assert router.jobs_forwarded == 0
        assert router.successful_forwards == 0
        assert len(router.peer_capabilities) == 0
        assert len(router.peer_scores) == 0
    
    @pytest.mark.asyncio
    async def test_forward_job_no_peers(self, router, sample_job):
        """Test forwarding when no peers available"""
        result = await router.forward_job(sample_job, "No local capacity")
        
        assert result is None
        assert router.jobs_forwarded == 0
    
    @pytest.mark.asyncio
    async def test_forward_job_success(self, router, mock_p2p, sample_job):
        """Test successful job forwarding"""
        # Add capable peer
        mock_p2p.add_peer(
            'peer-1',
            capabilities=['data_processing', 'fast_cpu', 'large_memory'],
            trust_score=0.9
        )
        
        result = await router.forward_job(sample_job, "Better peer available")
        
        assert result == 'peer-1'
        assert router.jobs_forwarded == 1
        assert len(mock_p2p.broadcast_calls) == 1
        
        broadcast = mock_p2p.broadcast_calls[0]
        assert broadcast['type'] == MessageType.JOB_FORWARD
        assert broadcast['data']['job_id'] == 'job-123'
        assert broadcast['data']['to_node'] == 'peer-1'
        assert broadcast['data']['reason'] == "Better peer available"
    
    @pytest.mark.asyncio
    async def test_find_best_peer_capability_match(self, router, mock_p2p, sample_job):
        """Test peer selection based on capabilities"""
        # Add peers with different capabilities
        mock_p2p.add_peer('peer-1', ['data_processing'], trust_score=0.9)
        mock_p2p.add_peer('peer-2', ['data_processing', 'fast_cpu'], trust_score=0.8)
        mock_p2p.add_peer('peer-3', ['data_processing', 'fast_cpu', 'large_memory'], trust_score=0.7)
        
        best_peer = await router._find_best_peer(sample_job)
        
        # peer-3 should win despite lower trust (has all requirements)
        assert best_peer == 'peer-3'
    
    @pytest.mark.asyncio
    async def test_find_best_peer_trust_score(self, router, mock_p2p, sample_job):
        """Test peer selection based on trust score"""
        # Add peers with same capabilities but different trust
        mock_p2p.add_peer('peer-1', ['data_processing', 'fast_cpu', 'large_memory'], trust_score=0.5)
        mock_p2p.add_peer('peer-2', ['data_processing', 'fast_cpu', 'large_memory'], trust_score=0.9)
        
        best_peer = await router._find_best_peer(sample_job)
        
        # peer-2 should win with higher trust
        assert best_peer == 'peer-2'
    
    @pytest.mark.asyncio
    async def test_find_best_peer_freshness(self, router, mock_p2p, sample_job):
        """Test peer selection based on last seen time"""
        current_time = time.time()
        
        # Add peers with same capabilities and trust but different last_seen
        mock_p2p.add_peer('peer-1', ['data_processing', 'fast_cpu', 'large_memory'], 
                         trust_score=0.8, last_seen=current_time - 100)  # Old
        mock_p2p.add_peer('peer-2', ['data_processing', 'fast_cpu', 'large_memory'], 
                         trust_score=0.8, last_seen=current_time)  # Fresh
        
        best_peer = await router._find_best_peer(sample_job)
        
        # peer-2 should win with fresher timestamp
        assert best_peer == 'peer-2'
    
    @pytest.mark.asyncio
    async def test_find_best_peer_no_capable_peers(self, router, mock_p2p, sample_job):
        """Test peer selection when no peer has required capability"""
        # Add peers without the required job_type
        mock_p2p.add_peer('peer-1', ['web_scraping'], trust_score=0.9)
        mock_p2p.add_peer('peer-2', ['image_processing'], trust_score=0.8)
        
        best_peer = await router._find_best_peer(sample_job)
        
        assert best_peer is None
    
    @pytest.mark.asyncio
    async def test_find_best_peer_skips_self(self, router, mock_p2p, sample_job):
        """Test that router skips itself when selecting peers"""
        # Add self as peer
        mock_p2p.add_peer('test-node-1', ['data_processing'], trust_score=1.0)
        
        # Add another peer
        mock_p2p.add_peer('peer-1', ['data_processing'], trust_score=0.5)
        
        best_peer = await router._find_best_peer(sample_job)
        
        # Should select peer-1, not self
        assert best_peer == 'peer-1'
    
    def test_update_peer_capabilities(self, router):
        """Test updating peer capabilities"""
        capabilities = ['data_processing', 'web_scraping']
        router.update_peer_capabilities('peer-1', capabilities)
        
        assert router.peer_capabilities['peer-1'] == capabilities
    
    def test_record_forward_success(self, router):
        """Test recording successful forward"""
        router.record_forward_success('peer-1')
        
        assert router.successful_forwards == 1
        assert router.peer_scores['peer-1'] == 0.6  # 0.5 + 0.1
        
        # Record another success
        router.record_forward_success('peer-1')
        assert router.peer_scores['peer-1'] == 0.7
    
    def test_record_forward_failure(self, router):
        """Test recording failed forward"""
        router.record_forward_failure('peer-1')
        
        assert router.peer_scores['peer-1'] == 0.3  # 0.5 - 0.2
        
        # Record another failure
        router.record_forward_failure('peer-1')
        assert router.peer_scores['peer-1'] == 0.1
    
    def test_get_forwarding_stats_no_forwards(self, router):
        """Test stats with no forwards"""
        stats = router.get_forwarding_stats()
        
        assert stats['jobs_forwarded'] == 0
        assert stats['successful_forwards'] == 0
        assert stats['success_rate'] == 0.0
        assert stats['known_peers'] == 0
    
    def test_get_forwarding_stats_with_data(self, router):
        """Test stats with forward data"""
        router.jobs_forwarded = 10
        router.successful_forwards = 7
        router.update_peer_capabilities('peer-1', ['data_processing'])
        router.update_peer_capabilities('peer-2', ['web_scraping'])
        
        stats = router.get_forwarding_stats()
        
        assert stats['jobs_forwarded'] == 10
        assert stats['successful_forwards'] == 7
        assert stats['success_rate'] == 0.7
        assert stats['known_peers'] == 2
    
    @pytest.mark.asyncio
    async def test_multiple_forwards(self, router, mock_p2p, sample_job):
        """Test forwarding multiple jobs"""
        mock_p2p.add_peer('peer-1', ['data_processing', 'fast_cpu', 'large_memory'], 
                         trust_score=0.9)
        
        # Forward multiple jobs
        job1 = {**sample_job, 'job_id': 'job-1'}
        job2 = {**sample_job, 'job_id': 'job-2'}
        job3 = {**sample_job, 'job_id': 'job-3'}
        
        await router.forward_job(job1, "Reason 1")
        await router.forward_job(job2, "Reason 2")
        await router.forward_job(job3, "Reason 3")
        
        assert router.jobs_forwarded == 3
        assert len(mock_p2p.broadcast_calls) == 3
    
    @pytest.mark.asyncio
    async def test_complex_scoring_scenario(self, router, mock_p2p):
        """Test complex peer scoring with all factors"""
        current_time = time.time()
        
        job = {
            'job_id': 'job-complex',
            'job_type': 'ml_training',
            'requirements': ['gpu', 'large_memory']
        }
        
        # Peer 1: Has all requirements, medium trust, fresh
        mock_p2p.add_peer('peer-1', 
                         ['ml_training', 'gpu', 'large_memory'],
                         trust_score=0.7,
                         last_seen=current_time)
        
        # Peer 2: Has all requirements, high trust, old
        mock_p2p.add_peer('peer-2',
                         ['ml_training', 'gpu', 'large_memory'],
                         trust_score=0.9,
                         last_seen=current_time - 100)
        
        # Peer 3: Missing one requirement, very high trust, fresh
        mock_p2p.add_peer('peer-3',
                         ['ml_training', 'gpu'],
                         trust_score=1.0,
                         last_seen=current_time)
        
        best_peer = await router._find_best_peer(job)
        
        # Should prefer complete capability match
        assert best_peer in ['peer-1', 'peer-2']


class TestJobRouterEdgeCases:
    """Test edge cases and error conditions"""
    
    @pytest.mark.asyncio
    async def test_job_without_requirements(self, router, mock_p2p):
        """Test job with no requirements field"""
        job = {
            'job_id': 'job-simple',
            'job_type': 'simple_task'
        }
        
        mock_p2p.add_peer('peer-1', ['simple_task'], trust_score=0.8)
        
        best_peer = await router._find_best_peer(job)
        assert best_peer == 'peer-1'
    
    @pytest.mark.asyncio
    async def test_peer_without_capabilities(self, router, mock_p2p, sample_job):
        """Test peer with missing capabilities field"""
        mock_p2p.peers['peer-1'] = {
            'trust_score': 0.8,
            'last_seen': time.time()
            # No 'capabilities' field
        }
        
        best_peer = await router._find_best_peer(sample_job)
        assert best_peer is None
    
    @pytest.mark.asyncio
    async def test_peer_with_zero_trust(self, router, mock_p2p, sample_job):
        """Test peer with zero trust score"""
        mock_p2p.add_peer('peer-1', ['data_processing', 'fast_cpu', 'large_memory'],
                         trust_score=0.0)
        mock_p2p.add_peer('peer-2', ['data_processing', 'fast_cpu', 'large_memory'],
                         trust_score=0.1)
        
        best_peer = await router._find_best_peer(sample_job)
        # Should still select a peer even with low trust
        assert best_peer is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])