# MarlOS Quick Start Guide

## 5-Minute Setup for Real Devices

### Step 1: Find Device IPs

**Linux/Mac:**
```bash
ip addr show | grep "inet "
# or
ifconfig | grep "inet "
```

**Windows:**
```cmd
ipconfig
```

Example output:
- Device 1: `192.168.1.100`
- Device 2: `192.168.1.101`
- Device 3: `192.168.1.102`

---

### Step 2: Install MarlOS on Each Device

```bash
git clone <your-repo-url>
cd MarlOS
pip install -r requirements.txt
```

---

### Step 3: Edit Launch Script

**On Device 1 (192.168.1.100):**
```bash
# Edit start-node.sh (Linux/Mac) or start-node.bat (Windows)
export NODE_ID="laptop-1"
export BOOTSTRAP_PEERS="tcp://192.168.1.101:5555,tcp://192.168.1.102:5555"
```

**On Device 2 (192.168.1.101):**
```bash
export NODE_ID="laptop-2"
export BOOTSTRAP_PEERS="tcp://192.168.1.100:5555,tcp://192.168.1.102:5555"
```

**On Device 3 (192.168.1.102):**
```bash
export NODE_ID="desktop-1"
export BOOTSTRAP_PEERS="tcp://192.168.1.100:5555,tcp://192.168.1.101:5555"
```

---

### Step 4: Open Firewall Ports

**Linux (ufw):**
```bash
sudo ufw allow 5555/tcp
sudo ufw allow 5556/tcp
sudo ufw allow 3001/tcp
```

**Windows (PowerShell as Admin):**
```powershell
New-NetFirewallRule -DisplayName "MarlOS" -Direction Inbound -Protocol TCP -LocalPort 5555,5556,3001 -Action Allow
```

**Mac:**
```bash
# Allow in System Preferences → Security → Firewall
```

---

### Step 5: Launch on Each Device

**Linux/Mac:**
```bash
chmod +x start-node.sh
./start-node.sh
```

**Windows:**
```cmd
start-node.bat
```

---

### Step 6: Verify Connection

**Check logs for peer discovery:**
```
[P2P] Connected to peer: tcp://192.168.1.101:5555
[P2P] Received PEER_ANNOUNCE from laptop-2
✓ 2 peers connected
```

**Access dashboard:**
```
http://192.168.1.100:3001  (Device 1)
http://192.168.1.101:3001  (Device 2)
http://192.168.1.102:3001  (Device 3)
```

---

### Step 7: Submit Test Job

```bash
# From any device:
python cli/marlOS.py execute "echo 'Hello distributed world!'"

# Or try other commands:
python cli/marlOS.py execute "uname -a"
python cli/marlOS.py execute "python --version"
```

You should see:
- Job submitted via WebSocket
- Auction happens across all nodes
- A node wins the bid (check dashboard/logs)
- Job executes and result is stored

**View results:**
- Dashboard: `http://192.168.1.100:3001` (replace with your IP)
- Logs: `tail -f data/agent.log`

---

## Troubleshooting

### Can't connect to peers?
```bash
# Test connectivity:
ping 192.168.1.101
nc -zv 192.168.1.101 5555

# Check if agent is running:
ps aux | grep agent.main

# Check firewall:
sudo ufw status
```

### Nodes can't discover each other?
```bash
# Verify BOOTSTRAP_PEERS is correct:
echo $BOOTSTRAP_PEERS

# Check logs:
tail -f data/agent.log | grep PEER_ANNOUNCE
```

### Port already in use?
```bash
# Find what's using the port:
lsof -i :5555

# Change port in script:
export PUB_PORT=5565
export SUB_PORT=5566
```

---

## Next Steps

- **Full Guide:** [docs/DISTRIBUTED_DEPLOYMENT.md](docs/DISTRIBUTED_DEPLOYMENT.md)
- **Architecture:** [docs/NETWORK_DESIGN.md](docs/NETWORK_DESIGN.md)
- **Dashboard:** Open `http://<device-ip>:3001` in browser
- **Submit Jobs:** Use CLI tool `python cli/marlOS.py execute "command"`

### CLI Commands Reference

```bash
# Execute shell commands
python cli/marlOS.py execute "your-command"

# Check swarm status
python cli/marlOS.py status

# Watch real-time monitoring
python cli/marlOS.py watch

# Check wallet balance
python cli/marlOS.py wallet

# List connected peers
python cli/marlOS.py peers

# Create job templates
python cli/marlOS.py create --name shell --command "echo test"

# Submit job from file
python cli/marlOS.py submit job.json
```

---

## Common Configurations

### Same WiFi Network
```bash
BOOTSTRAP_PEERS="tcp://192.168.1.101:5555,tcp://192.168.1.102:5555"
```

### Public Internet
```bash
BOOTSTRAP_PEERS="tcp://203.0.113.45:5555,tcp://198.51.100.89:5555"
# Requires port forwarding on routers
```

### Cloud + Local (NAT)
```bash
# Cloud server (public IP: 203.0.113.45)
BOOTSTRAP_PEERS=""  # Acts as bootstrap point

# Local devices (all connect to cloud)
BOOTSTRAP_PEERS="tcp://203.0.113.45:5555"
```

---

**That's it! Your distributed compute OS is running!**
