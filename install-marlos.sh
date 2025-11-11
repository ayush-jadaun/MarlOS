#!/bin/bash
###############################################################################
# MarlOS - Interactive Installation & Setup Script
#
# This script will:
# - Clone the repository (if needed)
# - Install all dependencies
# - Configure your node interactively
# - Set up networking and firewall
# - Start your MarlOS agent
#
# Usage: curl -sSL https://raw.githubusercontent.com/ayush-jadaun/MarlOS/main/install-marlos.sh | bash
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Configuration variables
REPO_URL="https://github.com/ayush-jadaun/MarlOS.git"
INSTALL_DIR="$HOME/MarlOS"
NODE_ID=""
DEPLOYMENT_MODE=""
BOOTSTRAP_PEERS=""
ENABLE_DOCKER="false"
ENABLE_HARDWARE="false"
MQTT_BROKER="localhost"

###############################################################################
# Utility Functions
###############################################################################

print_banner() {
    clear
    echo -e "${CYAN}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███╗   ███╗ █████╗ ██████╗ ██╗      ██████╗ ███████╗      ║
║   ████╗ ████║██╔══██╗██╔══██╗██║     ██╔═══██╗██╔════╝      ║
║   ██╔████╔██║███████║██████╔╝██║     ██║   ██║███████╗      ║
║   ██║╚██╔╝██║██╔══██║██╔══██╗██║     ██║   ██║╚════██║      ║
║   ██║ ╚═╝ ██║██║  ██║██║  ██║███████╗╚██████╔╝███████║      ║
║   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝      ║
║                                                               ║
║        Distributed Computing Operating System                ║
║        Interactive Installation Script v1.0                  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

print_step() {
    echo -e "\n${BOLD}${BLUE}==>${NC} ${BOLD}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

ask_question() {
    echo -e "\n${YELLOW}?${NC} ${BOLD}$1${NC}"
}

ask_yes_no() {
    while true; do
        echo -e "${YELLOW}?${NC} ${BOLD}$1${NC} ${CYAN}(y/n)${NC}: "
        read -r response
        case "$response" in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Please answer yes (y) or no (n).";;
        esac
    done
}

detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            DISTRO=$ID
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        DISTRO="macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
        DISTRO="windows"
    else
        OS="unknown"
        DISTRO="unknown"
    fi
}

get_local_ip() {
    if [[ "$OS" == "linux" ]]; then
        ip addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v 127.0.0.1 | head -1
    elif [[ "$OS" == "macos" ]]; then
        ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1
    else
        ipconfig | grep "IPv4" | awk '{print $NF}' | head -1
    fi
}

check_command() {
    command -v "$1" >/dev/null 2>&1
}

###############################################################################
# Installation Functions
###############################################################################

install_dependencies_linux() {
    print_step "Installing dependencies for Linux ($DISTRO)..."

    # Update package list
    if [[ "$DISTRO" == "ubuntu" ]] || [[ "$DISTRO" == "debian" ]]; then
        print_info "Updating package list..."
        sudo apt-get update -qq

        print_info "Installing system dependencies..."
        sudo apt-get install -y -qq \
            python3 \
            python3-pip \
            python3-venv \
            git \
            curl \
            build-essential \
            libzmq3-dev \
            nmap \
            net-tools

    elif [[ "$DISTRO" == "fedora" ]] || [[ "$DISTRO" == "rhel" ]] || [[ "$DISTRO" == "centos" ]]; then
        print_info "Installing system dependencies..."
        sudo dnf install -y \
            python3 \
            python3-pip \
            git \
            curl \
            gcc \
            zeromq-devel \
            nmap \
            net-tools

    elif [[ "$DISTRO" == "arch" ]]; then
        print_info "Installing system dependencies..."
        sudo pacman -S --noconfirm \
            python \
            python-pip \
            git \
            curl \
            base-devel \
            zeromq \
            nmap \
            net-tools
    fi

    print_success "System dependencies installed"
}

install_dependencies_macos() {
    print_step "Installing dependencies for macOS..."

    # Check if Homebrew is installed
    if ! check_command brew; then
        print_warning "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    print_info "Installing system dependencies..."
    brew install python3 git zeromq nmap

    print_success "System dependencies installed"
}

install_dependencies_windows() {
    print_step "Installing dependencies for Windows..."
    print_warning "Windows detected. Please ensure you have:"
    echo "  - Python 3.11+ installed"
    echo "  - Git installed"
    echo "  - Visual C++ Build Tools (for zeromq)"

    if ! ask_yes_no "Do you have these installed?"; then
        print_info "Please install:"
        echo "  1. Python: https://www.python.org/downloads/"
        echo "  2. Git: https://git-scm.com/download/win"
        echo "  3. Build Tools: https://visualstudio.microsoft.com/downloads/"
        exit 1
    fi
}

clone_repository() {
    print_step "Setting up MarlOS repository..."

    if [ -d "$INSTALL_DIR" ]; then
        if ask_yes_no "MarlOS directory already exists at $INSTALL_DIR. Update it?"; then
            cd "$INSTALL_DIR"
            print_info "Pulling latest changes..."
            git pull
        else
            print_info "Using existing repository"
        fi
    else
        print_info "Cloning MarlOS from GitHub..."
        git clone "$REPO_URL" "$INSTALL_DIR"
        print_success "Repository cloned to $INSTALL_DIR"
    fi

    cd "$INSTALL_DIR"
}

setup_python_environment() {
    print_step "Setting up Python virtual environment..."

    # Create venv if it doesn't exist
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    fi

    # Activate venv
    print_info "Activating virtual environment..."
    source venv/bin/activate

    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip -q

    # Install dependencies
    print_info "Installing Python dependencies (this may take a few minutes)..."
    pip install -r requirements.txt -q

    print_success "Python dependencies installed"
}

setup_firewall() {
    print_step "Setting up firewall rules..."

    if ! ask_yes_no "Do you want to configure firewall rules automatically?"; then
        print_warning "Skipping firewall configuration. You'll need to manually open ports 5555, 5556, and 3001."
        return
    fi

    if [[ "$OS" == "linux" ]]; then
        if check_command ufw; then
            print_info "Configuring UFW firewall..."
            sudo ufw allow 5555/tcp comment "MarlOS PUB" 2>/dev/null || true
            sudo ufw allow 5556/tcp comment "MarlOS SUB" 2>/dev/null || true
            sudo ufw allow 3001/tcp comment "MarlOS Dashboard" 2>/dev/null || true
            sudo ufw allow 1883/tcp comment "MQTT Broker" 2>/dev/null || true
            print_success "Firewall rules added"
        elif check_command firewall-cmd; then
            print_info "Configuring firewalld..."
            sudo firewall-cmd --permanent --add-port=5555/tcp
            sudo firewall-cmd --permanent --add-port=5556/tcp
            sudo firewall-cmd --permanent --add-port=3001/tcp
            sudo firewall-cmd --permanent --add-port=1883/tcp
            sudo firewall-cmd --reload
            print_success "Firewall rules added"
        else
            print_warning "No supported firewall detected. Please manually open ports 5555, 5556, 3001"
        fi
    elif [[ "$OS" == "macos" ]]; then
        print_info "macOS firewall configuration requires manual setup in System Preferences > Security > Firewall"
        print_info "Please allow incoming connections for Python"
    elif [[ "$OS" == "windows" ]]; then
        print_info "Configuring Windows Firewall..."
        powershell.exe -Command "New-NetFirewallRule -DisplayName 'MarlOS Ports' -Direction Inbound -Protocol TCP -LocalPort 5555,5556,3001 -Action Allow" 2>/dev/null || print_warning "Failed to configure firewall automatically"
    fi
}

###############################################################################
# Configuration Functions
###############################################################################

choose_deployment_mode() {
    print_step "Choose Deployment Mode"

    echo -e "\n${BOLD}Select how you want to run MarlOS:${NC}\n"
    echo "  1) Docker Containers (for local testing with multiple nodes)"
    echo "  2) Real Device / Native (for distributed computing across actual devices)"
    echo "  3) Development Mode (single node for testing)"
    echo ""

    while true; do
        read -p "Enter your choice (1-3): " choice
        case $choice in
            1)
                DEPLOYMENT_MODE="docker"
                print_success "Docker mode selected"
                break
                ;;
            2)
                DEPLOYMENT_MODE="native"
                print_success "Native/Real Device mode selected"
                break
                ;;
            3)
                DEPLOYMENT_MODE="dev"
                print_success "Development mode selected"
                break
                ;;
            *)
                print_error "Invalid choice. Please enter 1, 2, or 3."
                ;;
        esac
    done
}

configure_docker_deployment() {
    print_step "Configuring Docker Deployment"

    # Check if Docker is installed
    if ! check_command docker; then
        print_error "Docker is not installed!"
        echo ""
        print_info "Please install Docker first:"
        echo "  - Linux: https://docs.docker.com/engine/install/"
        echo "  - macOS: https://docs.docker.com/desktop/install/mac-install/"
        echo "  - Windows: https://docs.docker.com/desktop/install/windows-install/"
        exit 1
    fi

    print_success "Docker detected"

    if ask_yes_no "Do you want to start MarlOS with Docker Compose now?"; then
        print_info "Starting MarlOS with Docker Compose..."
        docker-compose up -d

        echo ""
        print_success "MarlOS is now running in Docker!"
        echo ""
        print_info "Access points:"
        echo "  - Agent 1 Dashboard: http://localhost:8081"
        echo "  - Agent 2 Dashboard: http://localhost:8082"
        echo "  - Agent 3 Dashboard: http://localhost:8083"
        echo ""
        print_info "Submit a test job:"
        echo "  python cli/marlOS.py execute 'echo Hello MarlOS' --port 8081"
    fi
}

configure_native_deployment() {
    print_step "Configuring Native Deployment"

    # Get node ID
    ask_question "Enter a unique Node ID for this device (e.g., laptop-1, server-a):"
    read -p "Node ID: " NODE_ID

    if [ -z "$NODE_ID" ]; then
        NODE_ID="node-$(hostname)-$(date +%s)"
        print_warning "No ID provided. Using: $NODE_ID"
    fi

    print_success "Node ID: $NODE_ID"

    # Detect local IP
    LOCAL_IP=$(get_local_ip)
    echo ""
    print_info "Detected local IP: $LOCAL_IP"

    # Network topology
    echo ""
    print_step "Network Configuration"
    echo -e "\n${BOLD}How will nodes connect?${NC}\n"
    echo "  1) Same WiFi/LAN (e.g., home network, office network)"
    echo "  2) Different Networks (Internet/WAN with public IPs)"
    echo "  3) Hybrid (some local, some remote)"
    echo "  4) Single node (no peers yet)"
    echo ""

    read -p "Enter your choice (1-4): " network_choice

    case $network_choice in
        1)
            configure_lan_network
            ;;
        2)
            configure_wan_network
            ;;
        3)
            configure_hybrid_network
            ;;
        4)
            print_info "Running as single node. You can add peers later."
            BOOTSTRAP_PEERS=""
            ;;
        *)
            print_warning "Invalid choice. Running as single node."
            BOOTSTRAP_PEERS=""
            ;;
    esac

    # Docker option
    echo ""
    if ask_yes_no "Enable Docker job execution? (requires Docker to be installed)"; then
        if check_command docker; then
            ENABLE_DOCKER="true"
            print_success "Docker execution enabled"
        else
            print_warning "Docker not found. Docker jobs will be disabled."
            ENABLE_DOCKER="false"
        fi
    else
        ENABLE_DOCKER="false"
        print_info "Docker execution disabled. Shell and security jobs will still work."
    fi

    # Hardware option
    echo ""
    if ask_yes_no "Enable hardware control (Arduino/ESP32 via MQTT)?"; then
        ENABLE_HARDWARE="true"
        ask_question "Enter MQTT broker address (default: localhost):"
        read -p "MQTT Broker: " MQTT_BROKER
        [ -z "$MQTT_BROKER" ] && MQTT_BROKER="localhost"
        print_success "Hardware control enabled with broker: $MQTT_BROKER"
    else
        ENABLE_HARDWARE="false"
    fi
}

configure_lan_network() {
    print_info "Configuring for same LAN/WiFi network"
    echo ""
    print_info "Other devices on your network should use these IPs in their BOOTSTRAP_PEERS:"
    echo "  tcp://$LOCAL_IP:5555"
    echo ""

    ask_question "Enter the IP addresses of other MarlOS nodes (comma-separated)"
    echo "Example: 192.168.1.100,192.168.1.101"
    read -p "Peer IPs: " peer_ips

    if [ -n "$peer_ips" ]; then
        # Convert IPs to tcp:// format
        BOOTSTRAP_PEERS=""
        IFS=',' read -ra IPS <<< "$peer_ips"
        for ip in "${IPS[@]}"; do
            ip=$(echo "$ip" | xargs)  # Trim whitespace
            if [ -n "$BOOTSTRAP_PEERS" ]; then
                BOOTSTRAP_PEERS="${BOOTSTRAP_PEERS},"
            fi
            BOOTSTRAP_PEERS="${BOOTSTRAP_PEERS}tcp://${ip}:5555"
        done
        print_success "Bootstrap peers: $BOOTSTRAP_PEERS"
    else
        print_warning "No peers specified. This node will run standalone."
        BOOTSTRAP_PEERS=""
    fi
}

configure_wan_network() {
    print_info "Configuring for Internet/WAN deployment"
    echo ""
    print_warning "Important: You need to set up port forwarding on your router!"
    print_info "Forward these ports to $LOCAL_IP:"
    echo "  - Port 5555 (TCP) - MarlOS Publisher"
    echo "  - Port 5556 (TCP) - MarlOS Subscriber"
    echo "  - Port 3001 (TCP) - Dashboard (optional)"
    echo ""

    ask_question "Enter your public IP or domain name:"
    read -p "Public IP/Domain: " public_ip

    if [ -z "$public_ip" ]; then
        public_ip=$(curl -s ifconfig.me)
        print_info "Auto-detected public IP: $public_ip"
    fi

    echo ""
    print_info "Share this with other nodes:"
    echo "  tcp://${public_ip}:5555"
    echo ""

    ask_question "Enter bootstrap peer addresses (comma-separated)"
    echo "Example: tcp://203.0.113.45:5555,tcp://198.51.100.89:5555"
    read -p "Bootstrap Peers: " BOOTSTRAP_PEERS

    if [ -z "$BOOTSTRAP_PEERS" ]; then
        print_warning "No peers specified. This node will run standalone."
    fi
}

configure_hybrid_network() {
    print_info "Configuring for hybrid network (local + remote)"
    echo ""

    ask_question "Enter all bootstrap peers (local IPs and public IPs, comma-separated)"
    echo "Example: tcp://192.168.1.100:5555,tcp://203.0.113.45:5555"
    read -p "Bootstrap Peers: " BOOTSTRAP_PEERS

    if [ -z "$BOOTSTRAP_PEERS" ]; then
        print_warning "No peers specified. This node will run standalone."
    fi
}

configure_dev_mode() {
    print_step "Configuring Development Mode"

    NODE_ID="dev-node-$(hostname)"
    BOOTSTRAP_PEERS=""
    ENABLE_DOCKER="false"
    ENABLE_HARDWARE="false"

    print_success "Development configuration set"
}

###############################################################################
# Launch Script Generation
###############################################################################

create_launch_script() {
    print_step "Creating launch script..."

    local script_name="start-${NODE_ID}.sh"

    cat > "$script_name" << EOF
#!/bin/bash
# MarlOS Node Launcher - Auto-generated
# Node ID: $NODE_ID

# Node Configuration
export NODE_ID="$NODE_ID"
export NODE_NAME="$NODE_ID"

# Network Ports
export PUB_PORT=5555
export SUB_PORT=5556
export DASHBOARD_PORT=3001

# Bootstrap Peers
export BOOTSTRAP_PEERS="$BOOTSTRAP_PEERS"

# Optional Features
export ENABLE_DOCKER=$ENABLE_DOCKER
export ENABLE_HARDWARE_RUNNER=$ENABLE_HARDWARE
export MQTT_BROKER_HOST="$MQTT_BROKER"

# Display startup info
echo "╔═══════════════════════════════════════╗"
echo "║     MarlOS Distributed Agent          ║"
echo "╚═══════════════════════════════════════╝"
echo ""
echo "🆔 Node ID:      \$NODE_ID"
echo "📛 Node Name:    \$NODE_NAME"
echo "📡 Bootstrap:    \$BOOTSTRAP_PEERS"
echo "🌐 Dashboard:    http://0.0.0.0:\$DASHBOARD_PORT"
echo "⚙️  PUB Port:     \$PUB_PORT"
echo "⚙️  SUB Port:     \$SUB_PORT"
echo "🐳 Docker:       \$ENABLE_DOCKER"
echo "🔧 Hardware:     \$ENABLE_HARDWARE_RUNNER"
echo ""
echo "Starting agent..."
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the agent
python -m agent.main

# Capture exit code
exit_code=\$?

if [ \$exit_code -ne 0 ]; then
    echo ""
    echo "❌ Agent exited with error code: \$exit_code"
    echo "Check logs at: data/\$NODE_ID/agent.log"
fi

exit \$exit_code
EOF

    chmod +x "$script_name"
    print_success "Launch script created: $script_name"

    # Also create Windows batch file
    local bat_script="start-${NODE_ID}.bat"
    cat > "$bat_script" << EOF
@echo off
REM MarlOS Node Launcher - Auto-generated
REM Node ID: $NODE_ID

set NODE_ID=$NODE_ID
set NODE_NAME=$NODE_ID
set PUB_PORT=5555
set SUB_PORT=5556
set DASHBOARD_PORT=3001
set BOOTSTRAP_PEERS=$BOOTSTRAP_PEERS
set ENABLE_DOCKER=$ENABLE_DOCKER
set ENABLE_HARDWARE_RUNNER=$ENABLE_HARDWARE
set MQTT_BROKER_HOST=$MQTT_BROKER

echo ╔═══════════════════════════════════════╗
echo ║     MarlOS Distributed Agent          ║
echo ╚═══════════════════════════════════════╝
echo.
echo 🆔 Node ID:      %NODE_ID%
echo 📛 Node Name:    %NODE_NAME%
echo 📡 Bootstrap:    %BOOTSTRAP_PEERS%
echo 🌐 Dashboard:    http://0.0.0.0:%DASHBOARD_PORT%
echo.

if exist venv\\Scripts\\activate.bat (
    call venv\\Scripts\\activate.bat
)

python -m agent.main

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Agent exited with error
    pause
)
EOF

    print_success "Windows launch script created: $bat_script"
}

create_systemd_service() {
    if [[ "$OS" != "linux" ]]; then
        return
    fi

    echo ""
    if ! ask_yes_no "Do you want to create a systemd service (auto-start on boot)?"; then
        return
    fi

    print_step "Creating systemd service..."

    local service_file="/etc/systemd/system/marlos-${NODE_ID}.service"

    sudo tee "$service_file" > /dev/null << EOF
[Unit]
Description=MarlOS Distributed Agent - $NODE_ID
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment="NODE_ID=$NODE_ID"
Environment="BOOTSTRAP_PEERS=$BOOTSTRAP_PEERS"
Environment="ENABLE_DOCKER=$ENABLE_DOCKER"
Environment="ENABLE_HARDWARE_RUNNER=$ENABLE_HARDWARE"
Environment="MQTT_BROKER_HOST=$MQTT_BROKER"
ExecStart=$INSTALL_DIR/venv/bin/python -m agent.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    print_success "Systemd service created: marlos-${NODE_ID}"

    if ask_yes_no "Enable service to start on boot?"; then
        sudo systemctl enable "marlos-${NODE_ID}"
        print_success "Service enabled"
    fi

    if ask_yes_no "Start service now?"; then
        sudo systemctl start "marlos-${NODE_ID}"
        print_success "Service started"
        echo ""
        print_info "Check status with: sudo systemctl status marlos-${NODE_ID}"
        print_info "View logs with: journalctl -u marlos-${NODE_ID} -f"
    fi
}

###############################################################################
# Main Installation Flow
###############################################################################

main() {
    print_banner

    print_info "This script will install and configure MarlOS on your system."
    echo ""

    if ! ask_yes_no "Do you want to continue?"; then
        print_warning "Installation cancelled."
        exit 0
    fi

    # Step 1: Detect OS
    print_step "Detecting operating system..."
    detect_os
    print_success "OS detected: $OS ($DISTRO)"

    # Step 2: Install system dependencies
    case $OS in
        linux)
            install_dependencies_linux
            ;;
        macos)
            install_dependencies_macos
            ;;
        windows)
            install_dependencies_windows
            ;;
        *)
            print_error "Unsupported operating system: $OS"
            exit 1
            ;;
    esac

    # Step 3: Clone repository
    clone_repository

    # Step 4: Setup Python environment
    setup_python_environment

    # Step 5: Choose deployment mode
    choose_deployment_mode

    # Step 6: Configure based on mode
    case $DEPLOYMENT_MODE in
        docker)
            configure_docker_deployment
            return
            ;;
        native)
            configure_native_deployment
            ;;
        dev)
            configure_dev_mode
            ;;
    esac

    # Step 7: Setup firewall
    setup_firewall

    # Step 8: Create launch scripts
    create_launch_script

    # Step 9: Optionally create systemd service
    create_systemd_service

    # Final summary
    echo ""
    echo -e "${GREEN}${BOLD}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                                                           ║"
    echo "║              🎉 Installation Complete! 🎉                ║"
    echo "║                                                           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""

    print_info "MarlOS has been successfully installed!"
    echo ""
    print_step "Quick Start:"
    echo ""
    echo "  1. Start your node:"
    echo "     ${CYAN}cd $INSTALL_DIR${NC}"
    echo "     ${CYAN}./start-${NODE_ID}.sh${NC}"
    echo ""
    echo "  2. Submit a test job:"
    echo "     ${CYAN}python cli/marlOS.py execute 'echo Hello MarlOS'${NC}"
    echo ""
    echo "  3. Check status:"
    echo "     ${CYAN}python cli/marlOS.py status${NC}"
    echo ""
    echo "  4. Access dashboard:"
    echo "     ${CYAN}http://$LOCAL_IP:3001${NC}"
    echo ""

    if [ -n "$BOOTSTRAP_PEERS" ]; then
        print_step "Network Information:"
        echo ""
        echo "  Your node will connect to:"
        echo "    $BOOTSTRAP_PEERS"
        echo ""
        echo "  Other nodes should add your node as:"
        echo "    ${CYAN}tcp://$LOCAL_IP:5555${NC}"
        echo ""
    fi

    print_step "Documentation:"
    echo ""
    echo "  - Quick Start:  $INSTALL_DIR/QUICKSTART.md"
    echo "  - Full Guide:   $INSTALL_DIR/docs/DISTRIBUTED_DEPLOYMENT.md"
    echo "  - Verification: $INSTALL_DIR/DEPLOYMENT_VERIFICATION.md"
    echo ""

    if ask_yes_no "Do you want to start MarlOS now?"; then
        print_info "Starting MarlOS..."
        echo ""
        cd "$INSTALL_DIR"
        ./start-${NODE_ID}.sh
    else
        print_info "You can start MarlOS later with:"
        echo "  cd $INSTALL_DIR && ./start-${NODE_ID}.sh"
    fi
}

# Run main installation
main
