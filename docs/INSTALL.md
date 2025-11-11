# MarlOS Installation Guide

## Interactive Installation Script

MarlOS provides an interactive installation script that automatically sets up everything you need. This is the **recommended** way to install MarlOS.

---

## One-Line Installation

### Linux / macOS / WSL

```bash
curl -sSL https://raw.githubusercontent.com/ayush-jadaun/MarlOS/main/scripts/install-marlos.sh | bash
```

### Or Download and Run

```bash
wget https://raw.githubusercontent.com/ayush-jadaun/MarlOS/main/scripts/install-marlos.sh
chmod +x install-marlos.sh
./install-marlos.sh
```

---

## What the Installer Does

The interactive script will:

1. **🔍 Detect Your System**
   - Identifies your OS (Linux, macOS, Windows)
   - Detects distribution (Ubuntu, Fedora, Arch, etc.)
   - Checks for existing installations

2. **📦 Install Dependencies**
   - Python 3.11+
   - Git
   - ZeroMQ library
   - System build tools
   - Network utilities (nmap, nettools)

3. **📥 Clone Repository**
   - Clones from GitHub
   - Or updates existing installation

4. **🐍 Setup Python Environment**
   - Creates virtual environment
   - Installs all Python packages
   - Sets up CLI tools

5. **⚙️ Interactive Configuration**
   - Asks about deployment mode
   - Configures network topology
   - Sets up node identity
   - Configures firewall rules

6. **🚀 Generate Launch Scripts**
   - Creates start-node.sh (Linux/Mac)
   - Creates start-node.bat (Windows)
   - Optionally creates systemd service

7. **▶️ Start Your Node**
   - Optionally starts immediately
   - Provides all necessary commands

---

## Installation Flow Examples

### Example 1: Docker Development Setup

```
? Do you want to continue? (y/n): y

Detecting OS...
✓ OS detected: linux (ubuntu)

Installing dependencies...
✓ System dependencies installed

Cloning repository...
✓ Repository cloned to /home/user/MarlOS

Setting up Python environment...
✓ Virtual environment created
✓ Python dependencies installed

Choose Deployment Mode:
  1) Docker Containers (for local testing)
  2) Real Device / Native (for distributed computing)
  3) Development Mode (single node)

Enter your choice (1-3): 1

✓ Docker mode selected
✓ Docker detected

? Do you want to start MarlOS with Docker Compose now? (y/n): y

Starting MarlOS with Docker Compose...
✓ MarlOS is now running in Docker!

Access points:
  - Agent 1 Dashboard: http://localhost:8081
  - Agent 2 Dashboard: http://localhost:8082
  - Agent 3 Dashboard: http://localhost:8083
```

---

### Example 2: Real Device on LAN

```
? Do you want to continue? (y/n): y

Detecting OS...
✓ OS detected: linux (ubuntu)

Installing dependencies...
✓ System dependencies installed

Cloning repository...
✓ Repository cloned to /home/user/MarlOS

Setting up Python environment...
✓ Virtual environment created
✓ Python dependencies installed

Choose Deployment Mode:
  1) Docker Containers
  2) Real Device / Native
  3) Development Mode

Enter your choice (1-3): 2

✓ Native/Real Device mode selected

? Enter a unique Node ID for this device (e.g., laptop-1, server-a):
Node ID: laptop-ayush

✓ Node ID: laptop-ayush
ℹ Detected local IP: 192.168.1.100

Network Configuration:
  1) Same WiFi/LAN
  2) Different Networks (Internet/WAN)
  3) Hybrid (some local, some remote)
  4) Single node (no peers yet)

Enter your choice (1-4): 1

ℹ Configuring for same LAN/WiFi network

ℹ Other devices should use these IPs in their BOOTSTRAP_PEERS:
  tcp://192.168.1.100:5555

? Enter the IP addresses of other MarlOS nodes (comma-separated)
Example: 192.168.1.100,192.168.1.101
Peer IPs: 192.168.1.101,192.168.1.102

✓ Bootstrap peers: tcp://192.168.1.101:5555,tcp://192.168.1.102:5555

? Enable Docker job execution? (y/n): n
ℹ Docker execution disabled. Shell and security jobs will still work.

? Enable hardware control (Arduino/ESP32 via MQTT)? (y/n): n

Setting up firewall rules...
? Do you want to configure firewall rules automatically? (y/n): y

ℹ Configuring UFW firewall...
✓ Firewall rules added

Creating launch script...
✓ Launch script created: start-laptop-ayush.sh
✓ Windows launch script created: start-laptop-ayush.bat

? Do you want to create a systemd service (auto-start on boot)? (y/n): y

Creating systemd service...
✓ Systemd service created: marlos-laptop-ayush

? Enable service to start on boot? (y/n): y
✓ Service enabled

? Start service now? (y/n): y
✓ Service started

ℹ Check status with: sudo systemctl status marlos-laptop-ayush
ℹ View logs with: journalctl -u marlos-laptop-ayush -f

╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║              🎉 Installation Complete! 🎉                ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

ℹ MarlOS has been successfully installed!

Quick Start:
  1. Start your node:
     cd /home/user/MarlOS
     ./start-laptop-ayush.sh

  2. Submit a test job:
     python cli/marlOS.py execute 'echo Hello MarlOS'

  3. Check status:
     python cli/marlOS.py status

  4. Access dashboard:
     http://192.168.1.100:3001

Network Information:
  Your node will connect to:
    tcp://192.168.1.101:5555,tcp://192.168.1.102:5555

  Other nodes should add your node as:
    tcp://192.168.1.100:5555
```

---

### Example 3: Internet/WAN Deployment

```
Network Configuration:
  1) Same WiFi/LAN
  2) Different Networks (Internet/WAN)
  3) Hybrid
  4) Single node

Enter your choice (1-4): 2

ℹ Configuring for Internet/WAN deployment

⚠ Important: You need to set up port forwarding on your router!
ℹ Forward these ports to 192.168.1.100:
  - Port 5555 (TCP) - MarlOS Publisher
  - Port 5556 (TCP) - MarlOS Subscriber
  - Port 3001 (TCP) - Dashboard (optional)

? Enter your public IP or domain name:
Public IP/Domain: 203.0.113.45

ℹ Share this with other nodes:
  tcp://203.0.113.45:5555

? Enter bootstrap peer addresses (comma-separated)
Example: tcp://203.0.113.45:5555,tcp://198.51.100.89:5555
Bootstrap Peers: tcp://198.51.100.89:5555,tcp://203.0.114.22:5555

✓ Bootstrap peers configured
```

---

## What Gets Created

After installation, you'll have:

### Directory Structure
```
~/MarlOS/
├── agent/                  # Core agent code
├── cli/                    # CLI tools
├── docs/                   # Documentation
├── data/                   # Runtime data (logs, keys, etc.)
├── venv/                   # Python virtual environment
├── start-<node-id>.sh      # Your launch script (Linux/Mac)
├── start-<node-id>.bat     # Your launch script (Windows)
├── install-marlos.sh       # Installer script
└── requirements.txt        # Python dependencies
```

### Launch Script

**Linux/Mac: `start-<node-id>.sh`**
```bash
#!/bin/bash
# Node Configuration
export NODE_ID="laptop-ayush"
export BOOTSTRAP_PEERS="tcp://192.168.1.101:5555"
export ENABLE_DOCKER=false
export DASHBOARD_PORT=3001

# Activate venv and run
source venv/bin/activate
python -m agent.main
```

**Windows: `start-<node-id>.bat`**
```batch
@echo off
set NODE_ID=laptop-ayush
set BOOTSTRAP_PEERS=tcp://192.168.1.101:5555
set ENABLE_DOCKER=false
set DASHBOARD_PORT=3001

call venv\Scripts\activate.bat
python -m agent.main
```

### Systemd Service (Linux Only)

**`/etc/systemd/system/marlos-<node-id>.service`**
```ini
[Unit]
Description=MarlOS Distributed Agent - laptop-ayush
After=network.target

[Service]
Type=simple
User=ayush
WorkingDirectory=/home/ayush/MarlOS
Environment="NODE_ID=laptop-ayush"
Environment="BOOTSTRAP_PEERS=tcp://192.168.1.101:5555"
ExecStart=/home/ayush/MarlOS/venv/bin/python -m agent.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Manage with:**
```bash
sudo systemctl start marlos-laptop-ayush
sudo systemctl stop marlos-laptop-ayush
sudo systemctl status marlos-laptop-ayush
journalctl -u marlos-laptop-ayush -f
```

---

## Manual Installation (Advanced)

If you prefer manual installation or the script doesn't work:

### 1. Install Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git curl build-essential libzmq3-dev nmap
```

**Fedora/RHEL:**
```bash
sudo dnf install -y python3 python3-pip git curl gcc zeromq-devel nmap
```

**macOS:**
```bash
brew install python3 git zeromq nmap
```

### 2. Clone Repository

```bash
git clone https://github.com/ayush-jadaun/MarlOS.git
cd MarlOS
```

### 3. Setup Python Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configure Node

Edit `start-node.sh` or create your own:
```bash
export NODE_ID="my-node"
export BOOTSTRAP_PEERS="tcp://192.168.1.101:5555"
export ENABLE_DOCKER=false
python -m agent.main
```

### 5. Setup Firewall

**Linux (UFW):**
```bash
sudo ufw allow 5555/tcp
sudo ufw allow 5556/tcp
sudo ufw allow 3001/tcp
```

**Windows:**
```powershell
New-NetFirewallRule -DisplayName "MarlOS" -Direction Inbound -Protocol TCP -LocalPort 5555,5556,3001 -Action Allow
```

---

## Troubleshooting

### "Command not found: curl"

Install curl first:
```bash
# Ubuntu/Debian
sudo apt-get install curl

# Fedora
sudo dnf install curl

# macOS
brew install curl
```

### "Permission denied" when running script

Make script executable:
```bash
chmod +x install-marlos.sh
./install-marlos.sh
```

### Python version too old

MarlOS requires Python 3.11+. Update Python:
```bash
# Ubuntu (using deadsnakes PPA)
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv

# Or download from python.org
```

### Firewall rules fail

If automatic firewall configuration fails, add rules manually:
```bash
# Check current firewall
sudo ufw status    # or: sudo firewall-cmd --list-all

# Add rules manually
sudo ufw allow 5555/tcp
sudo ufw allow 5556/tcp
sudo ufw allow 3001/tcp
```

### Cannot connect to peers

1. Check firewall is open: `nc -zv <peer-ip> 5555`
2. Verify peer is running: `curl http://<peer-ip>:3001` (may fail but shows connectivity)
3. Check BOOTSTRAP_PEERS format: Must be `tcp://IP:5555`
4. Wait 10 seconds for gossip discovery
5. Check logs: `tail -f data/agent.log`

---

## After Installation

### Start Your Node

```bash
cd ~/MarlOS
./start-<your-node-id>.sh
```

### Submit Test Job

```bash
python cli/marlOS.py execute "echo Hello MarlOS"
```

### Check Status

```bash
python cli/marlOS.py status
python cli/marlOS.py peers
python cli/marlOS.py wallet
```

### Access Dashboard

Open browser: `http://localhost:3001`

---

## Uninstallation

### Stop Service (if installed)

```bash
sudo systemctl stop marlos-<node-id>
sudo systemctl disable marlos-<node-id>
sudo rm /etc/systemd/system/marlos-<node-id>.service
sudo systemctl daemon-reload
```

### Remove Files

```bash
rm -rf ~/MarlOS
```

### Remove Firewall Rules

```bash
sudo ufw delete allow 5555/tcp
sudo ufw delete allow 5556/tcp
sudo ufw delete allow 3001/tcp
```

---

## Next Steps

- **Submit Jobs:** [CLI documentation](QUICKSTART.md#cli-commands-reference)
- **Configure Advanced Settings:** [Full deployment guide](docs/DISTRIBUTED_DEPLOYMENT.md)
- **Understand Architecture:** [Network design](docs/NETWORK_DESIGN.md)
- **Test Your Setup:** Run `./test_deployment.sh`

---

## Getting Help

- **Documentation:** Check `docs/` folder
- **Issues:** https://github.com/ayush-jadaun/MarlOS/issues
- **Logs:** `tail -f data/agent.log`
- **Status:** `python cli/marlOS.py status`

---

**Built by Team async_await at Hack36** 🚀
