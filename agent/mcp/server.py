"""
MarlOS MCP Server
Exposes MarlOS capabilities as MCP tools so AI agents (Claude, etc.)
can submit jobs, check status, and interact with the compute network.

Usage:
    # Standalone (connects to running MarlOS node via REST API)
    python -m agent.mcp.server

    # In Claude Desktop / claude_desktop_config.json:
    {
      "mcpServers": {
        "marlos": {
          "command": "python",
          "args": ["-m", "agent.mcp.server"],
          "env": {
            "MARLOS_API_URL": "http://localhost:3101"
          }
        }
      }
    }
"""

import os
import json
import asyncio
import logging
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
)

logger = logging.getLogger(__name__)

# Default API URL (REST API port = dashboard port + 100)
DEFAULT_API_URL = os.environ.get("MARLOS_API_URL", "http://localhost:3101")


def create_mcp_server(api_url: str = None) -> Server:
    """Create and configure the MarlOS MCP server."""
    server = Server("marlos")
    base_url = api_url or DEFAULT_API_URL

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="submit_job",
                description=(
                    "Submit a compute job to the MarlOS distributed network. "
                    "The job will be auctioned to the best-suited node and executed. "
                    "Supported job types: shell, docker, port_scan, malware_scan, "
                    "hash_crack, threat_intel."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "job_type": {
                            "type": "string",
                            "description": "Type of job: shell, docker, port_scan, malware_scan, hash_crack, threat_intel",
                            "enum": ["shell", "docker", "port_scan", "malware_scan", "hash_crack", "threat_intel"],
                        },
                        "payload": {
                            "type": "object",
                            "description": "Job-specific payload. For shell: {command: '...'}. For port_scan: {target: '...'}. For docker: {image: '...', command: '...'}.",
                        },
                        "payment": {
                            "type": "number",
                            "description": "Payment in AC tokens (default: 100.0)",
                            "default": 100.0,
                        },
                        "priority": {
                            "type": "number",
                            "description": "Priority 0.0-1.0 (default: 0.5)",
                            "default": 0.5,
                        },
                    },
                    "required": ["job_type", "payload"],
                },
            ),
            Tool(
                name="get_job_status",
                description="Check the status and result of a previously submitted job.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "The job ID returned from submit_job",
                        },
                    },
                    "required": ["job_id"],
                },
            ),
            Tool(
                name="list_jobs",
                description="List all jobs known to this MarlOS node (completed, executing, auctioning).",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="get_network_status",
                description=(
                    "Get the current status of the MarlOS network: connected peers, "
                    "node capabilities, wallet balance, trust score, and RL stats."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="get_peers",
                description="List all connected peers in the MarlOS network with their capabilities and trust scores.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="get_wallet",
                description="Get wallet balance and token economy information.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
            try:
                if name == "submit_job":
                    return await _submit_job(client, arguments)
                elif name == "get_job_status":
                    return await _get_job_status(client, arguments)
                elif name == "list_jobs":
                    return await _list_jobs(client)
                elif name == "get_network_status":
                    return await _get_network_status(client)
                elif name == "get_peers":
                    return await _get_peers(client)
                elif name == "get_wallet":
                    return await _get_wallet(client)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except httpx.ConnectError:
                return [TextContent(
                    type="text",
                    text=(
                        f"Cannot connect to MarlOS node at {base_url}. "
                        "Make sure a MarlOS agent is running:\n"
                        "  NODE_ID=my-node python -m agent.main\n\n"
                        "Or set MARLOS_API_URL to point to the correct address."
                    ),
                )]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {e}")]

    return server


async def _submit_job(client: httpx.AsyncClient, args: dict) -> list[TextContent]:
    resp = await client.post("/api/jobs", json={
        "job_type": args["job_type"],
        "payload": args["payload"],
        "payment": args.get("payment", 100.0),
        "priority": args.get("priority", 0.5),
    })
    data = resp.json()

    if resp.status_code == 201:
        return [TextContent(
            type="text",
            text=(
                f"Job submitted successfully!\n"
                f"  Job ID: {data['job_id']}\n"
                f"  Status: {data['status']}\n"
                f"  Type: {args['job_type']}\n"
                f"  Payment: {args.get('payment', 100.0)} AC\n\n"
                f"The job is now being auctioned across the network. "
                f"Use get_job_status with job_id '{data['job_id']}' to check results."
            ),
        )]
    else:
        return [TextContent(type="text", text=f"Error submitting job: {data}")]


async def _get_job_status(client: httpx.AsyncClient, args: dict) -> list[TextContent]:
    job_id = args["job_id"]
    resp = await client.get(f"/api/jobs/{job_id}")
    data = resp.json()

    if resp.status_code == 404:
        return [TextContent(type="text", text=f"Job '{job_id}' not found on this node.")]

    lines = [f"Job: {job_id}", f"Status: {data.get('status', 'unknown')}"]
    if data.get("result"):
        lines.append(f"Result: {json.dumps(data['result'], indent=2)}")
    if data.get("duration"):
        lines.append(f"Duration: {data['duration']:.2f}s")
    if data.get("error"):
        lines.append(f"Error: {data['error']}")

    return [TextContent(type="text", text="\n".join(lines))]


async def _list_jobs(client: httpx.AsyncClient) -> list[TextContent]:
    resp = await client.get("/api/jobs")
    data = resp.json()
    jobs = data.get("jobs", [])

    if not jobs:
        return [TextContent(type="text", text="No jobs found on this node.")]

    lines = [f"Total jobs: {len(jobs)}", ""]
    for job in jobs:
        lines.append(f"  {job['job_id']}: {job['status']}")

    return [TextContent(type="text", text="\n".join(lines))]


async def _get_network_status(client: httpx.AsyncClient) -> list[TextContent]:
    resp = await client.get("/api/status")
    state = resp.json()

    wallet = state.get("wallet", {})
    lines = [
        "MarlOS Network Status",
        "=" * 30,
        f"Node ID: {state.get('node_id', 'N/A')}",
        f"Node Name: {state.get('node_name', 'N/A')}",
        f"Peers: {state.get('peers', 0)}",
        f"Trust Score: {state.get('trust_score', 0):.3f}",
        f"Quarantined: {'Yes' if state.get('quarantined') else 'No'}",
        f"Balance: {wallet.get('balance', 0):.2f} AC",
        f"Jobs Completed: {state.get('jobs_completed', 0)}",
        f"Jobs Failed: {state.get('jobs_failed', 0)}",
        f"Capabilities: {', '.join(state.get('capabilities', []))}",
    ]

    return [TextContent(type="text", text="\n".join(lines))]


async def _get_peers(client: httpx.AsyncClient) -> list[TextContent]:
    resp = await client.get("/api/peers")
    data = resp.json()
    peers = data.get("peers", [])

    if not peers:
        return [TextContent(type="text", text="No peers connected.")]

    lines = [f"Connected peers: {len(peers)}", ""]
    for peer in peers:
        caps = ", ".join(peer.get("capabilities", []))
        lines.append(
            f"  {peer['node_id']}: trust={peer.get('trust', 0):.3f}, caps=[{caps}]"
        )

    return [TextContent(type="text", text="\n".join(lines))]


async def _get_wallet(client: httpx.AsyncClient) -> list[TextContent]:
    resp = await client.get("/api/wallet")
    data = resp.json()

    lines = [
        "MarlOS Wallet",
        "=" * 25,
        f"Balance: {data.get('balance', 0):.2f} AC",
        f"Staked: {data.get('staked', 0):.2f} AC",
        f"Total Value: {data.get('total_value', 0):.2f} AC",
        f"Lifetime Earned: {data.get('lifetime_earned', 0):.2f} AC",
        f"Lifetime Spent: {data.get('lifetime_spent', 0):.2f} AC",
    ]

    return [TextContent(type="text", text="\n".join(lines))]


async def main():
    """Run MCP server via stdio transport."""
    server = create_mcp_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
