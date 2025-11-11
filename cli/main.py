#!/usr/bin/env python3
"""
MarlOS - Interactive CLI Entry Point
Main command-line interface with beautiful interactive menus
"""

import os
import sys
import subprocess
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich import box
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

# Initialize console
console = Console()

# Get MarlOS root directory
MARLOS_ROOT = Path(__file__).parent.parent.absolute()


def is_pip_installed():
    """Check if MarlOS is installed via pip (not running from source)"""
    try:
        import pkg_resources
        # If we can get package info, it's pip installed
        dist = pkg_resources.get_distribution('marlos')
        return True
    except:
        return False


def get_source_root():
    """Get the source root directory (for git clone installations)"""
    # Try to find the actual source directory
    current = Path.cwd()

    # Check if we're in a MarlOS source directory
    if (current / "agent" / "main.py").exists():
        return current

    # Check common locations
    common_locations = [
        Path.home() / "MarlOS",
        Path.home() / "Documents" / "MarlOS",
        Path("/opt/MarlOS") if os.name != 'nt' else Path("C:/MarlOS"),
    ]

    for location in common_locations:
        if location.exists() and (location / "agent" / "main.py").exists():
            return location

    return None


def print_banner():
    """Print MarlOS banner"""
    banner = """
[bold cyan]
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███╗   ███╗ █████╗ ██████╗ ██╗      ██████╗ ███████╗      ║
║   ████╗ ████║██╔══██╗██╔══██╗██║     ██╔═══██╗██╔════╝      ║
║   ██╔████╔██║███████║██████╔╝██║     ██║   ██║███████╗      ║
║   ██║╚██╔╝██║██╔══██║██╔══██╗██║     ██║   ██║╚════██║      ║
║   ██║ ╚═╝ ██║██║  ██║██║  ██║███████╗╚██████╔╝███████║      ║
║   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝      ║
║                                                               ║
║        Autonomous Distributed Computing OS                   ║
║        v1.0.2 | Team async_await                             ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
[/bold cyan]
"""
    console.print(banner)


def check_installation():
    """Check if MarlOS is properly installed"""
    # If installed via pip, always return True
    if is_pip_installed():
        return True, True

    # For source installations, check for required files
    source_root = get_source_root()
    if source_root is None:
        return False, False

    required_files = [
        source_root / "agent" / "main.py",
        source_root / "requirements.txt",
    ]

    installed = all(f.exists() for f in required_files)

    # Check if venv exists and has packages
    venv_python = source_root / "venv" / "bin" / "python"
    if os.name == 'nt':  # Windows
        venv_python = source_root / "venv" / "Scripts" / "python.exe"

    venv_configured = venv_python.exists()

    return installed, venv_configured


def run_installation_wizard():
    """Run the full installation wizard"""
    console.print("\n[bold yellow]📦 MarlOS Installation Wizard[/bold yellow]\n")

    # Check if installed via pip
    if is_pip_installed():
        console.print("[green]✓[/green] MarlOS is already installed via pip!\n")
        console.print("Package location:", MARLOS_ROOT)
        console.print("\n[bold cyan]You're ready to use MarlOS![/bold cyan]\n")
        console.print("Available commands:")
        console.print("  [cyan]marl[/cyan]              # Interactive menu")
        console.print("  [cyan]marl start[/cyan]        # Start MarlOS")
        console.print("  [cyan]marl execute 'cmd'[/cyan] # Run a command")
        console.print("  [cyan]marl status[/cyan]       # Check status")
        console.print("  [cyan]marl --help[/cyan]       # Show all commands\n")

        # Check if they want to clone source for development
        if Confirm.ask("Do you want to clone the source code for development?", default=False):
            console.print("\nTo get the full source code:")
            console.print("  [cyan]git clone https://github.com/ayush-jadaun/MarlOS.git[/cyan]")
            console.print("  [cyan]cd MarlOS[/cyan]")
            console.print("  [cyan]pip install -e .[/cyan]  # Install in editable mode\n")

        return True

    # Running from source - continue with normal installation
    source_root = get_source_root()

    if source_root is None:
        console.print("[red]Error:[/red] MarlOS source directory not found.")
        console.print("\nYou have two options:\n")
        console.print("1. [bold]For normal use[/bold] (recommended):")
        console.print("   [cyan]pip install git+https://github.com/ayush-jadaun/MarlOS.git[/cyan]\n")
        console.print("2. [bold]For development[/bold]:")
        console.print("   [cyan]git clone https://github.com/ayush-jadaun/MarlOS.git[/cyan]")
        console.print("   [cyan]cd MarlOS[/cyan]")
        console.print("   [cyan]pip install -e .[/cyan]\n")
        return False

    console.print(f"[green]✓[/green] MarlOS source found at: {source_root}\n")

    # Check virtual environment
    venv_dir = source_root / "venv"
    if not venv_dir.exists():
        if Confirm.ask("Virtual environment not found. Create it now?"):
            with console.status("[bold green]Creating virtual environment..."):
                subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
            console.print("[green]✓[/green] Virtual environment created\n")
        else:
            console.print("[yellow]Skipping virtual environment creation[/yellow]")
            return False

    # Install dependencies
    venv_pip = venv_dir / "bin" / "pip"
    if os.name == 'nt':
        venv_pip = venv_dir / "Scripts" / "pip.exe"

    if Confirm.ask("Install/update Python dependencies?"):
        requirements_file = source_root / "requirements.txt"
        if not requirements_file.exists():
            console.print(f"[red]✗[/red] requirements.txt not found at {requirements_file}")
            return False

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Installing dependencies...", total=None)
            result = subprocess.run(
                [str(venv_pip), "install", "-r", str(requirements_file), "-q"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                console.print("[green]✓[/green] Dependencies installed\n")
            else:
                console.print(f"[red]✗[/red] Installation failed:\n{result.stderr}")
                return False

    console.print("[bold green]✓ Installation complete![/bold green]\n")
    return True


def show_main_menu():
    """Display the main interactive menu"""
    while True:
        console.clear()
        print_banner()

        # Check installation status
        installed, configured = check_installation()

        if not installed:
            console.print("[red]⚠ MarlOS not properly installed[/red]\n")
            if is_pip_installed():
                console.print("MarlOS is installed but agent source not found.\n")
                console.print("To run MarlOS, you need the source code:")
                console.print("  [cyan]git clone https://github.com/ayush-jadaun/MarlOS.git[/cyan]")
                console.print("  [cyan]cd MarlOS[/cyan]")
                console.print("  [cyan]./start-node.sh[/cyan]  # or use marl start\n")
            else:
                console.print("Please install MarlOS first:")
                console.print("  [cyan]pip install git+https://github.com/ayush-jadaun/MarlOS.git[/cyan]\n")
            return

        # Create menu
        table = Table(show_header=False, box=box.ROUNDED, border_style="cyan")
        table.add_column("Option", style="bold cyan", width=8)
        table.add_column("Description", style="white")

        table.add_row("1", "🚀 Start MarlOS (choose mode)")
        table.add_row("2", "⚡ Quick Execute (run a command)")
        table.add_row("3", "📊 Check Status")
        table.add_row("4", "👥 List Peers")
        table.add_row("5", "💰 View Wallet")
        table.add_row("6", "📺 Live Monitor")
        table.add_row("7", "📝 Create Job")
        table.add_row("8", "📤 Submit Job")
        table.add_row("9", "⚙️  Configuration")
        table.add_row("10", "📖 Documentation")
        table.add_row("0", "❌ Exit")

        console.print(table)
        console.print()

        choice = Prompt.ask(
            "[bold yellow]Select an option[/bold yellow]",
            choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
            default="1"
        )

        if choice == "0":
            console.print("\n[cyan]Goodbye! 👋[/cyan]\n")
            break
        elif choice == "1":
            start_marlos_interactive()
        elif choice == "2":
            quick_execute()
        elif choice == "3":
            check_status()
        elif choice == "4":
            list_peers()
        elif choice == "5":
            view_wallet()
        elif choice == "6":
            live_monitor()
        elif choice == "7":
            create_job()
        elif choice == "8":
            submit_job()
        elif choice == "9":
            configuration_menu()
        elif choice == "10":
            show_documentation()

        if choice != "0":
            console.print("\n[dim]Press Enter to continue...[/dim]")
            input()


def start_marlos_interactive():
    """Interactive mode selection for starting MarlOS"""
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]Start MarlOS[/bold cyan]\n\n"
        "Choose how you want to run MarlOS:",
        border_style="cyan"
    ))
    console.print()

    table = Table(show_header=False, box=box.ROUNDED)
    table.add_column("Option", style="bold")
    table.add_column("Mode", style="cyan")
    table.add_column("Description")

    table.add_row("1", "Docker Compose", "Multiple nodes in containers (testing)")
    table.add_row("2", "Native/Real Device", "Single node on this device")
    table.add_row("3", "Development", "Dev mode with debug logging")
    table.add_row("4", "Background Service", "Start as system service")
    table.add_row("0", "← Back", "Return to main menu")

    console.print(table)
    console.print()

    choice = Prompt.ask("Select mode", choices=["0", "1", "2", "3", "4"], default="2")

    if choice == "0":
        return
    elif choice == "1":
        start_docker_mode()
    elif choice == "2":
        start_native_mode()
    elif choice == "3":
        start_dev_mode()
    elif choice == "4":
        start_service_mode()


def start_docker_mode():
    """Start MarlOS in Docker mode"""
    console.print("\n[bold cyan]Starting MarlOS with Docker Compose...[/bold cyan]\n")

    # Check if source available
    if is_pip_installed():
        source_root = get_source_root()
        if source_root is None:
            console.print("[yellow]Source code not found.[/yellow]\n")
            console.print("Clone the repository first:")
            console.print("  [cyan]git clone https://github.com/ayush-jadaun/MarlOS.git[/cyan]")
            console.print("  [cyan]cd MarlOS[/cyan]")
            console.print("  [cyan]docker-compose up -d[/cyan]\n")
            return
        root_dir = source_root
    else:
        root_dir = MARLOS_ROOT

    docker_compose = root_dir / "docker-compose.yml"
    if not docker_compose.exists():
        console.print("[red]Error:[/red] docker-compose.yml not found")
        return

    # Check if Docker is installed
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[red]Error:[/red] Docker not installed")
        console.print("Install Docker: https://docs.docker.com/get-docker/")
        return

    if Confirm.ask("Start 3 agent nodes + MQTT broker?", default=True):
        with console.status("[bold green]Starting Docker containers..."):
            result = subprocess.run(
                ["docker-compose", "up", "-d"],
                cwd=root_dir,
                capture_output=True,
                text=True
            )

        if result.returncode == 0:
            console.print("[green]✓[/green] MarlOS started in Docker!\n")
            console.print("Dashboard URLs:")
            console.print("  • Agent 1: [cyan]http://localhost:8081[/cyan]")
            console.print("  • Agent 2: [cyan]http://localhost:8082[/cyan]")
            console.print("  • Agent 3: [cyan]http://localhost:8083[/cyan]")
            console.print("\nTest with: [cyan]marl execute 'echo Hello MarlOS' --port 8081[/cyan]")
        else:
            console.print(f"[red]✗[/red] Failed to start:\n{result.stderr}")


def start_native_mode():
    """Start MarlOS in native mode"""
    console.print("\n[bold cyan]Configure Native Node[/bold cyan]\n")

    # If pip installed, need source code
    if is_pip_installed():
        source_root = get_source_root()
        if source_root is None:
            console.print("[yellow]MarlOS is installed via pip, but source code not found.[/yellow]\n")
            console.print("To run a native node, you need the source code:\n")
            console.print("1. Clone the repository:")
            console.print("   [cyan]git clone https://github.com/ayush-jadaun/MarlOS.git[/cyan]")
            console.print("   [cyan]cd MarlOS[/cyan]\n")
            console.print("2. Run the node:")
            console.print("   [cyan]python -m agent.main[/cyan]\n")
            console.print("Or use the CLI directly:")
            console.print("   [cyan]marl execute 'echo test' --port 3001[/cyan]\n")
            return
        root_dir = source_root
    else:
        root_dir = MARLOS_ROOT

    # Check for existing launch scripts
    launch_scripts = list(root_dir.glob("start-*.sh"))

    if launch_scripts:
        console.print(f"[green]Found {len(launch_scripts)} launch script(s):[/green]\n")
        for i, script in enumerate(launch_scripts, 1):
            console.print(f"  {i}. {script.name}")
        console.print()

        if Confirm.ask("Use existing launch script?"):
            choice = Prompt.ask(
                "Select script number",
                choices=[str(i) for i in range(1, len(launch_scripts) + 1)],
                default="1"
            )
            script_to_run = launch_scripts[int(choice) - 1]

            console.print(f"\n[cyan]Starting {script_to_run.name}...[/cyan]\n")
            try:
                subprocess.run([str(script_to_run)], cwd=MARLOS_ROOT, check=True)
            except KeyboardInterrupt:
                console.print("\n[yellow]Agent stopped[/yellow]")
            return

    # New configuration
    console.print("[yellow]No launch scripts found. Let's create one![/yellow]\n")

    node_id = Prompt.ask("Node ID", default=f"node-{os.uname().nodename if hasattr(os, 'uname') else 'windows'}")

    console.print("\nBootstrap Peers (comma-separated IPs):")
    console.print("[dim]Example: 192.168.1.100,192.168.1.101[/dim]")
    peers_input = Prompt.ask("Peers (leave empty for standalone)", default="")

    bootstrap_peers = ""
    if peers_input:
        ips = [ip.strip() for ip in peers_input.split(',')]
        bootstrap_peers = ",".join([f"tcp://{ip}:5555" for ip in ips])

    # Create launch script
    script_path = root_dir / f"start-{node_id}.sh"
    with open(script_path, 'w') as f:
        f.write(f"""#!/bin/bash
export NODE_ID="{node_id}"
export BOOTSTRAP_PEERS="{bootstrap_peers}"
export PUB_PORT=5555
export SUB_PORT=5556
export DASHBOARD_PORT=3001
export ENABLE_DOCKER=false

cd {root_dir}
source venv/bin/activate
python -m agent.main
""")

    script_path.chmod(0o755)
    console.print(f"\n[green]✓[/green] Launch script created: {script_path.name}\n")

    if Confirm.ask("Start node now?", default=True):
        try:
            subprocess.run([str(script_path)], cwd=MARLOS_ROOT, check=True)
        except KeyboardInterrupt:
            console.print("\n[yellow]Agent stopped[/yellow]")


def start_dev_mode():
    """Start in development mode"""
    console.print("\n[bold cyan]Starting Development Mode...[/bold cyan]\n")

    # Check if source available
    if is_pip_installed():
        source_root = get_source_root()
        if source_root is None:
            console.print("[yellow]Source code not found.[/yellow]\n")
            console.print("Clone the repository first:")
            console.print("  [cyan]git clone https://github.com/ayush-jadaun/MarlOS.git[/cyan]\n")
            return
        root_dir = source_root
    else:
        root_dir = MARLOS_ROOT

    env = os.environ.copy()
    env.update({
        "NODE_ID": "dev-node",
        "BOOTSTRAP_PEERS": "",
        "LOG_LEVEL": "DEBUG",
        "ENABLE_DOCKER": "false"
    })

    try:
        venv_python = root_dir / "venv" / "bin" / "python"
        if os.name == 'nt':
            venv_python = root_dir / "venv" / "Scripts" / "python.exe"

        # If venv doesn't exist, use system python
        if not venv_python.exists():
            venv_python = sys.executable

        subprocess.run(
            [str(venv_python), "-m", "agent.main"],
            cwd=root_dir,
            env=env,
            check=True
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Dev agent stopped[/yellow]")


def start_service_mode():
    """Start as system service (Linux only)"""
    if os.name != 'posix':
        console.print("[yellow]System services only supported on Linux[/yellow]")
        return

    console.print("\n[bold cyan]System Service Management[/bold cyan]\n")

    # Check for existing services
    result = subprocess.run(
        ["systemctl", "list-units", "marlos-*.service", "--all", "--no-pager"],
        capture_output=True,
        text=True
    )

    if "marlos-" in result.stdout:
        console.print("[green]Found MarlOS services:[/green]\n")
        console.print(result.stdout)
        console.print()

        action = Prompt.ask(
            "Action",
            choices=["start", "stop", "restart", "status", "logs", "back"],
            default="status"
        )

        if action == "back":
            return

        service_name = Prompt.ask("Service name", default="marlos-node")

        if action == "logs":
            subprocess.run(["journalctl", "-u", service_name, "-f"])
        else:
            subprocess.run(["sudo", "systemctl", action, service_name])
    else:
        console.print("[yellow]No MarlOS services found.[/yellow]")
        console.print("\nCreate a service using: [cyan]marl install[/cyan]")


def quick_execute():
    """Quick execute a shell command"""
    console.print("\n[bold cyan]⚡ Quick Execute[/bold cyan]\n")

    command = Prompt.ask("Enter command to execute")
    port = Prompt.ask("Dashboard port", default="3001")

    console.print(f"\n[cyan]Submitting:[/cyan] {command}\n")

    try:
        from cli.marlOS import execute as execute_cmd
        ctx = click.Context(execute_cmd)
        ctx.invoke(execute_cmd, command=command, port=int(port), payment=10.0, priority=0.5, wait=False)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


def check_status():
    """Check MarlOS status"""
    console.print("\n[bold cyan]📊 MarlOS Status[/bold cyan]\n")

    port = Prompt.ask("Dashboard port", default="3001")

    try:
        from cli.marlOS import status as status_cmd
        ctx = click.Context(status_cmd)
        ctx.invoke(status_cmd, port=int(port), json_output=False)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


def list_peers():
    """List connected peers"""
    console.print("\n[bold cyan]👥 Connected Peers[/bold cyan]\n")

    port = Prompt.ask("Dashboard port", default="3001")

    try:
        from cli.marlOS import peers as peers_cmd
        ctx = click.Context(peers_cmd)
        ctx.invoke(peers_cmd, port=int(port))
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


def view_wallet():
    """View wallet balance"""
    console.print("\n[bold cyan]💰 Wallet Status[/bold cyan]\n")

    port = Prompt.ask("Dashboard port", default="3001")

    try:
        from cli.marlOS import wallet as wallet_cmd
        ctx = click.Context(wallet_cmd)
        ctx.invoke(wallet_cmd, port=int(port))
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


def live_monitor():
    """Live monitoring dashboard"""
    console.print("\n[bold cyan]📺 Live Monitor[/bold cyan]\n")

    port = Prompt.ask("Dashboard port", default="3001")

    try:
        from cli.marlOS import watch as watch_cmd
        ctx = click.Context(watch_cmd)
        ctx.invoke(watch_cmd, port=int(port), interval=2)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


def create_job():
    """Create a job template"""
    console.print("\n[bold cyan]📝 Create Job Template[/bold cyan]\n")

    job_types = ["shell", "docker", "malware_scan", "port_scan"]
    job_type = Prompt.ask("Job type", choices=job_types, default="shell")

    if job_type == "shell":
        command = Prompt.ask("Command to execute", default="echo 'Hello MarlOS'")
        payload = {"command": command}
    elif job_type == "port_scan":
        target = Prompt.ask("Target IP")
        ports = Prompt.ask("Port range", default="1-1000")
        payload = {"target": target, "ports": ports}
    else:
        payload = {}

    payment = float(Prompt.ask("Payment (AC)", default="100"))
    priority = float(Prompt.ask("Priority (0-1)", default="0.5"))
    output_file = Prompt.ask("Output file", default="job.json")

    import json
    job = {
        "job_type": job_type,
        "priority": priority,
        "payment": payment,
        "payload": payload
    }

    with open(output_file, 'w') as f:
        json.dump(job, f, indent=2)

    console.print(f"\n[green]✓[/green] Job template created: {output_file}")
    console.print(f"\nSubmit with: [cyan]marl submit {output_file}[/cyan]")


def submit_job():
    """Submit a job from file"""
    console.print("\n[bold cyan]📤 Submit Job[/bold cyan]\n")

    job_file = Prompt.ask("Job file path", default="job.json")
    port = Prompt.ask("Dashboard port", default="3001")

    try:
        from cli.marlOS import submit as submit_cmd
        ctx = click.Context(submit_cmd)
        ctx.invoke(submit_cmd, job_file=job_file, port=int(port), method='ws', wait=False)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


def configuration_menu():
    """Configuration menu"""
    console.print("\n[bold cyan]⚙️  Configuration[/bold cyan]\n")

    # Get correct root directory
    if is_pip_installed():
        source_root = get_source_root()
        if source_root is None:
            console.print("[yellow]Configuration requires source code.[/yellow]\n")
            console.print("Clone the repository:")
            console.print("  [cyan]git clone https://github.com/ayush-jadaun/MarlOS.git[/cyan]\n")
            return
        root_dir = source_root
    else:
        root_dir = MARLOS_ROOT

    console.print("Configuration options:")
    console.print("  1. Edit launch script")
    console.print("  2. View current config")
    console.print("  3. Re-run installer")
    console.print("  0. Back")
    console.print()

    choice = Prompt.ask("Select option", choices=["0", "1", "2", "3"])

    if choice == "1":
        launch_scripts = list(root_dir.glob("start-*.sh"))
        if launch_scripts:
            console.print("\nLaunch scripts:")
            for i, script in enumerate(launch_scripts, 1):
                console.print(f"  {i}. {script.name}")

            idx = int(Prompt.ask("Select script", default="1")) - 1
            editor = os.environ.get("EDITOR", "nano")
            subprocess.run([editor, str(launch_scripts[idx])])
        else:
            console.print("[yellow]No launch scripts found[/yellow]")

    elif choice == "2":
        env_vars = ["NODE_ID", "BOOTSTRAP_PEERS", "PUB_PORT", "SUB_PORT", "DASHBOARD_PORT"]
        table = Table(title="Current Configuration", box=box.ROUNDED)
        table.add_column("Variable", style="cyan")
        table.add_column("Value", style="green")

        for var in env_vars:
            value = os.environ.get(var, "[dim]not set[/dim]")
            table.add_row(var, value)

        console.print(table)

    elif choice == "3":
        installer = root_dir / "install-marlos.sh"
        if installer.exists():
            subprocess.run([str(installer)])
        else:
            console.print("[yellow]Installer not found[/yellow]")


def show_documentation():
    """Show documentation links"""
    console.print("\n[bold cyan]📖 Documentation[/bold cyan]\n")

    # Get correct root directory
    if is_pip_installed():
        source_root = get_source_root()
        root_dir = source_root if source_root else MARLOS_ROOT
    else:
        root_dir = MARLOS_ROOT

    docs = [
        ("Quick Start", "QUICKSTART.md"),
        ("Installation Guide", "INSTALL.md"),
        ("Deployment Guide", "docs/DISTRIBUTED_DEPLOYMENT.md"),
        ("Network Design", "docs/NETWORK_DESIGN.md"),
        ("RL Architecture", "docs/ARCHITECTURE_RL.md"),
        ("Share Guide", "SHARE.md"),
    ]

    table = Table(box=box.ROUNDED)
    table.add_column("Document", style="cyan")
    table.add_column("Path", style="dim")

    for name, path in docs:
        full_path = root_dir / path
        status = "[green]✓[/green]" if full_path.exists() else "[red]✗[/red]"
        table.add_row(f"{status} {name}", path)

    console.print(table)
    console.print()
    console.print("GitHub: [cyan]https://github.com/ayush-jadaun/MarlOS[/cyan]")
    console.print("Issues: [cyan]https://github.com/ayush-jadaun/MarlOS/issues[/cyan]")


# Click CLI group
@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version="1.0.2", prog_name="MarlOS")
def cli(ctx):
    """
    🌌 MarlOS - Autonomous Distributed Computing Operating System

    Interactive CLI for managing and interacting with MarlOS nodes.
    """
    if ctx.invoked_subcommand is None:
        # No command provided - show interactive menu
        show_main_menu()


@cli.command()
def interactive():
    """Launch interactive menu"""
    show_main_menu()


@cli.command()
def install():
    """Run installation wizard"""
    print_banner()
    run_installation_wizard()


# Import all commands from marlOS.py
@cli.command()
@click.argument('command')
@click.option('--port', '-p', default=3001, help='Dashboard port')
@click.option('--payment', default=10.0, help='Payment amount in AC')
@click.option('--priority', default=0.5, help='Job priority 0-1')
@click.option('--wait', '-w', is_flag=True, help='Wait for completion')
def execute(command, port, payment, priority, wait):
    """Quick execute a shell command"""
    from cli.marlOS import execute as execute_impl, submit_via_websocket
    import asyncio
    import uuid
    import time

    console.print(f"[cyan]⚡ Executing:[/cyan] {command}\n")

    job = {
        'job_id': f"job-{str(uuid.uuid4())[:8]}",
        'job_type': 'shell',
        'priority': priority,
        'payment': payment,
        'deadline': time.time() + 300,
        'payload': {'command': command, 'timeout': 60}
    }

    asyncio.run(submit_via_websocket(job, port, wait))


@cli.command()
@click.option('--port', '-p', default=3001, help='Dashboard port')
@click.option('--json-output', '-j', is_flag=True, help='JSON output')
def status(port, json_output):
    """Check swarm status"""
    from cli.marlOS import status as status_impl
    ctx = click.Context(status_impl)
    ctx.invoke(status_impl, port=port, json_output=json_output)


@cli.command()
@click.option('--port', '-p', default=3001, help='Dashboard port')
def peers(port):
    """List connected peers"""
    from cli.marlOS import peers as peers_impl
    ctx = click.Context(peers_impl)
    ctx.invoke(peers_impl, port=port)


@cli.command()
@click.option('--port', '-p', default=3001, help='Dashboard port')
def wallet(port):
    """Show wallet balance"""
    from cli.marlOS import wallet as wallet_impl
    ctx = click.Context(wallet_impl)
    ctx.invoke(wallet_impl, port=port)


@cli.command()
@click.option('--port', '-p', default=3001, help='Dashboard port')
@click.option('--interval', '-i', default=2, help='Update interval (seconds)')
def watch(port, interval):
    """Real-time monitoring"""
    from cli.marlOS import watch as watch_impl
    ctx = click.Context(watch_impl)
    ctx.invoke(watch_impl, port=port, interval=interval)


@cli.command()
@click.argument('job_file', type=click.Path(exists=True))
@click.option('--port', '-p', default=3001, help='Dashboard port')
@click.option('--wait', '-w', is_flag=True, help='Wait for completion')
def submit(job_file, port, wait):
    """Submit a job from file"""
    from cli.marlOS import submit as submit_impl
    ctx = click.Context(submit_impl)
    ctx.invoke(submit_impl, job_file=job_file, port=port, method='ws', wait=wait)


@cli.command()
@click.option('--name', '-n', required=True, help='Job type name')
@click.option('--command', '-c', help='Command (for shell jobs)')
@click.option('--payment', '-p', default=100.0, help='Payment in AC')
@click.option('--priority', default=0.5, help='Priority (0-1)')
@click.option('--output', '-o', default='job.json', help='Output file')
def create(name, command, payment, priority, output):
    """Create job template"""
    from cli.marlOS import create as create_impl
    ctx = click.Context(create_impl)
    ctx.invoke(create_impl, name=name, command=command, payment=payment, priority=priority, output=output)


@cli.command()
def start():
    """Start MarlOS (interactive mode selection)"""
    print_banner()
    start_marlos_interactive()


@cli.command()
def version():
    """Show version information"""
    console.print("\n[bold cyan]🌌 MarlOS v1.0.2[/bold cyan]")
    console.print("[cyan]Autonomous Distributed Computing Operating System[/cyan]")
    console.print("\n[dim]Built by Team async_await[/dim]\n")


if __name__ == '__main__':
    cli()
