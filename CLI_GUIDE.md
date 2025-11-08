# MarlOS CLI Guide

A command-line interface for interacting with the MarlOS distributed computing swarm.

## Quick Start

```bash
# Navigate to the project directory
cd MarlOS

# Use the CLI
python cli/marlOS.py [command] [options]
```

## Available Commands

### 1. Start Local Nodes

Start one or more MarlOS agent nodes locally:

```bash
python cli/marlOS.py start --nodes 3
```

**Options:**
- `--nodes, -n`: Number of nodes to start (default: 1)
- `--port, -p`: Base port number (default: 5555)
- `--config, -c`: Path to config file

**Example:**
```bash
# Start 3 nodes with custom base port
python cli/marlOS.py start -n 3 -p 6000
```

---

### 2. Submit Jobs

Submit a job to the swarm for execution:

```bash
python cli/marlOS.py submit job.json
```

**Options:**
- `--port, -p`: Dashboard WebSocket port (default: 8081 for agent-1)
- `--method, -m`: Submission method: `ws` (WebSocket) or `zmq` (default: ws)
- `--wait, -w`: Wait for job completion response

**Examples:**
```bash
# Submit to agent-1 (default)
python cli/marlOS.py submit test_job.json

# Submit to agent-2
python cli/marlOS.py submit test_job.json -p 8082

# Submit and wait for response
python cli/marlOS.py submit test_job.json -w
```

**Docker Port Mapping:**
- Agent 1: Port 8081
- Agent 2: Port 8082
- Agent 3: Port 8083

---

### 3. Check Status

View the current status of a node:

```bash
python cli/marlOS.py status
```

**Options:**
- `--port, -p`: Dashboard port (default: 8081)
- `--json-output, -j`: Output as JSON

**Examples:**
```bash
# Check agent-1 status
python cli/marlOS.py status

# Check agent-2 status
python cli/marlOS.py status -p 8082

# Get JSON output
python cli/marlOS.py status -j
```

**Output includes:**
- Node ID and name
- Trust score
- Quarantine status
- Wallet balance and earnings
- Network stats (peers, jobs completed/failed)

---

### 4. Real-Time Monitoring

Watch real-time updates from a node:

```bash
python cli/marlOS.py watch
```

**Options:**
- `--port, -p`: Dashboard port (default: 8081)
- `--interval, -i`: Update interval in seconds (default: 2)

**Examples:**
```bash
# Monitor agent-1 with default settings
python cli/marlOS.py watch

# Monitor agent-3 with 5-second updates
python cli/marlOS.py watch -p 8083 -i 5
```

**Press Ctrl+C to exit monitoring**

---

### 5. List Peers

Show connected peers for a node:

```bash
python cli/marlOS.py peers
```

**Options:**
- `--port, -p`: Dashboard port (default: 8081)

**Example:**
```bash
# List peers for agent-2
python cli/marlOS.py peers -p 8082
```

---

### 6. View Wallet

Display wallet information for a node:

```bash
python cli/marlOS.py wallet
```

**Options:**
- `--port, -p`: Dashboard port (default: 8081)

**Shows:**
- Balance
- Staked amount
- Total value
- Lifetime earnings/spending
- Net profit

---

### 7. Create Job Templates

Generate a job template file:

```bash
python cli/marlOS.py create --name shell --output my_job.json
```

**Options:**
- `--name, -n`: Job type (required)
- `--command, -c`: Command to execute (for shell jobs)
- `--payment, -p`: Payment amount in AC (default: 100.0)
- `--priority`: Job priority 0-1 (default: 0.5)
- `--output, -o`: Output file path (default: job.json)

**Job Types:**
- `shell`: Execute shell commands
- `docker`: Run Docker containers
- `malware_scan`: Security scanning
- `port_scan`: Network scanning
- Custom: Any custom job type

**Examples:**
```bash
# Create a shell job
python cli/marlOS.py create -n shell -c "ls -la" -o list_files.json

# Create a Docker job with custom payment
python cli/marlOS.py create -n docker -p 200 -o docker_job.json

# Create and submit
python cli/marlOS.py create -n shell -c "hostname" -o host.json
python cli/marlOS.py submit host.json
```

---

### 8. Version Info

Display version information:

```bash
python cli/marlOS.py version
```

---

## Working with Docker Containers

If you're running agents in Docker (via `docker-compose`):

### Port Mappings

```yaml
Agent 1: localhost:8081 → container:3001
Agent 2: localhost:8082 → container:3001
Agent 3: localhost:8083 → container:3001
```

### Examples

```bash
# Submit job to agent-1 (in Docker)
python cli/marlOS.py submit job.json -p 8081

# Check status of agent-2 (in Docker)
python cli/marlOS.py status -p 8082

# Watch agent-3 (in Docker)
python cli/marlOS.py watch -p 8083
```

---

## Job File Format

Example `job.json`:

```json
{
  "job_type": "shell",
  "priority": 0.7,
  "payment": 150.0,
  "payload": {
    "command": "python --version"
  },
  "requirements": ["python"],
  "verify": false,
  "verifiers": 1
}
```

**Required Fields:**
- `job_type`: Type of job to execute
- `payload`: Job-specific data

**Optional Fields:**
- `job_id`: Auto-generated if not provided
- `priority`: 0.0 to 1.0 (default: 0.5)
- `payment`: Amount in AC (default: 100.0)
- `deadline`: Unix timestamp (default: +5 minutes)
- `requirements`: List of required capabilities
- `verify`: Enable verification (default: false)
- `verifiers`: Number of verifiers needed (default: 1)

---

## Common Workflows

### 1. Submit and Monitor a Job

```bash
# Create job
python cli/marlOS.py create -n shell -c "echo 'Hello MarlOS'" -o hello.json

# Submit job
python cli/marlOS.py submit hello.json

# Watch execution in real-time
python cli/marlOS.py watch
```

### 2. Check Swarm Health

```bash
# Check each agent
python cli/marlOS.py status -p 8081
python cli/marlOS.py status -p 8082
python cli/marlOS.py status -p 8083

# List peers
python cli/marlOS.py peers
```

### 3. Monitor Earnings

```bash
# Check wallet before
python cli/marlOS.py wallet

# Submit high-value job
python cli/marlOS.py create -n docker -p 500 -o valuable.json
python cli/marlOS.py submit valuable.json

# Check wallet after
python cli/marlOS.py wallet
```

---

## Troubleshooting

### Connection Refused

**Problem:** `Could not connect to node. Is it running?`

**Solutions:**
1. Check if Docker containers are running: `docker ps`
2. Verify correct port: Use 8081-8083 for Docker agents
3. Start containers: `docker-compose up -d`

### WebSocket Timeout

**Problem:** WebSocket connection times out

**Solutions:**
1. Increase timeout in CLI
2. Check firewall settings
3. Verify agent dashboard is running

### Job Not Executing

**Problem:** Job submitted but not executing

**Solutions:**
1. Check job requirements match agent capabilities
2. Verify sufficient payment amount
3. Check agent trust score (not quarantined)
4. Use `watch` to see if job was received

---

## Tips

1. **Default Port**: CLI defaults to 8081 (agent-1 in Docker)
2. **Multiple Agents**: Use `-p` flag to target different agents
3. **Real-time Updates**: Use `watch` for live monitoring
4. **JSON Output**: Add `-j` flag for machine-readable output
5. **Job Templates**: Use `create` command to generate valid job files

---

## Help

Get help for any command:

```bash
python cli/marlOS.py --help
python cli/marlOS.py submit --help
python cli/marlOS.py create --help
```
