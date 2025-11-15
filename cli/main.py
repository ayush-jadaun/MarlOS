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

# Import node config management
from agent import node_config

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
    """
    Get the MarlOS installation root directory.

    This works for both:
    - Development mode (git clone + pip install -e .)
    - Normal pip install (everything in site-packages)

    Returns the directory containing the agent, cli, and other packages.
    """
    # Method 1: Check if running from development directory (git clone)
    current = Path.cwd()
    if (current / "agent" / "main.py").exists():
        return current

    # Method 2: Check common development locations
    common_dev_locations = [
        Path.home() / "MarlOS",
        Path.home() / "Documents" / "MarlOS",
        Path("/opt/MarlOS") if os.name != 'nt' else Path("C:/MarlOS"),
    ]

    for location in common_dev_locations:
        if location.exists() and (location / "agent" / "main.py").exists():
            return location

    # Method 3: Use installed package location (pip install marlos)
    # When pip installed, agent, cli, etc. are in site-packages/
    try:
        import pkg_resources
        # Get the location of the 'agent' package
        agent_path = Path(pkg_resources.resource_filename('agent', ''))
        # The parent directory contains all packages (agent, cli, etc.)
        # For pip installations, this is site-packages/
        # We return the parent of agent which contains everything
        install_root = agent_path.parent

        # Verify agent.main exists
        if (agent_path / "main.py").exists():
            return install_root
    except:
        pass

    # Method 4: Try using __file__ relative path from cli package
    try:
        cli_path = Path(__file__).parent  # This is site-packages/cli/
        install_root = cli_path.parent     # This is site-packages/

        # Verify agent exists at sibling location
        if (install_root / "agent" / "main.py").exists():
            return install_root
    except:
        pass

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
║        v1.0.5 | Team async_await                             ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
[/bold cyan]
"""
    console.print(banner)


def check_installation():
    """Check if MarlOS is properly installed"""
    # Check if pip installed
    pip_installed = is_pip_installed()

    # Check if source code is available
    source_root = get_source_root()
    has_source = source_root is not None and (source_root / "agent" / "main.py").exists()

    # For source installations, check venv
    venv_configured = False
    if has_source:
        venv_python = source_root / "venv" / "bin" / "python"
        if os.name == 'nt':  # Windows
            venv_python = source_root / "venv" / "Scripts" / "python.exe"
        venv_configured = venv_python.exists()

    return pip_installed or has_source, has_source


def verify_installation():
    """
    Verify that MarlOS is properly installed with all required components.

    This should always pass for properly installed MarlOS (via pip install).
    Returns True if OK, False if something is wrong.
    """
    source_root = get_source_root()

    if source_root is None or not (source_root / "agent" / "main.py").exists():
        console.print("\n[bold red]⚠️  MarlOS Installation Error[/bold red]\n")
        console.print("[red]✗[/red] Cannot find MarlOS agent code\n")

        console.print("This usually means MarlOS wasn't installed correctly.\n")
        console.print("[bold yellow]To fix this:[/bold yellow]\n")

        console.print("1. Reinstall MarlOS:")
        console.print("   [cyan]pip uninstall -y marlos[/cyan]")
        console.print("   [cyan]pip install --no-cache-dir marlos[/cyan]\n")

        console.print("2. Or install from GitHub:")
        console.print("   [cyan]pip install git+https://github.com/ayush-jadaun/MarlOS.git[/cyan]\n")

        return False

    return True


def check_agent_running(port=3001):
    """Check if MarlOS agent is running on specified port"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
    except:
        return False


def prompt_start_agent():
    """Prompt user to start agent if not running"""
    console.print("\n[bold yellow]⚠️  MarlOS Agent Not Running[/bold yellow]\n")
    console.print("The MarlOS agent must be running to use this command.\n")
    console.print("[bold]How to Start MarlOS:[/bold]\n")
    console.print("Option 1 - Interactive:")
    console.print("  [cyan]marl start[/cyan]\n")
    console.print("Option 2 - Direct:")
    console.print("  [cyan]cd ~/MarlOS[/cyan]  # or your MarlOS directory")
    console.print("  [cyan]python -m agent.main[/cyan]\n")
    console.print("Option 3 - Docker:")
    console.print("  [cyan]cd ~/MarlOS[/cyan]")
    console.print("  [cyan]docker-compose up -d[/cyan]\n")

    return Confirm.ask("Do you want to start MarlOS now?", default=True)


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
        installed, has_source = check_installation()

        if not installed:
            console.print("[red]⚠ MarlOS not properly installed[/red]\n")
            console.print("Please install MarlOS first:")
            console.print("  [cyan]pip install git+https://github.com/ayush-jadaun/MarlOS.git[/cyan]\n")
            return

        # Show source code status
        if not has_source:
            console.print("[yellow]ℹ️  Note: MarlOS CLI is installed but source code is not available.[/yellow]")
            console.print("   [dim]You can use CLI commands, but to start nodes you'll need the source.[/dim]\n")

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

    # Verify MarlOS installation
    if not verify_installation():
        input("\nPress Enter to continue...")
        return

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

    # Check for existing launch scripts (both .sh and .bat)
    # For pip installs, check user's home directory; for dev, check root_dir
    is_pip_mode = is_pip_installed()
    if is_pip_mode:
        scripts_dir = Path.home() / ".marlos" / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
    else:
        scripts_dir = root_dir

    if os.name == 'nt':
        launch_scripts = list(scripts_dir.glob("start-*.bat"))
    else:
        launch_scripts = list(scripts_dir.glob("start-*.sh"))

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
                if os.name == 'nt':
                    subprocess.run([str(script_to_run)], cwd=scripts_dir, shell=True, check=True)
                else:
                    subprocess.run([str(script_to_run)], cwd=scripts_dir, check=True)
            except KeyboardInterrupt:
                console.print("\n[yellow]Agent stopped[/yellow]")
            return

    # New configuration
    console.print("[yellow]No launch scripts found. Let's create one![/yellow]\n")

    # Ask for network mode
    console.print("[bold cyan]Choose Network Mode:[/bold cyan]\n")
    console.print("  1. [cyan]Private Mode[/cyan] - Connect your own devices (manual setup)")
    console.print("     • Save peer addresses")
    console.print("     • Auto-connect to your devices")
    console.print("     • Full control and privacy\n")
    console.print("  2. [cyan]Public Mode[/cyan] - Join global network (automatic)")
    console.print("     • DHT-based peer discovery")
    console.print("     • Connect to anyone worldwide")
    console.print("     • No manual configuration\n")

    network_mode = Prompt.ask("Select mode", choices=["1", "2"], default="1")
    network_mode_str = "private" if network_mode == "1" else "public"
    dht_enabled = "true" if network_mode == "2" else "false"

    console.print()

    # Ask for optional node name
    default_name = f"node-{os.uname().nodename if hasattr(os, 'uname') else 'windows'}"
    node_name = Prompt.ask("Node name (optional)", default=default_name)

    # Different prompts based on network mode
    bootstrap_peers = []

    if network_mode == "1":
        # Private mode - ask for bootstrap peers
        console.print("\n[cyan]Private Mode Configuration[/cyan]")
        console.print("Bootstrap Peers (comma-separated IPs or domains):")
        console.print("[dim]Examples:[/dim]")
        console.print("[dim]  - 192.168.1.100,192.168.1.101 (local network)[/dim]")
        console.print("[dim]  - 203.45.67.89 (public IP)[/dim]")
        console.print("[dim]  - mypc.duckdns.org (dynamic DNS)[/dim]")
        peers_input = Prompt.ask("Peers (leave empty for standalone)", default="")

        if peers_input:
            ips = [ip.strip() for ip in peers_input.split(',')]
            bootstrap_peers = [f"tcp://{ip}:5555" for ip in ips]
    else:
        # Public mode - no manual peers needed
        console.print("\n[cyan]Public Mode - Automatic Discovery[/cyan]")
        console.print("Your node will automatically discover and connect to peers via DHT\n")

    # Create node configuration
    console.print("\n[cyan]Creating node configuration...[/cyan]")
    node_id, config_path = node_config.create_node_config(
        node_name=node_name,
        network_mode=network_mode_str,
        bootstrap_peers=bootstrap_peers,
        dht_enabled=(network_mode == "2"),
        pub_port=5555,
        dashboard_port=3001
    )

    console.print(f"[green]✓[/green] Node created: [bold]{node_id}[/bold]")
    console.print(f"[green]✓[/green] Config: {config_path}")

    # Determine if this is a pip install or development mode
    is_pip = is_pip_installed()

    # For pip installs, create scripts in user's home directory
    # For development, create in project root
    if is_pip:
        script_dir = Path.home() / ".marlos" / "scripts"
        script_dir.mkdir(parents=True, exist_ok=True)
    else:
        script_dir = root_dir

    # Create launch script - different for Windows vs Unix
    if os.name == 'nt':  # Windows
        script_path = script_dir / f"start-{node_id}.bat"

        # Different script content for pip vs development
        if is_pip:
            # Pip install: packages already in Python path, no venv needed
            script_content = f"""@echo off
REM MarlOS Launch Script for {node_id}
REM Network Mode: {network_mode_str.upper()}
REM Config: {config_path}

set NODE_ID={node_id}

python -m agent.main
"""
        else:
            # Development: need to activate venv
            script_content = f"""@echo off
REM MarlOS Launch Script for {node_id}
REM Network Mode: {network_mode_str.upper()}
REM Config: {config_path}

set NODE_ID={node_id}

cd /d {root_dir}
call venv\\Scripts\\activate.bat
python -m agent.main
"""

        with open(script_path, 'w') as f:
            f.write(script_content)
        console.print(f"\n[green]✓[/green] Launch script created: {script_path}\n")

        if Confirm.ask("Start node now?", default=True):
            try:
                subprocess.run([str(script_path)], cwd=script_dir if is_pip else root_dir, shell=True, check=True)
            except KeyboardInterrupt:
                console.print("\n[yellow]Agent stopped[/yellow]")
    else:  # Linux/Mac
        script_path = script_dir / f"start-{node_id}.sh"

        # Different script content for pip vs development
        if is_pip:
            # Pip install: packages already in Python path, no venv needed
            script_content = f"""#!/bin/bash
# MarlOS Launch Script for {node_id}
# Network Mode: {network_mode_str.upper()}
# Config: {config_path}

export NODE_ID="{node_id}"

python -m agent.main
"""
        else:
            # Development: need to activate venv
            script_content = f"""#!/bin/bash
# MarlOS Launch Script for {node_id}
# Network Mode: {network_mode_str.upper()}
# Config: {config_path}

export NODE_ID="{node_id}"

cd {root_dir}
source venv/bin/activate
python -m agent.main
"""

        with open(script_path, 'w') as f:
            f.write(script_content)
        script_path.chmod(0o755)
        console.print(f"\n[green]✓[/green] Launch script created: {script_path}\n")

        if Confirm.ask("Start node now?", default=True):
            try:
                subprocess.run([str(script_path)], cwd=script_dir if is_pip else root_dir, check=True)
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

    port = int(Prompt.ask("Dashboard port", default="3001"))

    # Check if agent is running
    if not check_agent_running(port):
        if prompt_start_agent():
            start_marlos_interactive()
        return

    command = Prompt.ask("Enter command to execute")

    console.print(f"\n[cyan]Submitting:[/cyan] {command}\n")

    try:
        from cli.marlOS import execute as execute_cmd
        ctx = click.Context(execute_cmd)
        ctx.invoke(execute_cmd, command=command, port=port, payment=10.0, priority=0.5, wait=False)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


def check_status():
    """Check MarlOS status"""
    console.print("\n[bold cyan]📊 MarlOS Status[/bold cyan]\n")

    port = int(Prompt.ask("Dashboard port", default="3001"))

    # Check if agent is running
    if not check_agent_running(port):
        console.print(f"[red]✗[/red] No MarlOS agent running on port {port}\n")
        if prompt_start_agent():
            start_marlos_interactive()
        return

    try:
        from cli.marlOS import status as status_cmd
        ctx = click.Context(status_cmd)
        ctx.invoke(status_cmd, port=port, json_output=False)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


def list_peers():
    """List connected peers"""
    console.print("\n[bold cyan]👥 Connected Peers[/bold cyan]\n")

    port = int(Prompt.ask("Dashboard port", default="3001"))

    # Check if agent is running
    if not check_agent_running(port):
        console.print(f"[red]✗[/red] No MarlOS agent running on port {port}\n")
        if prompt_start_agent():
            start_marlos_interactive()
        return

    try:
        from cli.marlOS import peers as peers_cmd
        ctx = click.Context(peers_cmd)
        ctx.invoke(peers_cmd, port=port)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


def view_wallet():
    """View wallet balance"""
    console.print("\n[bold cyan]💰 Wallet Status[/bold cyan]\n")

    port = int(Prompt.ask("Dashboard port", default="3001"))

    # Check if agent is running
    if not check_agent_running(port):
        console.print(f"[red]✗[/red] No MarlOS agent running on port {port}\n")
        if prompt_start_agent():
            start_marlos_interactive()
        return

    try:
        from cli.marlOS import wallet as wallet_cmd
        ctx = click.Context(wallet_cmd)
        ctx.invoke(wallet_cmd, port=port)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


def live_monitor():
    """Live monitoring dashboard"""
    console.print("\n[bold cyan]📺 Live Monitor[/bold cyan]\n")

    port = int(Prompt.ask("Dashboard port", default="3001"))

    # Check if agent is running
    if not check_agent_running(port):
        console.print(f"[red]✗[/red] No MarlOS agent running on port {port}\n")
        if prompt_start_agent():
            start_marlos_interactive()
        return

    try:
        from cli.marlOS import watch as watch_cmd
        ctx = click.Context(watch_cmd)
        ctx.invoke(watch_cmd, port=port, interval=2)
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

    port = int(Prompt.ask("Dashboard port", default="3001"))

    # Check if agent is running
    if not check_agent_running(port):
        console.print(f"[red]✗[/red] No MarlOS agent running on port {port}\n")
        if prompt_start_agent():
            start_marlos_interactive()
        return

    job_file = Prompt.ask("Job file path", default="job.json")

    try:
        from cli.marlOS import submit as submit_cmd
        ctx = click.Context(submit_cmd)
        ctx.invoke(submit_cmd, job_file=job_file, port=port, method='ws', wait=False)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


def view_current_config():
    """View current configuration"""
    console.print("\n[bold cyan]Current Configuration[/bold cyan]\n")

    # Environment variables
    env_vars = {
        "NODE_ID": os.environ.get("NODE_ID", "not set"),
        "NETWORK_MODE": os.environ.get("NETWORK_MODE", "private"),
        "DHT_ENABLED": os.environ.get("DHT_ENABLED", "false"),
        "BOOTSTRAP_PEERS": os.environ.get("BOOTSTRAP_PEERS", "none"),
        "PUB_PORT": os.environ.get("PUB_PORT", "5555"),
        "SUB_PORT": os.environ.get("SUB_PORT", "5556"),
        "DASHBOARD_PORT": os.environ.get("DASHBOARD_PORT", "3001"),
    }

    table = Table(title="Environment Variables", box=box.ROUNDED)
    table.add_column("Variable", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    for var, value in env_vars.items():
        table.add_row(var, value)

    console.print(table)
    console.print()

    # Check for YAML config
    yaml_config = Path.home() / ".marlos" / "config.yaml"
    if yaml_config.exists():
        console.print(f"[green]✓[/green] YAML Config: {yaml_config}")
    else:
        console.print(f"[dim]YAML Config: Not created (using defaults)[/dim]")

    # Check for peers file
    peers_file = Path.home() / ".marlos" / "peers.json"
    if peers_file.exists():
        try:
            import json
            with open(peers_file) as f:
                data = json.load(f)
                peer_count = len(data.get('peers', []))
            console.print(f"[green]✓[/green] Saved Peers: {peer_count} peers")
        except:
            console.print(f"[yellow]⚠[/yellow] Saved Peers: Error reading file")
    else:
        console.print(f"[dim]Saved Peers: No peers saved[/dim]")


def edit_yaml_config(yaml_config: Path):
    """Edit YAML configuration file"""
    console.print("\n[bold cyan]Edit YAML Config[/bold cyan]\n")

    # Create if doesn't exist
    if not yaml_config.exists():
        console.print("[yellow]Config file doesn't exist. Generating sample...[/yellow]\n")
        generate_sample_config(yaml_config, show_message=False)

    console.print(f"Config file: [cyan]{yaml_config}[/cyan]\n")

    # Determine editor
    if os.name == 'nt':
        # Windows: try common editors
        editors = ["notepad.exe", "code", "notepad++"]
        editor = None
        for ed in editors:
            if subprocess.run(["where", ed], capture_output=True).returncode == 0:
                editor = ed
                break
        if not editor:
            editor = "notepad.exe"
    else:
        # Linux/Mac
        editor = os.environ.get("EDITOR", "nano")

    console.print(f"Opening with: [cyan]{editor}[/cyan]")
    console.print("[dim]Save and close the editor when done[/dim]\n")

    try:
        subprocess.run([editor, str(yaml_config)])
        console.print("\n[green]✓[/green] Config file saved")
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        console.print(f"\n[yellow]Manually edit:[/yellow] {yaml_config}")


def manage_peers_menu():
    """Manage saved peers"""
    console.print("\n[bold cyan]Manage Saved Peers[/bold cyan]\n")

    try:
        from agent.p2p.peer_manager import PeerManager
        peer_mgr = PeerManager()

        while True:
            console.print("[bold]Peer Management:[/bold]\n")
            console.print("  1. List all peers")
            console.print("  2. Add new peer")
            console.print("  3. Remove peer")
            console.print("  4. Toggle auto-connect")
            console.print("  5. Export peers")
            console.print("  6. Import peers")
            console.print("  0. Back")
            console.print()

            choice = Prompt.ask("Select option", choices=["0","1","2","3","4","5","6"])

            if choice == "0":
                break

            elif choice == "1":
                peer_mgr.list_peers()

            elif choice == "2":
                console.print("\n[cyan]Add New Peer[/cyan]\n")
                name = Prompt.ask("Peer name (e.g., 'My Office PC')")
                console.print("\n[dim]Examples:[/dim]")
                console.print("[dim]  - tcp://192.168.1.100:5555 (local)[/dim]")
                console.print("[dim]  - tcp://203.45.67.89:5555 (public IP)[/dim]")
                console.print("[dim]  - tcp://mypc.duckdns.org:5555 (DNS)[/dim]")
                address = Prompt.ask("Peer address")
                notes = Prompt.ask("Notes (optional)", default="")
                auto = Confirm.ask("Auto-connect on startup?", default=True)

                if peer_mgr.add_peer(name, address, notes=notes, auto_connect=auto):
                    console.print(f"\n[green]✓[/green] Peer added: {name}\n")
                else:
                    console.print(f"\n[yellow]⚠[/yellow] Peer already exists\n")

            elif choice == "3":
                peer_mgr.list_peers()
                if peer_mgr.peers:
                    address = Prompt.ask("Enter peer address to remove")
                    if peer_mgr.remove_peer(address):
                        console.print(f"\n[green]✓[/green] Peer removed\n")
                    else:
                        console.print(f"\n[red]✗[/red] Peer not found\n")

            elif choice == "4":
                peer_mgr.list_peers()
                if peer_mgr.peers:
                    address = Prompt.ask("Enter peer address")
                    peer = peer_mgr.get_peer(address)
                    if peer:
                        new_value = not peer.auto_connect
                        peer_mgr.update_peer(address, auto_connect=new_value)
                        status = "enabled" if new_value else "disabled"
                        console.print(f"\n[green]✓[/green] Auto-connect {status}\n")

            elif choice == "5":
                output = Prompt.ask("Export to file", default="peers_backup.json")
                peer_mgr.export_peers(output)
                console.print()

            elif choice == "6":
                input_file = Prompt.ask("Import from file")
                merge = Confirm.ask("Merge with existing peers?", default=True)
                peer_mgr.import_peers(input_file, merge=merge)
                console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\n[yellow]Tip:[/yellow] Make sure you're running in private mode")


def edit_launch_script():
    """Edit launch script"""
    console.print("\n[bold cyan]Edit Launch Script[/bold cyan]\n")

    # Find launch scripts
    scripts_dir = Path.home() / ".marlos" / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    if os.name == 'nt':
        launch_scripts = list(scripts_dir.glob("start-*.bat"))
    else:
        launch_scripts = list(scripts_dir.glob("start-*.sh"))

    if not launch_scripts:
        console.print("[yellow]No launch scripts found[/yellow]")
        console.print("Create one by: [cyan]marl → Start MarlOS → Native/Real Device[/cyan]\n")
        return

    console.print("Available launch scripts:\n")
    for i, script in enumerate(launch_scripts, 1):
        console.print(f"  {i}. {script.name}")
    console.print()

    idx = int(Prompt.ask("Select script", default="1")) - 1
    script_path = launch_scripts[idx]

    # Determine editor
    if os.name == 'nt':
        editor = "notepad.exe"
    else:
        editor = os.environ.get("EDITOR", "nano")

    try:
        subprocess.run([editor, str(script_path)])
        console.print("\n[green]✓[/green] Script saved")
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")


def _generate_basic_config() -> str:
    """Generate basic config as fallback"""
    return """# MarlOS Basic Configuration
# For full config with all features, use the agent-config.yml template

# Node Configuration
node_id: my-node-1
node_name: "My MarlOS Node"
data_dir: ~/.marlos/data

# Network Configuration
network:
  mode: private
  pub_port: 5555
  sub_port: 5556
  beacon_port: 5557
  bootstrap_peers: []
  dht_enabled: false
  dht_port: 5559
  discovery_interval: 5
  heartbeat_interval: 3
  max_peers: 50

# Token Economy
token_economy:
  starting_balance: 100.0
  network_fee: 0.05
  idle_reward: 1.0
  stake_requirement: 10.0

# Trust System
trust:
  starting_trust: 0.5
  max_trust: 1.0
  min_trust: 0.0
  quarantine_threshold: 0.2

# Reinforcement Learning
reinforcement_learning:
  enabled: true
  model_path: "rl_trainer/models/policy_v1.zip"

# Job Executor
executor:
  max_concurrent_jobs: 3
  job_timeout: 300
  docker_enabled: true

# Dashboard
dashboard:
  enabled: true
  host: "0.0.0.0"
  port: 3001
"""


def generate_sample_config(yaml_config: Path, show_message: bool = True):
    """Generate sample configuration file (copies from agent-config.yml template)"""
    if show_message:
        console.print("\n[bold cyan]Generate Sample Config[/bold cyan]\n")

    # Check if we have the full agent-config.yml template
    template_path = MARLOS_ROOT / "agent-config.yml"

    if template_path.exists():
        # Use the full template from the repository
        try:
            with open(template_path, 'r') as f:
                sample_config = f.read()

            if show_message:
                console.print("[green]✓[/green] Using full agent-config.yml template")

        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not read template: {e}")
            console.print("[yellow]Generating basic config instead...[/yellow]\n")
            sample_config = _generate_basic_config()
    else:
        # Fallback: generate basic config
        if show_message:
            console.print("[yellow]Note:[/yellow] Full template not found, using basic config")
            console.print(f"[dim]For full config, copy from: {template_path}[/dim]\n")
        sample_config = _generate_basic_config()

    try:
        with open(yaml_config, 'w') as f:
            f.write(sample_config)

        if show_message:
            console.print(f"[green]✓[/green] Sample config generated: {yaml_config}\n")
            console.print("[dim]Edit the file to customize your settings[/dim]")
            console.print(f"[dim]Then start agent with: python -m agent.main --config {yaml_config}[/dim]\n")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


def copy_full_template(yaml_config: Path):
    """Copy the full agent-config.yml template to user's config directory"""
    console.print("\n[bold cyan]Copy Full Configuration Template[/bold cyan]\n")

    # Find the full template
    template_path = MARLOS_ROOT / "agent-config.yml"

    if not template_path.exists():
        console.print("[red]✗[/red] Full template not found")
        console.print(f"[dim]Expected at: {template_path}[/dim]")
        console.print("\n[yellow]Tip:[/yellow] This file exists in the repository")
        console.print("Clone from: [cyan]https://github.com/ayush-jadaun/MarlOS.git[/cyan]\n")
        return

    # Check if target already exists
    if yaml_config.exists():
        console.print(f"[yellow]⚠[/yellow] Config already exists: {yaml_config}")
        if not Confirm.ask("Overwrite existing config?", default=False):
            console.print("[dim]Cancelled[/dim]")
            return

    try:
        # Copy the full template
        import shutil
        shutil.copy2(template_path, yaml_config)

        console.print(f"\n[green]✓[/green] Copied full template to: {yaml_config}")
        console.print(f"[dim]Source: {template_path}[/dim]\n")

        # Show what's included
        console.print("[bold]Template includes:[/bold]")
        console.print("  • Agent identity")
        console.print("  • Network configuration (P2P, security)")
        console.print("  • Token economy (taxation, UBI, fairness)")
        console.print("  • Trust & reputation system")
        console.print("  • Reinforcement learning")
        console.print("  • Bidding & auction system")
        console.print("  • Job execution (9+ runner types)")
        console.print("  • Predictive pre-execution")
        console.print("  • Dashboard & monitoring")
        console.print("  • Logging configuration")
        console.print("  • Performance tuning")
        console.print("  • Security settings")
        console.print("  • Experimental features")
        console.print("  • Benchmarking tools\n")

        console.print("[cyan]Next steps:[/cyan]")
        console.print("  1. Edit the config: [cyan]marl → Configuration → Edit YAML Config[/cyan]")
        console.print(f"  2. Start agent with: [cyan]python -m agent.main --config {yaml_config}[/cyan]\n")

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")


def network_mode_settings():
    """Configure network mode settings"""
    console.print("\n[bold cyan]Network Mode Settings[/bold cyan]\n")

    console.print("Current mode can be changed by:")
    console.print("  1. Editing launch script (Option 4)")
    console.print("  2. Setting environment variables:")
    console.print("     [cyan]export NETWORK_MODE=private[/cyan]  # or 'public'")
    console.print("     [cyan]export DHT_ENABLED=true[/cyan]")
    console.print("  3. Creating new launch script with different mode\n")

    console.print("[bold]Network Modes:[/bold]\n")
    console.print("  [cyan]PRIVATE[/cyan] - Connect your own devices")
    console.print("    • Manual peer management")
    console.print("    • Full privacy and control")
    console.print("    • Use: [cyan]NETWORK_MODE=private[/cyan]\n")

    console.print("  [cyan]PUBLIC[/cyan] - Join global network")
    console.print("    • Automatic DHT discovery")
    console.print("    • Connect to anyone")
    console.print("    • Use: [cyan]NETWORK_MODE=public DHT_ENABLED=true[/cyan]\n")


def reset_config_to_defaults(yaml_config: Path, peers_file: Path):
    """Reset configuration to defaults"""
    console.print("\n[bold yellow]⚠️  Reset Configuration[/bold yellow]\n")

    console.print("This will:")
    console.print("  • Delete YAML config file")
    console.print("  • Keep saved peers (optional)")
    console.print("  • Keep launch scripts")
    console.print()

    if not Confirm.ask("Are you sure?", default=False):
        console.print("[dim]Cancelled[/dim]")
        return

    try:
        # Remove YAML config
        if yaml_config.exists():
            yaml_config.unlink()
            console.print("[green]✓[/green] YAML config reset")

        # Ask about peers
        if peers_file.exists():
            if Confirm.ask("Also delete saved peers?", default=False):
                peers_file.unlink()
                console.print("[green]✓[/green] Saved peers deleted")
            else:
                console.print("[dim]Saved peers kept[/dim]")

        console.print("\n[green]✓[/green] Configuration reset to defaults\n")

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")


def configuration_menu():
    """Enhanced configuration menu"""
    console.clear()
    console.print("\n[bold cyan]⚙️  Configuration Management[/bold cyan]\n")

    # Get correct root directory
    if is_pip_installed():
        source_root = get_source_root()
        root_dir = source_root if source_root else MARLOS_ROOT
    else:
        root_dir = MARLOS_ROOT

    # Config file locations
    config_dir = Path.home() / ".marlos"
    config_dir.mkdir(parents=True, exist_ok=True)
    yaml_config = config_dir / "config.yaml"
    peers_file = config_dir / "peers.json"

    table = Table(show_header=False, box=box.ROUNDED)
    table.add_column("Option", style="bold")
    table.add_column("Description", style="cyan")

    table.add_row("1", "📝 View Current Configuration")
    table.add_row("2", "✏️  Edit YAML Config File")
    table.add_row("3", "📋 Manage Saved Peers (Private Mode)")
    table.add_row("4", "🔧 Edit Launch Script")
    table.add_row("5", "📄 Generate Sample Config")
    table.add_row("6", "📋 Copy Full agent-config.yml Template")
    table.add_row("7", "🌐 Network Mode Settings")
    table.add_row("8", "♻️  Reset to Defaults")
    table.add_row("0", "← Back to Main Menu")

    console.print(table)
    console.print()

    choice = Prompt.ask("Select option", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8"])

    if choice == "1":
        # View current configuration
        view_current_config()

    elif choice == "2":
        # Edit YAML config
        edit_yaml_config(yaml_config)

    elif choice == "3":
        # Manage peers
        manage_peers_menu()

    elif choice == "4":
        # Edit launch script
        edit_launch_script()

    elif choice == "5":
        # Generate sample config
        generate_sample_config(yaml_config)

    elif choice == "6":
        # Copy full template
        copy_full_template(yaml_config)

    elif choice == "7":
        # Network mode settings
        network_mode_settings()

    elif choice == "8":
        # Reset to defaults
        reset_config_to_defaults(yaml_config, peers_file)


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
@click.version_option(version="1.0.5", prog_name="MarlOS")
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
    # Check if agent is running
    if not check_agent_running(port):
        console.print(f"\n[red]✗[/red] No MarlOS agent running on port {port}\n")
        console.print("Start MarlOS first:")
        console.print("  [cyan]marl start[/cyan]\n")
        return

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
    # Check if agent is running
    if not check_agent_running(port):
        console.print(f"\n[red]✗[/red] No MarlOS agent running on port {port}\n")
        console.print("Start MarlOS first:")
        console.print("  [cyan]marl start[/cyan]\n")
        return

    from cli.marlOS import status as status_impl
    ctx = click.Context(status_impl)
    ctx.invoke(status_impl, port=port, json_output=json_output)


@cli.command()
@click.option('--port', '-p', default=3001, help='Dashboard port')
def peers(port):
    """List connected peers"""
    # Check if agent is running
    if not check_agent_running(port):
        console.print(f"\n[red]✗[/red] No MarlOS agent running on port {port}\n")
        console.print("Start MarlOS first:")
        console.print("  [cyan]marl start[/cyan]\n")
        return

    from cli.marlOS import peers as peers_impl
    ctx = click.Context(peers_impl)
    ctx.invoke(peers_impl, port=port)


@cli.command()
@click.option('--port', '-p', default=3001, help='Dashboard port')
def wallet(port):
    """Show wallet balance"""
    # Check if agent is running
    if not check_agent_running(port):
        console.print(f"\n[red]✗[/red] No MarlOS agent running on port {port}\n")
        console.print("Start MarlOS first:")
        console.print("  [cyan]marl start[/cyan]\n")
        return

    from cli.marlOS import wallet as wallet_impl
    ctx = click.Context(wallet_impl)
    ctx.invoke(wallet_impl, port=port)


@cli.command()
@click.option('--port', '-p', default=3001, help='Dashboard port')
@click.option('--interval', '-i', default=2, help='Update interval (seconds)')
def watch(port, interval):
    """Real-time monitoring"""
    # Check if agent is running
    if not check_agent_running(port):
        console.print(f"\n[red]✗[/red] No MarlOS agent running on port {port}\n")
        console.print("Start MarlOS first:")
        console.print("  [cyan]marl start[/cyan]\n")
        return

    from cli.marlOS import watch as watch_impl
    ctx = click.Context(watch_impl)
    ctx.invoke(watch_impl, port=port, interval=interval)


@cli.command()
@click.argument('job_file', type=click.Path(exists=True))
@click.option('--port', '-p', default=3001, help='Dashboard port')
@click.option('--wait', '-w', is_flag=True, help='Wait for completion')
def submit(job_file, port, wait):
    """Submit a job from file"""
    # Check if agent is running
    if not check_agent_running(port):
        console.print(f"\n[red]✗[/red] No MarlOS agent running on port {port}\n")
        console.print("Start MarlOS first:")
        console.print("  [cyan]marl start[/cyan]\n")
        return

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
    # Verify MarlOS installation
    if not verify_installation():
        return

    print_banner()
    start_marlos_interactive()


@cli.command()
def version():
    """Show version information"""
    console.print("\n[bold cyan]🌌 MarlOS v1.0.5[/bold cyan]")
    console.print("[cyan]Autonomous Distributed Computing Operating System[/cyan]")
    console.print("\n[dim]Built by Team async_await[/dim]\n")


# Node management commands
@cli.group()
def nodes():
    """Manage MarlOS nodes"""
    pass


@nodes.command('list')
def list_nodes():
    """List all configured nodes"""
    nodes = node_config.list_nodes()

    if not nodes:
        console.print("\n[yellow]No nodes configured yet.[/yellow]")
        console.print("[dim]Run 'marlos start' to create your first node.[/dim]\n")
        return

    console.print(f"\n[bold cyan]Configured Nodes ({len(nodes)})[/bold cyan]\n")

    from rich.table import Table
    table = Table()
    table.add_column("Node ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Mode", style="yellow")
    table.add_column("Created", style="dim")

    for node_info in nodes:
        table.add_row(
            node_info['node_id'],
            node_info.get('node_name', 'N/A'),
            node_info.get('network', {}).get('mode', 'N/A').upper(),
            node_info.get('created', 'N/A')
        )

    console.print(table)
    console.print()


@nodes.command('show')
@click.argument('node_id')
def show_node(node_id):
    """Show detailed configuration for a node"""
    import json
    from pathlib import Path

    config_path = Path.home() / ".marlos" / "nodes" / node_id / "config.json"

    if not config_path.exists():
        console.print(f"\n[red]Error:[/red] Node '{node_id}' not found\n")
        return

    with open(config_path) as f:
        config = json.load(f)

    console.print(f"\n[bold cyan]Node: {node_id}[/bold cyan]")
    console.print(f"[dim]Config: {config_path}[/dim]\n")

    # Pretty print the config
    from rich.syntax import Syntax
    config_json = json.dumps(config, indent=2)
    syntax = Syntax(config_json, "json", theme="monokai", line_numbers=True)
    console.print(syntax)
    console.print()


@nodes.command('edit')
@click.argument('node_id')
def edit_node(node_id):
    """Edit node configuration in your default editor"""
    import subprocess
    from pathlib import Path

    config_path = Path.home() / ".marlos" / "nodes" / node_id / "config.json"

    if not config_path.exists():
        console.print(f"\n[red]Error:[/red] Node '{node_id}' not found\n")
        return

    console.print(f"\n[cyan]Opening config in editor...[/cyan]")
    console.print(f"[dim]{config_path}[/dim]\n")

    # Use the system's default editor
    editor = os.getenv('EDITOR', 'notepad' if os.name == 'nt' else 'nano')

    try:
        subprocess.run([editor, str(config_path)], check=True)
        console.print("[green]✓[/green] Config updated\n")
    except subprocess.CalledProcessError:
        console.print("[red]Error opening editor[/red]\n")


@nodes.command('delete')
@click.argument('node_id')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation')
def delete_node(node_id, force):
    """Delete a node and its configuration"""
    import shutil
    from pathlib import Path

    node_dir = Path.home() / ".marlos" / "nodes" / node_id

    if not node_dir.exists():
        console.print(f"\n[red]Error:[/red] Node '{node_id}' not found\n")
        return

    if not force:
        from rich.prompt import Confirm
        if not Confirm.ask(f"\n[yellow]Delete node '{node_id}' and all its data?[/yellow]"):
            console.print("[dim]Cancelled[/dim]\n")
            return

    try:
        shutil.rmtree(node_dir)
        console.print(f"\n[green]✓[/green] Deleted node: {node_id}\n")
    except Exception as e:
        console.print(f"\n[red]Error deleting node:[/red] {e}\n")


if __name__ == '__main__':
    cli()
