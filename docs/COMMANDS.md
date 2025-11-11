# MarlOS Command Reference

Quick reference for the `marl` CLI command.

## Installation

```bash
# Install from GitHub
pip install git+https://github.com/ayush-jadaun/MarlOS.git

# Or from PyPI (when published)
pip install marlos
```

---

## Interactive Mode

Launch the beautiful interactive menu:

```bash
marl
```

This opens the main menu with all options.

---

## Direct Commands

### Core Commands

```bash
# Show help
marl --help

# Show version
marl version

# Run installation wizard
marl install

# Start MarlOS (interactive mode selection)
marl start

# Launch interactive menu explicitly
marl interactive
```

### Job Execution

```bash
# Quick execute a shell command
marl execute "echo Hello MarlOS"
marl execute "python --version"
marl execute "ls -la" --port 3001

# With custom options
marl execute "long-running-job" --payment 50 --priority 0.8

# Create job template
marl create --name shell --command "echo test" --output job.json
marl create --name port_scan --payment 100 --output scan.json

# Submit job from file
marl submit job.json
marl submit job.json --port 3001 --wait
```

### Monitoring & Status

```bash
# Check swarm status
marl status
marl status --port 3001
marl status --json  # JSON output

# List connected peers
marl peers
marl peers --port 3001

# View wallet balance
marl wallet
marl wallet --port 3001

# Real-time monitoring
marl watch
marl watch --port 3001 --interval 1
```

---

## Command Options

### Global Options

```
--help     Show help message
--version  Show version information
```

### `marl execute` Options

```
command             Command to execute (required)
--port, -p PORT     Dashboard port (default: 3001)
--payment AMOUNT    Payment in AC tokens (default: 10.0)
--priority FLOAT    Job priority 0-1 (default: 0.5)
--wait, -w          Wait for job completion
```

**Examples:**
```bash
marl execute "echo test"
marl execute "curl https://api.github.com" --port 3002
marl execute "python script.py" --payment 50 --wait
```

### `marl create` Options

```
--name, -n NAME       Job type name (required)
--command, -c CMD     Command for shell jobs
--payment, -p AMOUNT  Payment in AC (default: 100.0)
--priority FLOAT      Priority 0-1 (default: 0.5)
--output, -o FILE     Output file path (default: job.json)
```

**Examples:**
```bash
marl create --name shell --command "echo test"
marl create --name malware_scan --payment 150 --output scan.json
marl create --name port_scan --priority 0.9
```

### `marl submit` Options

```
job_file            Path to job JSON file (required)
--port, -p PORT     Dashboard port (default: 3001)
--wait, -w          Wait for job completion
```

**Examples:**
```bash
marl submit job.json
marl submit my-task.json --port 3002
marl submit critical-job.json --wait
```

### `marl status` Options

```
--port, -p PORT       Dashboard port (default: 3001)
--json-output, -j     Output as JSON
```

**Examples:**
```bash
marl status
marl status --port 3002
marl status --json > status.json
```

### `marl peers` Options

```
--port, -p PORT     Dashboard port (default: 3001)
```

**Examples:**
```bash
marl peers
marl peers --port 3002
```

### `marl wallet` Options

```
--port, -p PORT     Dashboard port (default: 3001)
```

**Examples:**
```bash
marl wallet
marl wallet --port 3002
```

### `marl watch` Options

```
--port, -p PORT         Dashboard port (default: 3001)
--interval, -i SECONDS  Update interval (default: 2)
```

**Examples:**
```bash
marl watch
marl watch --port 3002 --interval 1
```

---

## Interactive Menu Options

When you run `marl` without arguments, you get the interactive menu:

```
1.  🚀 Start MarlOS (choose mode)
    ├─ Docker Compose (multiple test nodes)
    ├─ Native/Real Device (distributed deployment)
    ├─ Development (debug mode)
    └─ Background Service (systemd)

2.  ⚡ Quick Execute (run a command)
    └─ Interactive prompt for command

3.  📊 Check Status
    └─ Display swarm status

4.  👥 List Peers
    └─ Show connected nodes

5.  💰 View Wallet
    └─ Display token balance

6.  📺 Live Monitor
    └─ Real-time dashboard

7.  📝 Create Job
    └─ Interactive job template creator

8.  📤 Submit Job
    └─ Submit job from file

9.  ⚙️  Configuration
    ├─ Edit launch script
    ├─ View current config
    └─ Re-run installer

10. 📖 Documentation
    └─ View docs and links

0.  ❌ Exit
```

---

## Environment Variables

```bash
# Set default dashboard port
export MARLOS_PORT=3001

# Node configuration
export NODE_ID="my-node"
export BOOTSTRAP_PEERS="tcp://192.168.1.100:5555"

# Feature flags
export ENABLE_DOCKER=true
export ENABLE_HARDWARE_RUNNER=false
export MQTT_BROKER_HOST="localhost"

# Logging
export LOG_LEVEL=DEBUG
```

---

## Configuration Files

MarlOS looks for configuration in these locations (in order):

1. `./agent-config.yml` (current directory)
2. `~/.marlos/config.yml` (user config)
3. `/etc/marlos/config.yml` (system config)

**Example config:**

```yaml
node:
  id: production-node-1
  name: Main Compute Node

network:
  pub_port: 5555
  sub_port: 5556
  bootstrap_peers:
    - tcp://192.168.1.100:5555
    - tcp://192.168.1.101:5555

executor:
  max_concurrent_jobs: 5
  docker_enabled: true
  sandbox_enabled: true

dashboard:
  port: 3001
  host: 0.0.0.0

token:
  starting_balance: 100.0
  stake_requirement: 10.0
```

---

## Common Workflows

### Setup New Node

```bash
# 1. Install
pip install git+https://github.com/ayush-jadaun/MarlOS.git

# 2. Configure
marl start
# Choose: Native Mode
# Enter: Node ID and bootstrap peers

# 3. Verify
marl status
marl peers
```

### Submit and Monitor Job

```bash
# 1. Execute
marl execute "python train_model.py" --payment 100

# 2. Monitor
marl watch

# 3. Check result
marl status
marl wallet  # Check earnings/spending
```

### Create Custom Job

```bash
# 1. Create template
marl create --name shell --command "my-script.sh" --output custom.json

# 2. Edit job file
nano custom.json

# 3. Submit
marl submit custom.json --wait
```

### Monitor Network

```bash
# Terminal 1: Live monitoring
marl watch

# Terminal 2: Check peers every 10 seconds
watch -n 10 "marl peers"

# Terminal 3: Execute jobs
marl execute "periodic-task"
```

---

## Keyboard Shortcuts (Interactive Menu)

- `1-10` - Select menu option
- `0` - Exit/Back
- `Ctrl+C` - Cancel current operation
- `Enter` - Confirm selection
- `↑↓` - Navigate (in some prompts)

---

## Tips & Tricks

### 1. Shell Aliases

Add to `~/.bashrc` or `~/.zshrc`:

```bash
alias ms='marl status'
alias mp='marl peers'
alias mw='marl wallet'
alias mx='marl execute'
alias mm='marl watch'
```

Usage:
```bash
ms              # Check status
mp              # List peers
mx "echo test"  # Execute command
mm              # Watch live
```

### 2. Default Port

Set once, use everywhere:
```bash
export MARLOS_PORT=3002
marl status      # Uses 3002
marl execute ""  # Uses 3002
```

### 3. Quick Scripts

Create wrapper scripts:

**`~/bin/marlos-job`:**
```bash
#!/bin/bash
marl execute "$1" --payment "${2:-10}" --wait
```

Usage:
```bash
marlos-job "python script.py" 50  # Payment 50 AC
```

### 4. JSON Output for Scripts

```bash
# Get status as JSON
marl status --json | jq '.peers'

# Parse wallet balance
marl wallet --json | jq '.balance'
```

### 5. Background Monitoring

```bash
# Log status every minute
watch -n 60 "marl status >> marlos-status.log"

# Alert on peer changes
watch -n 10 'marl peers | grep -q "3 peers" || notify-send "Peer count changed"'
```

---

## Troubleshooting Commands

```bash
# Check installation
marl version
which marl
pip show marlos

# Test connection
marl status --port 3001

# List all running MarlOS processes
ps aux | grep "agent.main"

# View logs (if systemd service)
journalctl -u marlos-* -f

# Reinstall
pip uninstall marlos
pip install --upgrade --force-reinstall git+https://github.com/ayush-jadaun/MarlOS.git
```

---

## Exit Codes

```
0   - Success
1   - General error
2   - Command not found
3   - Connection error
4   - Configuration error
130 - Interrupted (Ctrl+C)
```

---

## Getting Help

```bash
# General help
marl --help

# Command-specific help
marl execute --help
marl create --help
marl submit --help

# Interactive menu
marl
# Select option 10 (Documentation)
```

**Online Resources:**
- Documentation: https://github.com/ayush-jadaun/MarlOS
- Issues: https://github.com/ayush-jadaun/MarlOS/issues
- Discussions: https://github.com/ayush-jadaun/MarlOS/discussions

---

**Quick tip:** Just type `marl` and explore the interactive menu - it's the easiest way to get started! 🚀
