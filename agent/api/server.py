"""
MarlOS REST API Server
Provides HTTP endpoints for job submission, status queries, and network info.
Runs alongside the WebSocket dashboard server.
"""

import asyncio
import json
import uuid
import time
import logging
from aiohttp import web

logger = logging.getLogger(__name__)


class RESTAPIServer:
    """
    Lightweight REST API for MarlOS agent.
    Runs on a configurable port (default: dashboard_port + 100, e.g., 3101).
    """

    def __init__(self, agent, host: str = "0.0.0.0", port: int = None):
        self.agent = agent
        self.host = host
        self.port = port or (agent.config.dashboard.port + 100)
        self.app = web.Application()
        self.runner = None
        self._setup_routes()

    def _setup_routes(self):
        self.app.router.add_get("/api/status", self.get_status)
        self.app.router.add_get("/api/health", self.get_health)
        self.app.router.add_post("/api/jobs", self.submit_job)
        self.app.router.add_get("/api/jobs/{job_id}", self.get_job)
        self.app.router.add_get("/api/jobs", self.list_jobs)
        self.app.router.add_get("/api/peers", self.get_peers)
        self.app.router.add_get("/api/wallet", self.get_wallet)
        self.app.router.add_get("/api/trust", self.get_trust)
        self.app.router.add_get("/api/rl", self.get_rl_stats)
        # Pipeline endpoints
        self.app.router.add_post("/api/pipelines", self.submit_pipeline)
        self.app.router.add_get("/api/pipelines", self.list_pipelines)
        self.app.router.add_get("/api/pipelines/{pipeline_id}", self.get_pipeline)

        # CORS middleware
        self.app.middlewares.append(self._cors_middleware)

    @web.middleware
    async def _cors_middleware(self, request, handler):
        if request.method == "OPTIONS":
            response = web.Response()
        else:
            response = await handler(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    async def start(self):
        """Start the REST API server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()
        print(f"[API] REST API started on http://{self.host}:{self.port}")

    async def stop(self):
        """Stop the REST API server."""
        if self.runner:
            await self.runner.cleanup()

    # ── Endpoints ────────────────────────────────────────────────

    async def get_health(self, request):
        """GET /api/health — Simple health check."""
        return web.json_response({"status": "ok", "node_id": self.agent.node_id})

    async def get_status(self, request):
        """GET /api/status — Full node state."""
        state = self.agent.get_state()
        return web.json_response(state)

    async def submit_job(self, request):
        """POST /api/jobs — Submit a job to the network."""
        try:
            body = await request.json()
        except json.JSONDecodeError:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        job_type = body.get("job_type")
        if not job_type:
            return web.json_response({"error": "job_type is required"}, status=400)

        payload = body.get("payload", {})
        if not payload:
            return web.json_response({"error": "payload is required"}, status=400)

        job_id = body.get("job_id", f"job-{str(uuid.uuid4())[:8]}")
        payment = body.get("payment", 100.0)
        priority = body.get("priority", 0.5)
        deadline = body.get("deadline", time.time() + 300)

        try:
            from ..p2p.protocol import MessageType

            await self.agent.p2p.broadcast_message(
                MessageType.JOB_BROADCAST,
                job_id=job_id,
                job_type=job_type,
                priority=priority,
                payment=payment,
                deadline=deadline,
                payload=payload,
                requirements=body.get("requirements"),
                verify=body.get("verify", False),
                verifiers=body.get("verifiers", 1),
            )

            return web.json_response({
                "job_id": job_id,
                "status": "submitted",
                "message": "Job broadcast to network for auction",
            }, status=201)

        except Exception as e:
            logger.error(f"Error submitting job: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_job(self, request):
        """GET /api/jobs/{job_id} — Get job result."""
        job_id = request.match_info["job_id"]
        result = self.agent.job_results.get(job_id)

        if result:
            return web.json_response({
                "job_id": job_id,
                "status": result.status.value if hasattr(result.status, 'value') else str(result.status),
                "result": result.result if hasattr(result, 'result') else None,
                "duration": result.duration if hasattr(result, 'duration') else None,
                "error": result.error if hasattr(result, 'error') else None,
            })

        # Check active jobs
        if job_id in self.agent.active_job_metadata:
            return web.json_response({
                "job_id": job_id,
                "status": "executing",
            })

        # Check active auctions
        if job_id in self.agent.auction.active_auctions:
            return web.json_response({
                "job_id": job_id,
                "status": "auctioning",
            })

        return web.json_response({"error": "Job not found"}, status=404)

    async def list_jobs(self, request):
        """GET /api/jobs — List all known jobs."""
        jobs = []

        # Completed jobs
        for job_id, result in self.agent.job_results.items():
            jobs.append({
                "job_id": job_id,
                "status": result.status.value if hasattr(result.status, 'value') else str(result.status),
            })

        # Active jobs
        for job_id in self.agent.active_job_metadata:
            if job_id not in self.agent.job_results:
                jobs.append({"job_id": job_id, "status": "executing"})

        return web.json_response({"jobs": jobs, "total": len(jobs)})

    async def get_peers(self, request):
        """GET /api/peers — List connected peers."""
        peers = []
        for peer_id, info in self.agent.p2p.peers.items():
            peers.append({
                "node_id": peer_id,
                "capabilities": info.get("capabilities", []),
                "ip": info.get("ip", ""),
                "trust": self.agent.reputation.get_peer_trust(peer_id),
            })

        return web.json_response({
            "peers": peers,
            "count": len(peers),
        })

    async def get_wallet(self, request):
        """GET /api/wallet — Get wallet info."""
        wallet = self.agent.wallet
        return web.json_response({
            "balance": wallet.balance,
            "staked": wallet.staked,
            "total_value": wallet.balance + wallet.staked,
            "lifetime_earned": wallet.lifetime_earned,
            "lifetime_spent": wallet.lifetime_spent,
        })

    async def get_trust(self, request):
        """GET /api/trust — Get trust info."""
        return web.json_response({
            "my_trust": self.agent.reputation.get_my_trust_score(),
            "quarantined": self.agent.reputation.am_i_quarantined(),
            "peer_scores": {
                pid: self.agent.reputation.get_peer_trust(pid)
                for pid in self.agent.p2p.peers
            },
        })

    async def get_rl_stats(self, request):
        """GET /api/rl — Get RL and online learning stats."""
        learning_stats = self.agent.online_learner.get_learning_stats()
        return web.json_response({
            "online_learning": learning_stats["learning_enabled"],
            "buffer_size": learning_stats["buffer_size"],
            "updates_performed": learning_stats["updates_performed"],
            "exploration_rate": self.agent.rl_policy.exploration_rate
            if hasattr(self.agent.rl_policy, "exploration_rate") else None,
        })

    # ── Pipeline endpoints ───────────────────────────────────────

    async def submit_pipeline(self, request):
        """POST /api/pipelines — Submit a job pipeline (DAG)."""
        try:
            body = await request.json()
        except json.JSONDecodeError:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        from ..pipeline.dag import Pipeline

        try:
            pipeline = Pipeline.from_dict(body)
        except (KeyError, TypeError) as e:
            return web.json_response({"error": f"Invalid pipeline format: {e}"}, status=400)

        errors = pipeline.validate()
        if errors:
            return web.json_response({"error": errors}, status=400)

        result = await self.agent.pipeline_engine.submit_pipeline(pipeline)
        return web.json_response(result.to_dict(), status=201)

    async def list_pipelines(self, request):
        """GET /api/pipelines — List all pipelines."""
        pipelines = self.agent.pipeline_engine.list_pipelines()
        return web.json_response({"pipelines": pipelines, "total": len(pipelines)})

    async def get_pipeline(self, request):
        """GET /api/pipelines/{pipeline_id} — Get pipeline status."""
        pipeline_id = request.match_info["pipeline_id"]
        pipeline = self.agent.pipeline_engine.get_pipeline(pipeline_id)
        if not pipeline:
            return web.json_response({"error": "Pipeline not found"}, status=404)
        return web.json_response(pipeline.to_dict())
