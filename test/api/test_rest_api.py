"""Unit tests for the REST API server."""

import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from agent.api.server import RESTAPIServer


def make_mock_agent():
    """Create a mock MarlOS agent for testing."""
    agent = MagicMock()
    agent.node_id = "test-node"
    agent.config.dashboard.port = 3001
    agent.job_results = {}
    agent.active_job_metadata = {}
    agent.auction.active_auctions = {}
    agent.p2p.peers = {
        "peer-1": {"capabilities": ["shell", "docker"], "ip": "192.168.1.2"},
        "peer-2": {"capabilities": ["shell"], "ip": "192.168.1.3"},
    }
    agent.p2p.broadcast_message = AsyncMock()

    # Wallet
    agent.wallet.balance = 100.0
    agent.wallet.staked = 10.0
    agent.wallet.lifetime_earned = 250.0
    agent.wallet.lifetime_spent = 160.0

    # Trust
    agent.reputation.get_my_trust_score.return_value = 0.75
    agent.reputation.am_i_quarantined.return_value = False
    agent.reputation.get_peer_trust.return_value = 0.6

    # RL
    agent.rl_policy.exploration_rate = 0.1
    agent.online_learner.get_learning_stats.return_value = {
        "learning_enabled": True,
        "buffer_size": 50,
        "updates_performed": 3,
    }

    # Pipeline engine
    agent.pipeline_engine.list_pipelines.return_value = []
    agent.pipeline_engine.get_pipeline.return_value = None

    # get_state
    agent.get_state.return_value = {
        "node_id": "test-node",
        "node_name": "Test Node",
        "peers": 2,
        "trust_score": 0.75,
        "quarantined": False,
        "capabilities": ["shell", "docker"],
        "jobs_completed": 5,
        "jobs_failed": 1,
        "wallet": {"balance": 100.0},
    }

    return agent


@pytest.fixture
def api_server():
    agent = make_mock_agent()
    server = RESTAPIServer(agent, port=0)  # port 0 = auto
    return server


@pytest.fixture
def client(aiohttp_client, api_server):
    return aiohttp_client(api_server.app)


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health(self, client):
        cli = await client
        resp = await cli.get("/api/health")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "ok"
        assert data["node_id"] == "test-node"


class TestStatusEndpoint:
    @pytest.mark.asyncio
    async def test_status(self, client):
        cli = await client
        resp = await cli.get("/api/status")
        assert resp.status == 200
        data = await resp.json()
        assert data["node_id"] == "test-node"
        assert data["peers"] == 2


class TestJobEndpoints:
    @pytest.mark.asyncio
    async def test_submit_job(self, client):
        cli = await client
        resp = await cli.post("/api/jobs", json={
            "job_type": "shell",
            "payload": {"command": "echo hello"},
            "payment": 50.0,
        })
        assert resp.status == 201
        data = await resp.json()
        assert data["status"] == "submitted"
        assert "job_id" in data

    @pytest.mark.asyncio
    async def test_submit_job_missing_type(self, client):
        cli = await client
        resp = await cli.post("/api/jobs", json={
            "payload": {"command": "echo hello"},
        })
        assert resp.status == 400

    @pytest.mark.asyncio
    async def test_submit_job_missing_payload(self, client):
        cli = await client
        resp = await cli.post("/api/jobs", json={
            "job_type": "shell",
        })
        assert resp.status == 400

    @pytest.mark.asyncio
    async def test_list_jobs_empty(self, client):
        cli = await client
        resp = await cli.get("/api/jobs")
        assert resp.status == 200
        data = await resp.json()
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_job_not_found(self, client):
        cli = await client
        resp = await cli.get("/api/jobs/nonexistent")
        assert resp.status == 404


class TestPeerEndpoint:
    @pytest.mark.asyncio
    async def test_get_peers(self, client):
        cli = await client
        resp = await cli.get("/api/peers")
        assert resp.status == 200
        data = await resp.json()
        assert data["count"] == 2


class TestWalletEndpoint:
    @pytest.mark.asyncio
    async def test_get_wallet(self, client):
        cli = await client
        resp = await cli.get("/api/wallet")
        assert resp.status == 200
        data = await resp.json()
        assert data["balance"] == 100.0
        assert data["staked"] == 10.0


class TestTrustEndpoint:
    @pytest.mark.asyncio
    async def test_get_trust(self, client):
        cli = await client
        resp = await cli.get("/api/trust")
        assert resp.status == 200
        data = await resp.json()
        assert data["my_trust"] == 0.75
        assert data["quarantined"] is False


class TestRLEndpoint:
    @pytest.mark.asyncio
    async def test_get_rl_stats(self, client):
        cli = await client
        resp = await cli.get("/api/rl")
        assert resp.status == 200
        data = await resp.json()
        assert data["online_learning"] is True
        assert data["buffer_size"] == 50
