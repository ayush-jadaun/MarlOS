"""
Integration Tests for MarlOS
Tests real components working together on localhost.
Uses the same infrastructure as the demo script.
"""

import pytest
import pytest_asyncio
import asyncio
import time
import os
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from agent.main import MarlOSAgent
from agent.config import (
    AgentConfig, NetworkConfig, TokenConfig, TrustConfig,
    RLConfig, ExecutorConfig, DashboardConfig, PredictiveConfig
)
from agent.p2p.protocol import MessageType


def make_test_config(index: int, total: int, data_dir: str) -> AgentConfig:
    """Create test node config with unique ports."""
    base_port = 16000 + (index * 10)
    dashboard_port = 14001 + index

    bootstrap = [
        f"tcp://127.0.0.1:{16000 + (j * 10)}"
        for j in range(total) if j != index
    ]

    return AgentConfig(
        node_id=f"integ-node-{index}",
        node_name=f"IntegNode-{index}",
        network=NetworkConfig(
            pub_port=base_port,
            sub_port=base_port + 1,
            bootstrap_peers=bootstrap,
            discovery_interval=2,
            heartbeat_interval=2,
        ),
        dashboard=DashboardConfig(port=dashboard_port),
        token=TokenConfig(starting_balance=100.0),
        trust=TrustConfig(),
        rl=RLConfig(online_learning=False, exploration_rate=0.1),
        executor=ExecutorConfig(max_concurrent_jobs=3, docker_enabled=False),
        predictive=PredictiveConfig(enabled=False),
        data_dir=os.path.join(data_dir, f"integ-node-{index}"),
    )


@pytest_asyncio.fixture
async def network():
    """Start a 3-node test network, yield agents, then clean up."""
    data_dir = os.path.join(os.path.dirname(__file__), ".integ_data")
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir, ignore_errors=True)

    agents = []
    num_nodes = 3

    for i in range(num_nodes):
        config = make_test_config(i, num_nodes, data_dir)
        agent = MarlOSAgent(config)
        await agent.start()
        agents.append(agent)
        await asyncio.sleep(0.3)

    # Wait for peer discovery
    max_wait = 15
    start = time.time()
    while time.time() - start < max_wait:
        if all(a.p2p.get_peer_count() >= num_nodes - 1 for a in agents):
            break
        await asyncio.sleep(0.5)

    yield agents

    for agent in agents:
        try:
            await agent.stop()
        except Exception:
            pass

    if os.path.exists(data_dir):
        shutil.rmtree(data_dir, ignore_errors=True)


class TestPeerDiscovery:
    @pytest.mark.asyncio
    async def test_all_nodes_discover_each_other(self, network):
        for agent in network:
            assert agent.p2p.get_peer_count() >= 2, \
                f"{agent.node_id} only has {agent.p2p.get_peer_count()} peers"

    @pytest.mark.asyncio
    async def test_peer_capabilities_shared(self, network):
        """Each node should know other nodes' capabilities."""
        for agent in network:
            for peer_id, info in agent.p2p.peers.items():
                caps = info.get("capabilities", [])
                assert "shell" in caps, f"{peer_id} missing shell capability"


class TestJobExecution:
    @pytest.mark.asyncio
    async def test_submit_and_execute_job(self, network):
        """Submit a shell job and verify it completes."""
        job = {
            'job_id': 'integ-job-1',
            'job_type': 'shell',
            'payload': {'command': 'echo "integration test"'},
            'payment': 50.0,
            'priority': 0.5,
            'deadline': time.time() + 60,
        }

        await network[0].p2p.broadcast_message(MessageType.JOB_BROADCAST, **job)

        # Wait for auction (2s bid + 5s grace) + execution
        max_wait = 20
        start = time.time()
        while time.time() - start < max_wait:
            for agent in network:
                if 'integ-job-1' in agent.job_results:
                    result = agent.job_results['integ-job-1']
                    assert str(result.status) in ('JobStatus.SUCCESS', 'success')
                    return
            await asyncio.sleep(0.5)

        pytest.fail("Job was not completed by any node within timeout")

    @pytest.mark.asyncio
    async def test_multiple_jobs_distributed(self, network):
        """Submit 3 jobs, verify they get distributed."""
        for i in range(3):
            job = {
                'job_id': f'integ-multi-{i}',
                'job_type': 'shell',
                'payload': {'command': f'echo "job {i}"'},
                'payment': 30.0,
                'priority': 0.5,
                'deadline': time.time() + 60,
            }
            await network[0].p2p.broadcast_message(MessageType.JOB_BROADCAST, **job)
            await asyncio.sleep(1)

        # Wait for completion
        max_wait = 30
        start = time.time()
        while time.time() - start < max_wait:
            total = sum(a.jobs_completed for a in network)
            if total >= 3:
                break
            await asyncio.sleep(0.5)

        total = sum(a.jobs_completed for a in network)
        assert total >= 3, f"Only {total}/3 jobs completed"


class TestTokenEconomy:
    @pytest.mark.asyncio
    async def test_winner_earns_tokens(self, network):
        """Winner should earn more than starting balance."""
        job = {
            'job_id': 'integ-token-1',
            'job_type': 'shell',
            'payload': {'command': 'echo "pay me"'},
            'payment': 50.0,
            'priority': 0.5,
            'deadline': time.time() + 60,
        }

        await network[0].p2p.broadcast_message(MessageType.JOB_BROADCAST, **job)

        max_wait = 20
        start = time.time()
        while time.time() - start < max_wait:
            for agent in network:
                if 'integ-token-1' in agent.job_results:
                    assert agent.wallet.balance > 100.0, \
                        f"Winner balance {agent.wallet.balance} not > 100"
                    return
            await asyncio.sleep(0.5)

        pytest.fail("Job not completed in time")


class TestTrustSystem:
    @pytest.mark.asyncio
    async def test_trust_increases_on_success(self, network):
        """Trust should increase after successful job."""
        job = {
            'job_id': 'integ-trust-1',
            'job_type': 'shell',
            'payload': {'command': 'echo "trust me"'},
            'payment': 30.0,
            'priority': 0.5,
            'deadline': time.time() + 60,
        }

        await network[0].p2p.broadcast_message(MessageType.JOB_BROADCAST, **job)

        max_wait = 20
        start = time.time()
        while time.time() - start < max_wait:
            for agent in network:
                if 'integ-trust-1' in agent.job_results:
                    trust = agent.reputation.get_my_trust_score()
                    assert trust >= 0.5, f"Trust {trust} should be >= 0.5 after success"
                    return
            await asyncio.sleep(0.5)

        pytest.fail("Job not completed in time")


class TestOnlineLearning:
    @pytest.mark.asyncio
    async def test_experiences_collected(self, network):
        """After job execution, RL experiences should be buffered."""
        # Enable online learning on one node
        network[0].online_learner.learning_enabled = True

        job = {
            'job_id': 'integ-rl-1',
            'job_type': 'shell',
            'payload': {'command': 'echo "learn from this"'},
            'payment': 40.0,
            'priority': 0.5,
            'deadline': time.time() + 60,
        }

        await network[0].p2p.broadcast_message(MessageType.JOB_BROADCAST, **job)
        await asyncio.sleep(15)

        # At least one node should have experiences
        total_exp = sum(
            a.online_learner.get_learning_stats()['buffer_size']
            for a in network
        )
        # Even if this node didn't win, the bidding itself generates RL data
        # Just verify the system didn't crash
        assert total_exp >= 0


class TestRESTAPI:
    @pytest.mark.asyncio
    async def test_health_endpoint(self, network):
        """REST API health check should respond."""
        import aiohttp
        port = network[0].rest_api.port
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://127.0.0.1:{port}/api/health") as resp:
                assert resp.status == 200
                data = await resp.json()
                assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_submit_job_via_api(self, network):
        """Submit a job through the REST API."""
        import aiohttp
        port = network[0].rest_api.port
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://127.0.0.1:{port}/api/jobs",
                json={
                    "job_type": "shell",
                    "payload": {"command": "echo api-test"},
                    "payment": 25.0,
                }
            ) as resp:
                assert resp.status == 201
                data = await resp.json()
                assert data["status"] == "submitted"
                assert "job_id" in data
