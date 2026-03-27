# MarlOS CLI Reference Guide

Complete reference for the `marl` command-line interface (v1.0.5).

MarlOS provides two layers of CLI interaction: **direct commands** you run from your terminal, and an **interactive menu** that launches when you run `marl` with no arguments.

---

## Table of Contents

- [Getting Started](#getting-started)
- [marl (no command) / marl interactive](#marl-interactive)
- [marl start](#marl-start)
- [marl demo](#marl-demo)
- [marl execute](#marl-execute)
- [marl submit](#marl-submit)
- [marl status](#marl-status)
- [marl peers](#marl-peers)
- [marl wallet](#marl-wallet)
- [marl watch](#marl-watch)
- [marl create](#marl-create)
- [marl install](#marl-install)
- [marl version](#marl-version)
- [marl nodes](#marl-nodes)
  - [marl nodes list](#marl-nodes-list)
  - [marl nodes show](#marl-nodes-show)
  - [marl nodes edit](#marl-nodes-edit)
  - [marl nodes delete](#marl-nodes-delete)
- [Common Workflows](#common-workflows)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

---

## Getting Started

After installing MarlOS (`pip install marlos` or `pip install -e .` from the repo), the `marl` command becomes available globally.

```bash
# Verify installation
marl version

# Show all available commands
marl --help

# Launch the interactive menu
marl
```

Most commands that talk to a running node (execute, status, peers, wallet, watch, submit) communicate over WebSocket to the agent's dashboard port (default `3001`). The agent must be running first.

---

## marl interactive

Launches a full-screen interactive menu with numbered options. This is also what happens when you run `marl` with no subcommand.

**Usage:**

```bash
marl
marl interactive
```

**Menu options:**

| # | Action | Description |
|---|--------|-------------|
| 1 | Start MarlOS | Choose a start mode (Docker, Native, Dev, Service) |
| 2 | Quick Execute | Submit a shell command to the swarm |
| 3 | Check Status | View node info, wallet, and network stats |
| 4 | List Peers | Show connected and trusted peers |
| 5 | View Wallet | Display AC balance and transaction summary |
| 6 | Live Monitor | Real-time dashboard in the terminal |
| 7 | Create Job | Build a job template JSON file interactively |
| 8 | Submit Job | Send a job file to a running node |
| 9 | Configuration | Manage YAML config, peers, launch scripts, network mode |
| 10 | Documentation | List available docs and links |
| 0 | Exit | Quit the menu |

The interactive menu checks whether the agent is running before attempting network operations and will offer to start it for you if it is not.

---

## marl start

Start MarlOS agent nodes. When called from the CLI directly, it opens an interactive mode selector.

**Usage:**

```bash
marl start
```

**Start modes presented interactively:**

| Mode | Description |
|------|-------------|
| Docker Compose | Launches 3 agent nodes in Docker containers. Requires Docker. Dashboard ports: 8081, 8082, 8083. |
| Native/Real Device | Runs a single node on the local machine. Creates a launch script and node config under `~/.marlos/`. Prompts for network mode (Private or Public) and bootstrap peers. |
| Development | Starts a dev node with `NODE_ID=dev-node`, `LOG_LEVEL=DEBUG`, and Docker disabled. |
| Background Service | Linux only. Manages systemd services (`marlos-*.service`): start, stop, restart, status, logs. |

**marlOS.py start command (lower-level):**

The companion module `marlOS.py` also exposes a `start` command with explicit flags, useful for scripting:

```bash
# Start 1 node on the default port
python -m cli.marlOS start

# Start 3 nodes, base port 6000
python -m cli.marlOS start --nodes 3 --port 6000

# Start with a custom config file
python -m cli.marlOS start --config /path/to/config.yaml
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--nodes` | `-n` | `1` | Number of agent nodes to start |
| `--port` | `-p` | `5555` | Base port number. Each subsequent node offsets by 10 (pub) and 11 (sub). |
| `--config` | `-c` | None | Path to a YAML config file. Must exist. |

When starting multiple nodes, each gets sequential ports and dashboard ports (`3001`, `3002`, ...). Press `Ctrl+C` to stop all nodes.

---

## marl demo

Run an end-to-end demo of the MarlOS network. Starts a local cluster, submits jobs, and shows the full lifecycle.

**Usage:**

```bash
marl demo
marl demo --nodes 5 --jobs 3
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--nodes` | `-n` | `3` | Number of demo nodes to spin up |
| `--jobs` | `-j` | `2` | Number of demo jobs to submit |

**Example:**

```bash
# Run the default demo (3 nodes, 2 jobs)
marl demo

# Larger demo
marl demo -n 5 -j 10
```

The demo script lives at `scripts/demo.py` and exits with a status code you can use in CI.

---

## marl execute

Submit a shell command for execution on the swarm. This is the fastest way to run something.

**Usage:**

```bash
marl execute "<command>"
marl execute "echo Hello World"
marl execute "ls -la /tmp" --payment 50 --priority 0.8 --wait
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `command` | The shell command string to execute (required) |

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--port` | `-p` | `3001` | Dashboard WebSocket port of the target node |
| `--payment` | | `10.0` | Payment offered in AC (MarlCredits) |
| `--priority` | | `0.5` | Job priority from 0.0 (lowest) to 1.0 (highest) |
| `--wait` | `-w` | off | Wait for a response from the node before returning |

**How it works:**

1. The CLI builds a shell job with a unique `job_id`, a 5-minute deadline, and a 60-second execution timeout.
2. It connects to the agent's WebSocket dashboard and submits the job.
3. If `--wait` is set, it blocks up to 2 seconds for a response.

**Examples:**

```bash
# Basic execution
marl execute "echo hello"

# Higher payment to attract bidders, wait for result
marl execute "python3 train.py" --payment 100 --priority 1.0 --wait

# Target a specific node on a non-default port
marl execute "uptime" --port 8081
```

---

## marl submit

Submit a job defined in a JSON file to the swarm.

**Usage:**

```bash
marl submit <file> [options]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `file` | Path to a JSON job file (must exist) |

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--port` | `-p` | `3001` | Dashboard WebSocket port |
| `--wait` | `-w` | off | Wait for a response after submission |

The `marlOS.py` module also supports `--method` (`ws` or `zmq`, default `ws`). The main CLI always uses WebSocket.

**Job file format:**

A job JSON file must contain at least `job_type` and `payload`. Optional fields (`job_id`, `priority`, `payment`, `deadline`) are auto-filled if missing.

```json
{
  "job_type": "shell",
  "priority": 0.7,
  "payment": 50.0,
  "payload": {
    "command": "echo Hello MarlOS"
  }
}
```

**Examples:**

```bash
# Submit a job file
marl submit job.json

# Submit and wait for acknowledgement
marl submit my_task.json --wait

# Submit to a node on port 8082
marl submit job.json --port 8082
```

---

## marl status

Query the current status of a running MarlOS node. Displays node identity, wallet balance, network stats, and capabilities.

**Usage:**

```bash
marl status
marl status --port 8081
marl status --json-output
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--port` | `-p` | `3001` | Dashboard WebSocket port to query |
| `--json-output` | `-j` | off | Output raw JSON instead of formatted tables |

**Displayed information:**

- **Node Information** -- Node ID, node name, trust score, quarantine status
- **Wallet** -- Balance, staked amount, total value, lifetime earned, net profit
- **Network** -- Connected peers, active jobs, jobs completed, jobs failed
- **Capabilities** -- List of supported job types

**Examples:**

```bash
# Check default node
marl status

# Get machine-readable output for scripting
marl status -j

# Check a Docker node
marl status --port 8082
```

---

## marl peers

List connected peers and their trust statistics.

**Usage:**

```bash
marl peers
marl peers --port 8081
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--port` | `-p` | `3001` | Dashboard WebSocket port |

**Displayed information:**

- Total peer count
- Number of trusted peers
- Number of quarantined peers

**Example:**

```bash
marl peers
# Output:
#   Total Peers: 4
#   Trusted Peers: 3
#   Quarantined Peers: 1
```

---

## marl wallet

Show wallet balance and transaction history for a running node.

**Usage:**

```bash
marl wallet
marl wallet --port 8081
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--port` | `-p` | `3001` | Dashboard WebSocket port |

**Displayed fields:**

| Field | Description |
|-------|-------------|
| Balance | Available AC (MarlCredits) |
| Staked | AC locked in staking |
| Total Value | Balance + Staked |
| Lifetime Earned | Total AC ever received |
| Lifetime Spent | Total AC ever spent |
| Net Profit | Lifetime Earned - Lifetime Spent |

**Example:**

```bash
marl wallet
# Output:
#   Balance:         142.50 AC
#   Staked:           10.00 AC
#   Total Value:     152.50 AC
#   Lifetime Earned: 250.00 AC
#   Lifetime Spent:  107.50 AC
#   Net Profit:      142.50 AC
```

---

## marl watch

Real-time monitoring dashboard in the terminal. Polls the node at a configurable interval and renders a live-updating Rich layout.

**Usage:**

```bash
marl watch
marl watch --port 8081 --interval 5
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--port` | `-p` | `3001` | Dashboard WebSocket port |
| `--interval` | `-i` | `2` | Polling interval in seconds |

**Dashboard panels:**

- **Header** -- Node name
- **Status** -- Trust score, balance, staked AC, peer count, active/completed/failed jobs
- **Footer** -- "Press Ctrl+C to exit"

Press `Ctrl+C` to stop monitoring.

**Example:**

```bash
# Default: poll every 2 seconds
marl watch

# Slower updates, different port
marl watch -p 8082 -i 10
```

---

## marl create

Generate a job template JSON file. Supports built-in templates for common job types.

**Usage:**

```bash
marl create --name <type> [options]
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--name` | `-n` | (required) | Job type: `shell`, `docker`, `malware_scan`, `port_scan`, or any custom name |
| `--command` | `-c` | None | Shell command (used when `--name shell`) |
| `--payment` | `-p` | `100.0` | Payment amount in AC |
| `--priority` | | `0.5` | Job priority (0.0 to 1.0) |
| `--output` | `-o` | `job.json` | Output file path |

**Built-in templates:**

| Type | Payload |
|------|---------|
| `shell` | `{ "command": "<your command>" }` |
| `docker` | `{ "image": "alpine:latest", "command": ["echo", "Hello from Docker"] }` |
| `malware_scan` | `{ "file_url": "...", "file_hash": "..." }` |
| `port_scan` | `{ "target": "192.168.1.1", "ports": "1-1000" }` |

If `--name` does not match a built-in template, an empty payload is generated.

**Examples:**

```bash
# Create a shell job template
marl create --name shell --command "python3 train.py" --payment 200 --output train.json

# Create a port scan template
marl create -n port_scan -o scan.json

# Create a Docker job template with custom priority
marl create --name docker --priority 0.9

# Then submit the template
marl submit train.json
```

---

## marl install

Run the installation wizard. Checks whether MarlOS is pip-installed or running from source, sets up a virtual environment if needed, and installs Python dependencies.

**Usage:**

```bash
marl install
```

**What it does (depending on install state):**

- **Pip-installed:** Confirms installation is good, shows available commands, optionally guides you to clone source for development.
- **Running from source:** Looks for or creates a `venv/` directory, installs dependencies from `requirements.txt`.

---

## marl version

Print the MarlOS version.

**Usage:**

```bash
marl version
marl --version
```

**Output:**

```
MarlOS v1.0.5
Autonomous Distributed Computing Operating System
Built by Team async_await
```

---

## marl nodes

A command group for managing node configurations stored under `~/.marlos/nodes/`. Each node gets its own directory with a `config.yaml` file.

### marl nodes list

List all configured nodes.

**Usage:**

```bash
marl nodes list
```

**Output columns:** Node ID, Name, Network Mode, Created date.

**Example:**

```bash
marl nodes list
# Output:
#   Node ID          Name              Mode      Created
#   node-abc123      My Laptop         PRIVATE   2026-03-15
#   node-def456      Office Server     PUBLIC    2026-03-20
```

---

### marl nodes show

Display the full YAML configuration for a specific node.

**Usage:**

```bash
marl nodes show <node_id>
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `node_id` | The ID of the node to inspect |

**Example:**

```bash
marl nodes show node-abc123
# Prints the config.yaml with syntax highlighting and line numbers
```

---

### marl nodes edit

Open a node's configuration file in your default editor.

**Usage:**

```bash
marl nodes edit <node_id>
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `node_id` | The ID of the node to edit |

Uses the `$EDITOR` environment variable (falls back to `notepad` on Windows, `nano` on Linux/macOS).

**Example:**

```bash
marl nodes edit node-abc123
# Opens ~/.marlos/nodes/node-abc123/config.yaml in your editor
```

---

### marl nodes delete

Delete a node and all its configuration data.

**Usage:**

```bash
marl nodes delete <node_id>
marl nodes delete <node_id> --force
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `node_id` | The ID of the node to delete |

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--force` | `-f` | off | Skip the confirmation prompt |

**Example:**

```bash
# With confirmation prompt
marl nodes delete node-abc123

# Skip confirmation
marl nodes delete node-abc123 --force
```

---

## Common Workflows

### First-time setup

```bash
# Install
pip install marlos

# Verify
marl version

# Run the installation wizard (optional, for source installs)
marl install

# Start your first node interactively
marl start
```

### Single-node development

```bash
# Start a dev node (from the repo root)
NODE_ID=dev-node python -m agent.main

# In another terminal, run commands
marl execute "echo hello"
marl status
marl watch
```

### Multi-node Docker testing

```bash
# Start the Docker cluster
docker-compose up -d

# Check each node
marl status --port 8081
marl status --port 8082
marl status --port 8083

# Submit a job to node 1
marl execute "echo distributed" --port 8081 --payment 50

# Watch node 2
marl watch --port 8082
```

### Create and submit a custom job

```bash
# Generate a template
marl create --name shell --command "python3 my_script.py" --payment 200 --output my_job.json

# Edit the file if needed
# Then submit
marl submit my_job.json --wait
```

### Run the demo

```bash
marl demo --nodes 5 --jobs 4
```

---

## Environment Variables

These environment variables override YAML and default config values:

| Variable | Default | Description |
|----------|---------|-------------|
| `NODE_ID` | auto-generated | Unique identifier for the node |
| `PUB_PORT` | `5555` | ZeroMQ PUB socket port |
| `SUB_PORT` | `5556` | ZeroMQ SUB socket port |
| `DASHBOARD_PORT` | `3001` | WebSocket dashboard port |
| `NETWORK_MODE` | `private` | `private` (manual peers) or `public` (DHT discovery) |
| `BOOTSTRAP_PEERS` | empty | Comma-separated peer addresses (e.g., `tcp://192.168.1.100:5555`) |
| `DHT_ENABLED` | `false` | Enable DHT-based peer discovery |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `ENABLE_DOCKER` | `true` | Enable Docker-based job execution |

---

## Troubleshooting

**"No MarlOS agent running on port 3001"**

The node is not started or is on a different port. Start it with `marl start` or `python -m agent.main`, then retry.

**"WebSocket error: ..."**

The agent's dashboard WebSocket server is not reachable. Confirm the correct `--port` and that the agent started without errors.

**"MarlOS Installation Error -- Cannot find MarlOS agent code"**

Reinstall MarlOS:
```bash
pip uninstall -y marlos
pip install --no-cache-dir marlos
```

Or install from source:
```bash
git clone https://github.com/ayush-jadaun/MarlOS.git
cd MarlOS
pip install -e .
```

**Commands hang or time out**

WebSocket connections have a 5-second open timeout. If the agent is under heavy load or the port is wrong, commands will time out. Verify the agent process is healthy with `marl status --port <port>`.
