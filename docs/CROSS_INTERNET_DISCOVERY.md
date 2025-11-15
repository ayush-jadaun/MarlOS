# Cross-Internet Peer Discovery for MarlOS

## Current State

**MarlOS currently uses manual bootstrap configuration** - you need to know the IP address of at least one peer to join the network. This works for:
- ✅ Same LAN (local network)
- ✅ Same WiFi network
- ⚠️ Different networks (requires manual IP configuration)

## The Problem: NAT and Firewalls

When computers are on different internet connections:

```
Computer A (Home WiFi)          Computer B (Office Network)
├─ Private IP: 192.168.1.100   ├─ Private IP: 10.0.0.50
├─ Public IP: 203.0.113.1      ├─ Public IP: 198.51.100.1
└─ Behind NAT Router            └─ Behind NAT + Firewall
```

**Problem:** Computer A can't directly connect to `192.168.1.100` because:
1. Private IPs only work on local network
2. NAT routers block incoming connections
3. Firewalls filter traffic

## Solutions for Cross-Internet Discovery

### Option 1: Bootstrap Server (Recommended)

A **bootstrap server** acts as a meeting point for peers.

**How it works:**
```
1. All peers connect to bootstrap server on startup
2. Bootstrap server maintains a registry of active peers
3. Peers exchange addresses through the bootstrap
4. Peers connect directly to each other (P2P)
```

**Setup:**

1. **Deploy a Bootstrap Server** (on a VPS with public IP):
   ```python
   # bootstrap_server.py
   import asyncio
   import json
   from datetime import datetime

   peers = {}  # node_id -> {ip, port, last_seen}

   async def handle_peer(reader, writer):
       data = await reader.read(4096)
       request = json.loads(data.decode())

       addr = writer.get_extra_info('peername')

       if request['type'] == 'register':
           # Register peer
           node_id = request['node_id']
           peers[node_id] = {
               'ip': addr[0],
               'port': request['port'],
               'last_seen': datetime.now()
           }

           # Return current peer list
           response = {'peers': list(peers.values())}
           writer.write(json.dumps(response).encode())
           await writer.drain()

       writer.close()

   async def main():
       server = await asyncio.start_server(
           handle_peer, '0.0.0.0', 5558
       )
       async with server:
           await server.serve_forever()

   asyncio.run(main())
   ```

2. **Configure MarlOS to use bootstrap server:**
   ```bash
   # Add to requirements.txt already has bootstrap support
   # Just need to set environment variable:
   export BOOTSTRAP_SERVER="tcp://your-vps-ip:5558"
   ```

3. **Update agent config** to use bootstrap:
   ```python
   # In agent/config.py
   bootstrap_servers: List[str] = [
       "tcp://your-vps-ip:5558"
   ]
   ```

**Pros:**
- ✅ Easy to implement
- ✅ Works behind NAT
- ✅ Reliable peer discovery

**Cons:**
- ❌ Requires a server with public IP (costs ~$5/month)
- ❌ Single point of failure (can have multiple bootstrap servers)

---

### Option 2: NAT Traversal (Hole Punching)

Use STUN/TURN servers to establish direct connections through NAT.

**Technologies:**
- **STUN** (Session Traversal Utilities for NAT): Discovers public IP
- **TURN** (Traversal Using Relays around NAT): Relays traffic when direct connection fails
- **ICE** (Interactive Connectivity Establishment): Combines STUN/TURN

**Setup:**

1. **Add NAT traversal dependencies:**
   ```bash
   pip install aiortc aioice
   ```

2. **Use public STUN servers:**
   ```python
   STUN_SERVERS = [
       "stun.l.google.com:19302",
       "stun1.l.google.com:19302",
       "stun2.l.google.com:19302"
   ]
   ```

3. **Implement hole punching** (complex, requires significant changes)

**Pros:**
- ✅ Direct P2P connections
- ✅ No central server needed
- ✅ Free STUN servers available

**Cons:**
- ❌ Complex implementation
- ❌ May not work with symmetric NAT
- ❌ Requires TURN server for relay (fallback)

---

### Option 3: Port Forwarding (Manual)

Forward ports on your router to allow incoming connections.

**Setup:**

1. **Find your router's admin panel** (usually `192.168.1.1`)

2. **Forward these ports to your computer:**
   - Port 5555 (TCP) - P2P Publisher
   - Port 5556 (TCP) - P2P Subscriber
   - Port 3001 (TCP) - Dashboard

3. **Share your public IP:**
   ```bash
   curl ifconfig.me  # Get your public IP
   ```

4. **Other peers connect using:**
   ```bash
   export BOOTSTRAP_PEERS="tcp://your-public-ip:5555"
   marl
   ```

**Pros:**
- ✅ Simple concept
- ✅ Direct connections
- ✅ No extra software needed

**Cons:**
- ❌ Security risk (opens ports to internet)
- ❌ Manual configuration per user
- ❌ Dynamic IPs change
- ❌ Some ISPs block port forwarding

---

### Option 4: VPN or Mesh Network

Use a VPN to create a virtual local network.

**Tools:**
- **ZeroTier** (easiest): Creates virtual LAN, free for <50 devices
- **Tailscale**: WireGuard-based, very secure
- **Nebula**: Self-hosted mesh VPN

**Setup with ZeroTier:**

1. **Create network at** https://my.zerotier.com
2. **Install ZeroTier on all computers:**
   ```bash
   # Windows
   Download from https://www.zerotier.com/download/

   # Linux
   curl -s https://install.zerotier.com | sudo bash
   ```

3. **Join network:**
   ```bash
   sudo zerotier-cli join YOUR_NETWORK_ID
   ```

4. **Use ZeroTier IPs for bootstrap:**
   ```bash
   # Each computer gets a virtual IP like 10.147.18.x
   export BOOTSTRAP_PEERS="tcp://10.147.18.1:5555"
   marl
   ```

**Pros:**
- ✅ Most secure
- ✅ Works like a LAN
- ✅ Easy to use
- ✅ No port forwarding needed

**Cons:**
- ❌ All users need VPN software
- ❌ Slight latency overhead
- ❌ Limited to VPN network size

---

## Recommended Setup

### For Testing/Development (2-5 peers):
**Use ZeroTier VPN**
- Easiest setup
- No server costs
- Works reliably

### For Production (5-100 peers):
**Use Bootstrap Server + NAT Traversal**
- Deploy 2-3 bootstrap servers for redundancy
- Implement STUN for direct connections
- Use TURN as fallback

### For Large Scale (100+ peers):
**Use DHT (Distributed Hash Table)**
- Like BitTorrent's peer discovery
- Fully decentralized
- Complex to implement

---

## Quick Implementation: Add Bootstrap Server Support

I can help you implement bootstrap server support. Here's what needs to be done:

1. **Create a simple bootstrap server** (Python script)
2. **Update MarlOS to register with bootstrap on startup**
3. **Fetch peer list from bootstrap**
4. **Deploy bootstrap to a VPS** (DigitalOcean, AWS, etc.)

Would you like me to implement this? It would enable cross-internet discovery without complex NAT traversal.

---

## Summary Table

| Method | Complexity | Cost | Security | NAT Support |
|--------|-----------|------|----------|-------------|
| Bootstrap Server | ⭐⭐ Easy | $5/mo | ⭐⭐⭐ Good | ✅ Yes |
| NAT Traversal | ⭐⭐⭐⭐⭐ Hard | Free | ⭐⭐⭐ Good | ✅ Yes |
| Port Forwarding | ⭐ Very Easy | Free | ⭐ Poor | ⚠️ Manual |
| VPN (ZeroTier) | ⭐ Very Easy | Free | ⭐⭐⭐⭐⭐ Excellent | ✅ Yes |
| DHT | ⭐⭐⭐⭐ Hard | Free | ⭐⭐⭐ Good | ⚠️ Complex |

**My Recommendation:** Start with **ZeroTier** for immediate results, then add **Bootstrap Server** for production deployment.
