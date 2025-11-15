# MarlOS Network Modes - User Guide

## Overview

MarlOS now supports **two network modes** for different use cases:

1. **PRIVATE MODE** - Connect your own devices manually
2. **PUBLIC MODE** - Join the global network automatically

---

## Quick Start

### Install MarlOS

```bash
pip install -e .
```

### Start a Node

```bash
marl
# Select option 1: Start MarlOS
# Select option 2: Native/Real Device
# Choose your network mode!
```

---

## PRIVATE MODE

**Best for:** Personal use, connecting your own devices across different networks

### Features
- ✅ Manual peer management
- ✅ Save favorite peers
- ✅ Auto-connect on startup
- ✅ Works across different networks (different WiFi, cellular, etc.)
- ✅ Full privacy and control
- ✅ No external dependencies

### Setup Guide

#### Step 1: Start First Node

```bash
marl
# Choose: Start MarlOS → Native/Real Device
# Network Mode: Select 1 (Private Mode)
# Node ID: my-laptop
# Bootstrap Peers: (leave empty for first node)
```

Your first node starts and shows:
```
✅ Agent my-laptop is ONLINE
   Network Mode: PRIVATE
   Saved Peers: 0
   P2P Address: tcp://192.168.1.100:5555
```

**Save this IP address!** You'll need it for other nodes.

#### Step 2: Start Second Node (Same Network)

On another computer on the same WiFi:

```bash
marl
# Choose: Start MarlOS → Native/Real Device
# Network Mode: Select 1 (Private Mode)
# Node ID: my-desktop
# Bootstrap Peers: 192.168.1.100
```

#### Step 3: Start Third Node (Different Network)

On a computer at a friend's house or office:

**Option A: Using Public IP (requires port forwarding)**

First, set up port forwarding on your first node's router:
- Forward port 5555 (TCP) to your laptop's local IP

Then:
```bash
marl
# Node ID: my-office-pc
# Bootstrap Peers: 203.45.67.89  # Your public IP
```

**Option B: Using Dynamic DNS (recommended)**

1. Set up free dynamic DNS:
   - Go to https://www.duckdns.org
   - Create a domain like: `my-marlos.duckdns.org`
   - Point it to your home IP

2. Start node:
```bash
marl
# Bootstrap Peers: my-marlos.duckdns.org
```

#### Managing Peers (Coming Soon)

```bash
marl peers list          # List all saved peers
marl peers add "Office PC" tcp://203.45.67.89:5555
marl peers remove tcp://203.45.67.89:5555
```

---

## PUBLIC MODE

**Best for:** Joining the global MarlOS network, automatic discovery

### Features
- ✅ Automatic peer discovery via DHT
- ✅ No manual configuration
- ✅ Connect to anyone worldwide
- ✅ Decentralized (no central server after initial bootstrap)
- ⚠️ Less private (anyone can discover you)

### Setup Guide

#### Quick Start

```bash
marl
# Choose: Start MarlOS → Native/Real Device
# Network Mode: Select 2 (Public Mode)
# Node ID: global-node-1
```

That's it! Your node will:
1. Connect to DHT bootstrap nodes
2. Announce itself to the network
3. Automatically discover and connect to other nodes

#### How It Works

```
Your Node
   ↓
Connects to DHT Bootstrap Nodes
   ↓
Announces itself with:
  - Node ID
  - IP Address
  - Port
  - Capabilities
   ↓
Discovers other nodes automatically
   ↓
Connects to discovered peers
```

### DHT Bootstrap Nodes

The system uses public bootstrap nodes to help nodes find each other.

**Default bootstrap nodes:**
```
dht1.marlos.network:5559
dht2.marlos.network:5559
dht3.marlos.network:5559
```

*Note: These need to be set up. For testing, you can run your own bootstrap node.*

---

## Running Your Own Bootstrap Node (Private Mode Alternative)

If you don't want to manually configure peers but also don't want to join the public network:

### Step 1: Set Up a Bootstrap Server

On a VPS or always-on computer:

```python
# Save as bootstrap.py
from agent.p2p.dht_manager import DHTManager
import asyncio

async def main():
    dht = DHTManager("bootstrap-1", port=5559, bootstrap_nodes=[])
    await dht.start("0.0.0.0", 5555, [])
    await asyncio.Event().wait()  # Run forever

asyncio.run(main())
```

```bash
python bootstrap.py
```

### Step 2: Configure Your Nodes

Set environment variable before starting:

```bash
export DHT_BOOTSTRAP_NODES="your-server.com:5559"
marl
# Select Public Mode
```

Now your nodes will form a private network using your bootstrap!

---

## Comparison

| Feature | Private Mode | Public Mode |
|---------|-------------|-------------|
| **Setup** | Manual peer IPs | Automatic |
| **Privacy** | High | Low |
| **Discovery** | Manual | Automatic |
| **Requires** | Peer IPs/domains | Internet |
| **Best For** | Personal devices | Global network |
| **NAT/Firewall** | Needs config | Works better |
| **Dependencies** | None | DHT bootstrap nodes |

---

## Troubleshooting

### Private Mode Issues

**Problem:** Can't connect to peer

**Solutions:**
1. Check firewall allows port 5555
2. Verify IP address is correct
3. If using public IP, ensure port forwarding is set up
4. Try using dynamic DNS instead of IP

**Problem:** Peer disconnects frequently

**Solutions:**
1. Use dynamic DNS if IP changes
2. Check network stability
3. Ensure both nodes are running

### Public Mode Issues

**Problem:** "Failed to join DHT network"

**Solutions:**
1. Check internet connection
2. Verify bootstrap nodes are reachable
3. Check firewall allows port 5559
4. Try running with: `pip install kademlia`

**Problem:** No peers discovered

**Solutions:**
1. Wait a few minutes for network propagation
2. Check that other public nodes are running
3. Verify bootstrap nodes are working

---

## Advanced Configuration

### Environment Variables

```bash
# Network Mode
export NETWORK_MODE="private"  # or "public"
export DHT_ENABLED="true"      # for public mode

# Ports
export PUB_PORT=5555           # P2P publisher port
export SUB_PORT=5556           # P2P subscriber port
export DHT_PORT=5559           # DHT port (public mode)

# Private Mode
export BOOTSTRAP_PEERS="tcp://192.168.1.100:5555,tcp://10.0.0.50:5555"

# Public Mode
export DHT_BOOTSTRAP_NODES="dht1.example.com:5559,dht2.example.com:5559"
```

### Config File (YAML)

```yaml
# config.yaml
network:
  mode: private  # or public
  pub_port: 5555
  dht_enabled: true
  dht_port: 5559
  bootstrap_peers:
    - "tcp://192.168.1.100:5555"
    - "tcp://my-pc.duckdns.org:5555"
  dht_bootstrap_nodes:
    - ["dht1.marlos.network", 5559]
    - ["dht2.marlos.network", 5559]
```

Then run:
```bash
python -m agent.main --config config.yaml
```

---

## Security Considerations

### Private Mode
- ✅ Only connects to peers you specify
- ✅ Full control over who joins
- ✅ Network traffic encrypted
- ⚠️ Manual key exchange recommended

### Public Mode
- ⚠️ Anyone can discover your node
- ⚠️ Potential for spam/malicious nodes
- ✅ Network traffic still encrypted
- ✅ Reputation system helps filter bad actors

---

## Next Steps

1. **Private Mode Users:**
   - Set up dynamic DNS for your main device
   - Add your devices to saved peers
   - Configure auto-connect

2. **Public Mode Users:**
   - Join the global network
   - Contribute compute power
   - Earn tokens by completing jobs

3. **Both:**
   - Monitor your node via dashboard
   - Check the reputation system
   - Explore job submission

---

## Getting Help

- Documentation: https://github.com/ayush-jadaun/MarlOS
- Issues: https://github.com/ayush-jadaun/MarlOS/issues
- Discord: (coming soon)

---

Happy computing with MarlOS! 🚀
