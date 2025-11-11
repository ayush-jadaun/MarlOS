# Share MarlOS with Your Team

## 📤 Quick Share Instructions

Send this to anyone who wants to join your MarlOS network:

---

### 🚀 Join Our MarlOS Network

**Step 1: Install MarlOS**

**Option A: pip install (Quickest)**
```bash
pip install git+https://github.com/ayush-jadaun/MarlOS.git
marl  # Start interactive setup
```

**Option B: Full installer**
```bash
curl -sSL https://raw.githubusercontent.com/ayush-jadaun/MarlOS/main/scripts/install-marlos.sh | bash
```

**Step 2: During Installation**

When asked for configuration, use these settings:

- **Deployment Mode:** Choose `2` (Real Device / Native)
- **Node ID:** Choose a unique name (e.g., `laptop-yourname`)
- **Network Type:** Choose `1` (Same WiFi/LAN)
- **Bootstrap Peers:** Enter: `YOUR_IP_HERE` *(replace with coordinator's IP)*

**Step 3: That's It!**

The installer handles everything else automatically. Your node will join the network!

---

## 📋 For Coordinators/Admins

### Share These Details with Your Team

```
🌐 MarlOS Network Configuration

Network Name: [Your Network Name]
Network Type: [LAN / WAN / Hybrid]

Coordinator Node:
  - IP Address: [YOUR_IP]
  - Bootstrap: tcp://[YOUR_IP]:5555

Installation Command:
  curl -sSL https://raw.githubusercontent.com/ayush-jadaun/MarlOS/main/scripts/install-marlos.sh | bash

Bootstrap Peers (use during installation):
  [YOUR_IP],192.168.1.101,192.168.1.102

Dashboard URLs:
  - Coordinator: http://[YOUR_IP]:3001
  - Agent 1: http://192.168.1.101:3001
  - Agent 2: http://192.168.1.102:3001

Test Command (after installation):
  python cli/marlOS.py execute "echo Hello MarlOS"

Need Help?
  - Documentation: https://github.com/ayush-jadaun/MarlOS
  - Issues: https://github.com/ayush-jadaun/MarlOS/issues
```

### Template for Email/Slack

```
Hi team!

We're setting up a MarlOS distributed computing network. Here's how to join:

1. Run this command on your laptop/device:
   curl -sSL https://raw.githubusercontent.com/ayush-jadaun/MarlOS/main/scripts/install-marlos.sh | bash

2. When prompted:
   - Choose option 2 (Real Device)
   - Enter your device name (e.g., laptop-yourname)
   - Choose option 1 (Same WiFi/LAN)
   - Enter bootstrap peers: [YOUR_IP_LIST]

3. Let it install (takes ~5 minutes)

4. Test with:
   python cli/marlOS.py execute "echo I'm connected!"

My coordinator IP: [YOUR_IP]
Dashboard: http://[YOUR_IP]:3001

Questions? Check: https://github.com/ayush-jadaun/MarlOS
```

---

## 🌍 For Remote Team Members

If team members are on different networks (not same WiFi):

### Requirements
- Port forwarding on coordinator's router
- Forward ports 5555, 5556, 3001 to coordinator's local IP

### Share These Details

```
🌐 MarlOS Remote Network Configuration

Coordinator Public IP: [YOUR_PUBLIC_IP]
Bootstrap Peers: tcp://[YOUR_PUBLIC_IP]:5555

Installation:
  curl -sSL https://raw.githubusercontent.com/ayush-jadaun/MarlOS/main/scripts/install-marlos.sh | bash

During Setup:
  - Deployment: Option 2 (Real Device)
  - Network: Option 2 (Different Networks / WAN)
  - Bootstrap Peers: tcp://[YOUR_PUBLIC_IP]:5555

Your router must forward these ports:
  - 5555 → Your Local IP
  - 5556 → Your Local IP
  - 3001 → Your Local IP (optional, for dashboard)

Find your public IP: curl ifconfig.me
```

---

## 🎓 For Workshop/Hackathon

### Quick Setup (Same Room)

**Organizer:**
1. Note your laptop's IP: `ip addr` or `ifconfig`
2. Share on screen/whiteboard

**Participants:**
1. Run installer: `curl -sSL https://raw.githubusercontent.com/ayush-jadaun/MarlOS/main/scripts/install-marlos.sh | bash`
2. Use organizer's IP as bootstrap peer
3. Start competing on the distributed network!

### Sample Workshop Announcement

```
📢 MarlOS Workshop - Distributed Computing Challenge

We'll be creating a real distributed computing network in this room!

Setup (5 minutes):
  1. Connect to WiFi: [WIFI_NAME]
  2. Run: curl -sSL https://raw.githubusercontent.com/ayush-jadaun/MarlOS/main/scripts/install-marlos.sh | bash
  3. Bootstrap peer: tcp://192.168.1.XXX:5555 (see projector)

Challenge:
  - Submit computing jobs
  - Watch RL-based auction in action
  - Most efficient node wins!

Dashboard: http://192.168.1.XXX:3001
```

---

## 🏢 For Enterprise/Lab Deployment

### Prerequisites Checklist

- [ ] All devices on same network or VPN
- [ ] Firewall rules configured (ports 5555, 5556, 3001)
- [ ] Python 3.11+ available
- [ ] Git installed
- [ ] Network administrator approval

### Batch Deployment

**Option 1: Ansible Playbook (Coming Soon)**

**Option 2: Manual Script Distribution**

Share `install-marlos.sh` and `deploy-config.env`:

```bash
# deploy-config.env
export NODE_ID="compute-$(hostname)"
export BOOTSTRAP_PEERS="tcp://server-main:5555,tcp://server-backup:5555"
export ENABLE_DOCKER=true
export DASHBOARD_PORT=3001

# Run on each node:
./install-marlos.sh
```

**Option 3: Container Orchestration**

Deploy via Kubernetes/Docker Swarm (see enterprise docs)

---

## 📱 Social Media Share

### Twitter/X

```
🚀 Just deployed MarlOS - a self-organizing distributed computing OS!

One command to join the network:
curl -sSL https://bit.ly/marlos-install | bash

✅ Zero configuration
✅ RL-based job scheduling
✅ Crypto-secured P2P
✅ Auto-discovery

Check it out: https://github.com/ayush-jadaun/MarlOS

#DistributedComputing #ReinforcementLearning #P2P
```

### LinkedIn

```
Excited to share MarlOS - an autonomous distributed computing operating system!

Unlike traditional systems that need complex configuration, MarlOS uses:
• Reinforcement learning for intelligent job distribution
• Peer-to-peer networking with zero central coordination
• Cryptographic security (Ed25519 signatures)
• Automatic peer discovery and fault tolerance

Installation is literally one command. Try it out!

https://github.com/ayush-jadaun/MarlOS
```

---

## 🤝 Collaboration Tips

### For GitHub Contributors

```markdown
## Contributing to MarlOS

Want to help develop MarlOS?

1. Install developer environment:
   ```bash
   curl -sSL https://raw.githubusercontent.com/ayush-jadaun/MarlOS/main/scripts/install-marlos.sh | bash
   # Choose option 3 (Development Mode)
   ```

2. Make changes and test locally

3. Submit PR with your improvements!

See CONTRIBUTING.md for guidelines.
```

### For Research Collaborators

```
📚 MarlOS Research Network

Testing distributed algorithms? Join our research network:

Setup:
  curl -sSL https://raw.githubusercontent.com/ayush-jadaun/MarlOS/main/scripts/install-marlos.sh | bash

Features for Research:
  - RL policy experimentation
  - Network topology simulation
  - Performance metrics collection
  - Byzantine fault injection
  - Economic mechanism testing

Research Dashboard: http://[COORDINATOR]:3001
Dataset Export: python cli/marlOS.py export-metrics

Paper: [arXiv link]
Cite: [BibTeX]
```

---

## 🆘 Support Your Team

### Common Questions

**Q: "The installer asks for sudo password. Is this safe?"**
A: Yes, it's only used to install system packages (Python, Git, etc.) and configure firewall. You can review the script first: https://github.com/ayush-jadaun/MarlOS/blob/main/install-marlos.sh

**Q: "Can I run this on Windows?"**
A: Yes! WSL2 is recommended, but native Windows works too. The installer detects your OS automatically.

**Q: "Do I need Docker?"**
A: No! Docker is optional. Shell jobs, security jobs, and hardware control work without Docker.

**Q: "What if my IP changes?"**
A: Use dynamic DNS (DuckDNS, No-IP) or re-run the installer to update bootstrap peers.

**Q: "How do I know it's working?"**
A: Run `python cli/marlOS.py status` - you should see connected peers.

---

## 📞 Contact Info to Share

```
MarlOS Support

📖 Documentation: https://github.com/ayush-jadaun/MarlOS
🐛 Report Issues: https://github.com/ayush-jadaun/MarlOS/issues
💬 Discussions: https://github.com/ayush-jadaun/MarlOS/discussions

Built by Team async_await
```

---

**Make distributed computing accessible to everyone!** 🚀
