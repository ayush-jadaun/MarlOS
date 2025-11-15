#!/usr/bin/env python3
"""
MarlOS CLI Tool
Command-line interface for interacting with the distributed computing swarm
"""
import os
import sys

# Fix Windows emoji encoding issues
if sys.platform == 'win32':
    # Force UTF-8 encoding for stdout/stderr
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

import click
import asyncio
import json
import time
import zmq
import zmq.asyncio
import websockets
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich import box

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.main import MarlOSAgent
from agent.config import AgentConfig
from agent.crypto.signing import SigningKey, sign_message
from agent.p2p.protocol import MessageType, create_message

# Configure console
console = Console()


@click.group()
@click.version_option(version="1.0.5", prog_name="MarlOS")
def cli():
    """
    🌌 MarlOS - Autonomous Distributed Computing Swarm

    A self-organizing, self-improving distributed operating system
    powered by reinforcement learning and peer-to-peer networking.
    """
    pass


@cli.command()
@click.option('--nodes', '-n', default=1, help='Number of nodes to start')
@click.option('--port', '-p', default=5555, help='Base port number')
@click.option('--config', '-c', type=click.Path(exists=True), help='Config file path')
def start(nodes, port, config):
    """Start MarlOS agent nodes"""
    console.print(f"[bold cyan]🚀 Starting {nodes} MarlOS node(s)...[/bold cyan]\n")

    async def run_nodes():
        agents = []

        for i in range(nodes):
            if config:
                agent_config = AgentConfig()  # Load from config file
            else:
                agent_config = AgentConfig()
                agent_config.network.pub_port = port + (i * 10)
                agent_config.network.sub_port = port + (i * 10) + 1
                agent_config.dashboard.port = 3001 + i
                agent_config.node_id = f"node-{i+1}"

            agent = MarlOSAgent(agent_config)
            agents.append(agent)

            await agent.start()

            # Small delay between nodes
            if i < nodes - 1:
                await asyncio.sleep(2)

        console.print(f"\n[green]✅ All {nodes} nodes are online![/green]")
        console.print(f"[yellow]💡 Press Ctrl+C to stop all nodes[/yellow]\n")

        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]🛑 Shutting down nodes...[/yellow]")
            for agent in agents:
                await agent.stop()
            console.print("[green]✅ All nodes stopped[/green]")

    try:
        asyncio.run(run_nodes())
    except KeyboardInterrupt:
        console.print("\n[green]✅ Stopped cleanly[/green]")


@cli.command()
@click.argument('job_file', type=click.Path(exists=True))
@click.option('--port', '-p', default=8081, help='WebSocket dashboard port (default: 8081 for agent-1)')
@click.option('--method', '-m', default='ws', type=click.Choice(['zmq', 'ws']), help='Submission method (ws recommended)')
@click.option('--wait', '-w', is_flag=True, help='Wait for job completion')
def submit(job_file, port, method, wait):
    """Submit a job to the swarm"""
    console.print(f"[cyan]📤 Submitting job from {job_file}...[/cyan]")

    # Load job
    with open(job_file, 'r') as f:
        job = json.load(f)

    # Validate job
    required_fields = ['job_type', 'payload']
    for field in required_fields:
        if field not in job:
            console.print(f"[red]❌ Missing required field: {field}[/red]")
            return

    # Add job metadata
    import uuid
    job['job_id'] = job.get('job_id', f"job-{str(uuid.uuid4())[:8]}")
    job['priority'] = job.get('priority', 0.5)
    job['payment'] = job.get('payment', 100.0)
    job['deadline'] = job.get('deadline', time.time() + 300)  # 5 min default

    if method == 'zmq':
        submit_via_zmq(job, port)
    else:
        asyncio.run(submit_via_websocket(job, port, wait))


def submit_via_zmq(job, port):
    """Submit job via ZMQ (direct to P2P network)"""
    try:
        # Sign job
        key_file = "data/keys/cli_user.key"
        signing_key = SigningKey.load_or_generate(key_file)

        # Create message
        message = create_message(
            MessageType.JOB_BROADCAST,
            node_id="cli-user",
            timestamp=time.time(),
            **job
        )

        signed_message = sign_message(signing_key, message.to_dict())

        # Broadcast to swarm using a temporary PUB socket
        context = zmq.Context()
        publisher = context.socket(zmq.PUB)

        # Bind on a temporary port and broadcast
        temp_port = 5599
        publisher.bind(f"tcp://*:{temp_port}")

        console.print(f"[red]⚠️  WARNING: ZMQ submission is deprecated and may not work![/red]")
        console.print(f"[yellow]💡 Agents are not subscribed to port {temp_port}[/yellow]")
        console.print(f"[green]✅ Use --method ws (WebSocket) for reliable job submission[/green]")

        # Allow time for connection
        time.sleep(1)

        publisher.send_json(signed_message)

        console.print(f"[green]✅ Job broadcast: {job['job_id']}[/green]")
        console.print(f"   Type: {job['job_type']}")
        console.print(f"   Payment: {job['payment']} AC")
        console.print(f"   Priority: {job['priority']}")

        time.sleep(1)  # Give time for message to send
        publisher.close()
        context.term()

    except Exception as e:
        console.print(f"[red]❌ Error submitting job: {e}[/red]")


async def submit_via_websocket(job, dashboard_port, wait):
    """Submit job via WebSocket dashboard API"""
    try:
        uri = f"ws://localhost:{dashboard_port}"

        async with websockets.connect(uri, open_timeout=5) as websocket:
            # Create a job broadcast request
            request = {
                'type': 'submit_job',
                'job': job
            }

            await websocket.send(json.dumps(request))

            console.print(f"[green]✅ Job submitted via WebSocket: {job['job_id']}[/green]")
            console.print(f"   Type: {job['job_type']}")
            console.print(f"   Payment: {job['payment']} AC")
            console.print(f"   Priority: {job['priority']}")
            console.print(f"   Dashboard: ws://localhost:{dashboard_port}")

            if wait:
                console.print("\n[yellow]⏳ Waiting for response...[/yellow]")
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    console.print(f"[cyan]Response: {response}[/cyan]")
                except asyncio.TimeoutError:
                    pass

    except websockets.exceptions.WebSocketException as e:
        console.print(f"[red]❌ WebSocket error: {e}[/red]")
        console.print(f"[yellow]💡 Make sure agent is running on port {dashboard_port}[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error submitting job: {e}[/red]")


@cli.command()
@click.option('--port', '-p', default=8081, help='Dashboard WebSocket port (default: 8081 for agent-1)')
@click.option('--json-output', '-j', is_flag=True, help='Output as JSON')
def status(port, json_output):
    """Check swarm status"""

    async def get_status():
        try:
            uri = f"ws://localhost:{port}"
            async with websockets.connect(uri, open_timeout=5) as websocket:
                # Request state
                await websocket.send(json.dumps({'type': 'get_state'}))

                # Receive state
                response = await websocket.recv()
                state = json.loads(response)

                if 'data' in state:
                    state = state['data']

                if json_output:
                    console.print_json(data=state)
                else:
                    # Display formatted status
                    console.print("\n[bold cyan]📊 MarlOS Swarm Status[/bold cyan]\n")

                    # Node info
                    table = Table(title="Node Information", box=box.ROUNDED)
                    table.add_column("Property", style="cyan")
                    table.add_column("Value", style="green")

                    table.add_row("Node ID", state.get('node_id', 'N/A'))
                    table.add_row("Node Name", state.get('node_name', 'N/A'))
                    table.add_row("Trust Score", f"{state.get('trust_score', 0):.3f}")
                    table.add_row("Quarantined", "Yes" if state.get('quarantined', False) else "No")

                    console.print(table)
                    console.print()

                    # Wallet info
                    wallet = state.get('wallet', {})
                    table = Table(title=" Wallet", box=box.ROUNDED)
                    table.add_column("Property", style="cyan")
                    table.add_column("Value", style="green")

                    table.add_row("Balance", f"{wallet.get('balance', 0):.2f} AC")
                    table.add_row("Staked", f"{wallet.get('staked', 0):.2f} AC")
                    table.add_row("Total Value", f"{wallet.get('total_value', 0):.2f} AC")
                    table.add_row("Lifetime Earned", f"{wallet.get('lifetime_earned', 0):.2f} AC")
                    table.add_row("Net Profit", f"{wallet.get('net_profit', 0):.2f} AC")

                    console.print(table)
                    console.print()

                    # Network info
                    table = Table(title="🌐 Network", box=box.ROUNDED)
                    table.add_column("Property", style="cyan")
                    table.add_column("Value", style="green")

                    table.add_row("Connected Peers", str(state.get('peers', 0)))
                    table.add_row("Active Jobs", str(state.get('active_jobs', 0)))
                    table.add_row("Jobs Completed", str(state.get('jobs_completed', 0)))
                    table.add_row("Jobs Failed", str(state.get('jobs_failed', 0)))

                    console.print(table)
                    console.print()

                    # Capabilities
                    capabilities = state.get('capabilities', [])
                    console.print(f"[cyan]🛠️  Capabilities:[/cyan] {', '.join(capabilities)}")
                    console.print()

        except websockets.exceptions.WebSocketException:
            console.print("[red]❌ Could not connect to node. Is it running?[/red]")
            console.print(f"[yellow]💡 Try: Marl start[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")

    asyncio.run(get_status())


@cli.command()
@click.option('--port', '-p', default=8081, help='Dashboard WebSocket port (default: 8081 for agent-1)')
def peers(port):
    """List connected peers"""

    async def list_peers():
        try:
            uri = f"ws://localhost:{port}"
            async with websockets.connect(uri, open_timeout=5) as websocket:
                await websocket.send(json.dumps({'type': 'get_state'}))
                response = await websocket.recv()
                state = json.loads(response)

                if 'data' in state:
                    state = state['data']

                rep_stats = state.get('reputation_stats', {})

                console.print("\n[bold cyan]👥 Connected Peers[/bold cyan]\n")
                console.print(f"Total Peers: {state.get('peers', 0)}")
                console.print(f"Trusted Peers: {rep_stats.get('trusted_peers', 0)}")
                console.print(f"Quarantined Peers: {rep_stats.get('quarantined_peers', 0)}")
                console.print()

        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")

    asyncio.run(list_peers())


@cli.command()
@click.option('--port', '-p', default=8081, help='Dashboard WebSocket port (default: 8081 for agent-1)')
@click.option('--interval', '-i', default=2, help='Update interval (seconds)')
def watch(port, interval):
    """Real-time monitoring dashboard"""

    async def monitor():
        try:
            uri = f"ws://localhost:{port}"

            with Live(console=console, refresh_per_second=1) as live:
                async with websockets.connect(
                    uri,
                    ping_interval=20,  # Send ping every 20 seconds
                    ping_timeout=30    # Wait up to 30 seconds for pong
                ) as websocket:
                    while True:
                        await websocket.send(json.dumps({'type': 'get_state'}))
                        response = await websocket.recv()
                        state = json.loads(response)

                        if 'data' in state:
                            state = state['data']

                        # Create dashboard layout
                        layout = Layout()
                        layout.split_column(
                            Layout(name="header", size=3),
                            Layout(name="body"),
                            Layout(name="footer", size=3)
                        )

                        wallet = state.get('wallet', {})

                        # Header
                        layout["header"].update(
                            Panel(
                                f"[bold cyan]🌌 MarlOS - {state.get('node_name', 'N/A')}[/bold cyan]",
                                style="cyan"
                            )
                        )

                        # Body
                        body_text = f"""
[cyan]Trust Score:[/cyan] {state.get('trust_score', 0):.3f}
[cyan]Balance:[/cyan] {wallet.get('balance', 0):.2f} AC | [cyan]Staked:[/cyan] {wallet.get('staked', 0):.2f} AC
[cyan]Peers:[/cyan] {state.get('peers', 0)} | [cyan]Active Jobs:[/cyan] {state.get('active_jobs', 0)}
[cyan]Completed:[/cyan] {state.get('jobs_completed', 0)} | [cyan]Failed:[/cyan] {state.get('jobs_failed', 0)}
                        """
                        layout["body"].update(Panel(body_text.strip(), title="Status", border_style="green"))

                        # Footer
                        layout["footer"].update(
                            Panel(
                                "[yellow]Press Ctrl+C to exit[/yellow]",
                                style="yellow"
                            )
                        )

                        live.update(layout)
                        await asyncio.sleep(interval)

        except KeyboardInterrupt:
            console.print("\n[green]✅ Monitoring stopped[/green]")
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")

    try:
        asyncio.run(monitor())
    except KeyboardInterrupt:
        pass


@cli.command()
@click.option('--port', '-p', default=8081, help='Dashboard WebSocket port (default: 8081 for agent-1)')
def wallet(port):
    """Show wallet balance and transaction history"""

    async def show_wallet():
        try:
            uri = f"ws://localhost:{port}"
            async with websockets.connect(uri, open_timeout=5) as websocket:
                await websocket.send(json.dumps({'type': 'get_state'}))
                response = await websocket.recv()
                state = json.loads(response)

                if 'data' in state:
                    state = state['data']

                wallet = state.get('wallet', {})

                console.print("\n[bold cyan] Wallet Information[/bold cyan]\n")

                table = Table(box=box.ROUNDED)
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="green")

                table.add_row("Balance", f"{wallet.get('balance', 0):.2f} AC")
                table.add_row("Staked", f"{wallet.get('staked', 0):.2f} AC")
                table.add_row("Total Value", f"{wallet.get('total_value', 0):.2f} AC")
                table.add_row("Lifetime Earned", f"{wallet.get('lifetime_earned', 0):.2f} AC")
                table.add_row("Lifetime Spent", f"{wallet.get('lifetime_spent', 0):.2f} AC")
                table.add_row("Net Profit", f"{wallet.get('net_profit', 0):.2f} AC")

                console.print(table)
                console.print()

        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")

    asyncio.run(show_wallet())


@cli.command()
def jobs():
    """List job history"""
    console.print("[yellow]💡 Job history tracking coming soon![/yellow]")
    console.print("[cyan]Use 'Marl watch' for real-time job monitoring[/cyan]")


@cli.command()
@click.argument('command')
@click.option('--port', '-p', default=8081, help='Dashboard WebSocket port (default: 8081 for agent-1)')
@click.option('--payment', default=10.0, help='Payment amount in AC (default: 10)')
@click.option('--priority', default=0.5, help='Job priority 0-1 (default: 0.5)')
@click.option('--wait', '-w', is_flag=True, help='Wait for job completion')
def execute(command, port, payment, priority, wait):
    """
    Quick execute a shell command on the swarm

    Example: Marl execute "echo Hello World"
    """
    console.print(f"[cyan]⚡ Executing: {command}[/cyan]\n")

    # Create shell job
    import uuid
    job = {
        'job_id': f"job-{str(uuid.uuid4())[:8]}",
        'job_type': 'shell',
        'priority': priority,
        'payment': payment,
        'deadline': time.time() + 300,  # 5 min
        'payload': {
            'command': command,
            'timeout': 60
        }
    }

    # Submit via WebSocket
    asyncio.run(submit_via_websocket(job, port, wait))


@cli.command()
@click.option('--name', '-n', required=True, help='Job type name')
@click.option('--command', '-c', help='Command to execute (for shell jobs)')
@click.option('--payment', '-p', default=100.0, help='Payment amount in AC')
@click.option('--priority', default=0.5, help='Job priority (0-1)')
@click.option('--output', '-o', default='job.json', help='Output file path')
def create(name, command, payment, priority, output):
    """Create a job template file"""

    job_templates = {
        'shell': {
            'job_type': 'shell',
            'priority': priority,
            'payment': payment,
            'payload': {
                'command': command or 'echo "Hello MarlOS"'
            }
        },
        'docker': {
            'job_type': 'docker',
            'priority': priority,
            'payment': payment,
            'payload': {
                'image': 'alpine:latest',
                'command': ['echo', 'Hello from Docker']
            }
        },
        'malware_scan': {
            'job_type': 'malware_scan',
            'priority': priority,
            'payment': payment,
            'payload': {
                'file_url': 'https://example.com/file.exe',
                'file_hash': 'sha256_hash_here'
            }
        },
        'port_scan': {
            'job_type': 'port_scan',
            'priority': priority,
            'payment': payment,
            'payload': {
                'target': '192.168.1.1',
                'ports': '1-1000'
            }
        }
    }

    if name in job_templates:
        job = job_templates[name]
    else:
        job = {
            'job_type': name,
            'priority': priority,
            'payment': payment,
            'payload': {}
        }

    with open(output, 'w') as f:
        json.dump(job, f, indent=2)

    console.print(f"[green]✅ Job template created: {output}[/green]")
    console.print(f"[cyan]Edit the file and submit with: Marl submit {output}[/cyan]")


@cli.command()
def version():
    """Show version information"""
    console.print("\n[bold cyan]🌌 MarlOS v1.0.5[/bold cyan]")
    console.print("[cyan]A self-organizing distributed computing swarm[/cyan]\n")


if __name__ == '__main__':
    cli()
