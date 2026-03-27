# Lab Setup Guide — MarlOS on a LAN

Set up MarlOS across 5+ machines on the same network (WiFi, Ethernet, lab).

## Prerequisites

- 2+ machines on the same network (laptops, desktops, Raspberry Pi, VMs)
- Python 3.11+ on each machine
- Machines can reach each other on TCP ports 5555-5560 and 3001

## Step 1: Install on Every Machine

On **each machine**:

```bash
git clone https://github.com/ayush-jadaun/MarlOS.git
cd MarlOS
pip install -r requirements.txt
```

## Step 2: Find IP Addresses

On each machine, find its LAN IP:

```bash
# Linux/macOS
ip addr show | grep "inet " | grep -v 127.0.0.1

# Windows
ipconfig | findstr "IPv4"
```

Example results:
- Machine A: `192.168.1.100`
- Machine B: `192.168.1.101`
- Machine C: `192.168.1.102`
- Machine D: `192.168.1.103`
- Machine E: `192.168.1.104`

## Step 3: Start the First Node (Bootstrap)

On **Machine A** (the first node — others will connect to it):

```bash
NODE_ID=node-alpha python -m agent.main
```

Note the output line:
```
P2P Address: tcp://192.168.1.100:5555
```

This is the address other nodes will bootstrap from.

## Step 4: Start Remaining Nodes

On **Machine B**:
```bash
NODE_ID=node-beta BOOTSTRAP_PEERS="tcp://192.168.1.100:5555" python -m agent.main
```

On **Machine C**:
```bash
NODE_ID=node-gamma BOOTSTRAP_PEERS="tcp://192.168.1.100:5555,tcp://192.168.1.101:5555" python -m agent.main
```

On **Machine D**:
```bash
NODE_ID=node-delta BOOTSTRAP_PEERS="tcp://192.168.1.100:5555" python -m agent.main
```

On **Machine E**:
```bash
NODE_ID=node-epsilon BOOTSTRAP_PEERS="tcp://192.168.1.100:5555" python -m agent.main
```

Each node only needs **one** bootstrap peer to discover the full network (gossip protocol propagates peer info).

## Step 5: Verify Discovery

After ~5 seconds, each node should print:
```
👋 Peer discovered: node-beta (caps: [shell, docker, ...])
👋 Peer discovered: node-gamma (caps: [shell, docker, ...])
```

Check from any node:
```bash
# REST API (from any machine)
curl http://192.168.1.100:3101/api/peers

# CLI (on the machine running that node)
marl peers
```

Expected: each node sees all other nodes.

## Step 6: Submit a Job

From **any machine**:

```bash
# Via CLI
marl execute "echo hello from the mesh"

# Via REST API
curl -X POST http://192.168.1.100:3101/api/jobs \
  -H "Content-Type: application/json" \
  -d '{"job_type": "shell", "payload": {"command": "hostname && echo job done"}, "payment": 50}'
```

Watch the logs on all machines — you'll see:
1. All nodes receive the job broadcast
2. RL decides to BID, FORWARD, or DEFER
3. Auction determines winner
4. Winner stakes tokens, executes, gets paid
5. Trust scores update

## Step 7: View the Dashboard

Open a browser to any node's dashboard:
```
http://192.168.1.100:3001
```

The D3.js network graph shows all connected nodes, trust scores, and data flow.

## Step 8: Stress Test

Submit many jobs and watch the network distribute them:

```bash
# From any machine
for i in $(seq 1 20); do
  curl -s -X POST http://192.168.1.100:3101/api/jobs \
    -H "Content-Type: application/json" \
    -d "{\"job_type\": \"shell\", \"payload\": {\"command\": \"echo job $i\"}, \"payment\": 30}" &
done
wait
echo "All jobs submitted"
```

Then check distribution:
```bash
curl http://192.168.1.100:3101/api/status
curl http://192.168.1.101:3101/api/status
curl http://192.168.1.102:3101/api/status
```

## Firewall Notes

If nodes can't discover each other, check firewalls:

```bash
# Linux — allow MarlOS ports
sudo ufw allow 5555:5560/tcp
sudo ufw allow 3001/tcp
sudo ufw allow 3101/tcp

# Windows — run as admin
netsh advfirewall firewall add rule name="MarlOS P2P" dir=in action=allow protocol=TCP localport=5555-5560
netsh advfirewall firewall add rule name="MarlOS Dashboard" dir=in action=allow protocol=TCP localport=3001
netsh advfirewall firewall add rule name="MarlOS API" dir=in action=allow protocol=TCP localport=3101
```

## Custom Ports

If default ports conflict, use env vars:

```bash
NODE_ID=node-1 PUB_PORT=6000 SUB_PORT=6001 DASHBOARD_PORT=4001 \
  BOOTSTRAP_PEERS="tcp://192.168.1.100:5555" python -m agent.main
```

REST API always runs on `DASHBOARD_PORT + 100`.

## Adding a Custom Runner to the Lab

Want all machines to support a new job type? On each machine:

1. Create `plugins/my_runner.py`:
```python
from agent.plugins import runner

@runner.register("my_task")
async def my_runner(job):
    result = do_something(job["payload"])
    return {"status": "success", "result": result}
```

2. Restart the node. The plugin auto-loads.

## Troubleshooting

| Problem | Fix |
|---|---|
| "No peers discovered" | Check firewall, verify IPs, ensure BOOTSTRAP_PEERS is correct |
| "Connection refused" | Target node not running, or port mismatch |
| "Job not executed" | Check `marl status` — node might be quarantined or out of tokens |
| Port conflict | Use `PUB_PORT`, `SUB_PORT`, `DASHBOARD_PORT` env vars |
| Slow discovery | Increase `discovery_interval` or add more bootstrap peers |
