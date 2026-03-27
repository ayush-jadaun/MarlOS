# MarlOS API Guide

Complete reference for interacting with MarlOS nodes via the REST API, MCP server (for AI agents), and the JavaScript SDK.

**Base URL:** `http://localhost:3101` (default: dashboard port + 100)

---

## Table of Contents

- [REST API](#rest-api)
  - [Health and Status](#health-and-status)
  - [Jobs](#jobs)
  - [Pipelines (DAG)](#pipelines-dag)
  - [Job Groups (Batch)](#job-groups-batch)
  - [Network and Peers](#network-and-peers)
  - [Economy](#economy)
  - [RL Stats](#rl-stats)
- [MCP Server (for Claude / AI Agents)](#mcp-server-for-claude--ai-agents)
  - [Configuration](#mcp-configuration)
  - [Available Tools](#mcp-available-tools)
  - [Example: Claude Security Scan](#example-claude-submitting-a-security-scan)
- [JavaScript SDK](#javascript-sdk)
  - [Installation](#installation)
  - [Quick Start](#quick-start)
  - [Jobs](#sdk-jobs)
  - [submitAndWait Pattern](#submitandwait-pattern)
  - [Pipelines](#sdk-pipelines)
  - [Job Groups](#sdk-job-groups)
  - [Network and Economy](#sdk-network-and-economy)
  - [Error Handling](#error-handling)

---

## REST API

All endpoints return JSON. CORS is enabled for all origins. The API supports `GET`, `POST`, and `OPTIONS` methods.

### Health and Status

#### `GET /api/health`

Simple health check. Use this to verify the node is running.

```bash
curl http://localhost:3101/api/health
```

**Response (200):**
```json
{
  "status": "ok",
  "node_id": "dev-node"
}
```

#### `GET /api/status`

Full node state including wallet, trust, capabilities, and job counts.

```bash
curl http://localhost:3101/api/status
```

**Response (200):**
```json
{
  "node_id": "dev-node",
  "node_name": "MarlOS-dev",
  "peers": 3,
  "trust_score": 0.850,
  "quarantined": false,
  "wallet": {
    "balance": 1000.0,
    "staked": 200.0
  },
  "jobs_completed": 42,
  "jobs_failed": 2,
  "capabilities": ["shell", "docker", "port_scan"]
}
```

---

### Jobs

#### `POST /api/jobs`

Submit a job to the MarlOS network. The job is broadcast to all peers for auction; the best-suited node wins and executes it.

**Supported job types:** `shell`, `docker`, `port_scan`, `malware_scan`, `hash_crack`, `threat_intel`

```bash
curl -X POST http://localhost:3101/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "shell",
    "payload": {
      "command": "echo hello world"
    },
    "payment": 100.0,
    "priority": 0.5
  }'
```

**Request body:**

| Field          | Type   | Required | Default              | Description                                     |
|----------------|--------|----------|----------------------|-------------------------------------------------|
| `job_type`     | string | Yes      | --                   | `shell`, `docker`, `port_scan`, `malware_scan`, `hash_crack`, `threat_intel` |
| `payload`      | object | Yes      | --                   | Job-specific data (see payload examples below)   |
| `payment`      | number | No       | `100.0`              | Payment in AC tokens                            |
| `priority`     | number | No       | `0.5`                | Priority 0.0 (low) to 1.0 (high)               |
| `job_id`       | string | No       | auto-generated       | Custom job ID                                   |
| `deadline`     | number | No       | now + 300s           | Unix timestamp deadline                         |
| `verify`       | bool   | No       | `false`              | Enable result verification                      |
| `verifiers`    | number | No       | `1`                  | Number of verifier nodes                        |
| `requirements` | object | No       | `null`               | Node capability requirements                    |

**Payload examples by job type:**

```json
// shell
{ "command": "ls -la /tmp" }

// docker
{ "image": "python:3.11", "command": "python -c 'print(42)'" }

// port_scan
{ "target": "192.168.1.0/24" }

// malware_scan
{ "target": "/path/to/scan" }

// hash_crack
{ "hash": "5f4dcc3b5aa765d61d8327deb882cf99", "algorithm": "md5" }

// threat_intel
{ "indicator": "suspicious-domain.com", "type": "domain" }
```

**Response (201):**
```json
{
  "job_id": "job-a1b2c3d4",
  "status": "submitted",
  "message": "Job broadcast to network for auction"
}
```

**Error responses:**

- `400` -- Missing `job_type` or `payload`, or invalid JSON
- `500` -- Internal error during broadcast

#### `GET /api/jobs`

List all known jobs (completed, executing, and auctioning).

```bash
curl http://localhost:3101/api/jobs
```

**Response (200):**
```json
{
  "jobs": [
    { "job_id": "job-a1b2c3d4", "status": "success" },
    { "job_id": "job-e5f6g7h8", "status": "executing" }
  ],
  "total": 2
}
```

#### `GET /api/jobs/{job_id}`

Get the status and result of a specific job.

```bash
curl http://localhost:3101/api/jobs/job-a1b2c3d4
```

**Response (200) -- Completed job:**
```json
{
  "job_id": "job-a1b2c3d4",
  "status": "success",
  "result": {
    "stdout": "hello world\n",
    "exit_code": 0
  },
  "duration": 0.342,
  "error": null
}
```

**Response (200) -- In-progress job:**
```json
{
  "job_id": "job-a1b2c3d4",
  "status": "executing"
}
```

**Response (200) -- Auctioning job:**
```json
{
  "job_id": "job-a1b2c3d4",
  "status": "auctioning"
}
```

**Response (404):**
```json
{
  "error": "Job not found"
}
```

---

### Pipelines (DAG)

Pipelines let you define multi-step workflows as a directed acyclic graph. Each step can depend on the completion of other steps before it runs.

#### `POST /api/pipelines`

Submit a pipeline of jobs with dependency ordering.

```bash
curl -X POST http://localhost:3101/api/pipelines \
  -H "Content-Type: application/json" \
  -d '{
    "name": "security-audit",
    "steps": [
      {
        "id": "scan-ports",
        "job_type": "port_scan",
        "payload": { "target": "192.168.1.100" },
        "payment": 50.0
      },
      {
        "id": "scan-malware",
        "job_type": "malware_scan",
        "payload": { "target": "/opt/app" },
        "payment": 75.0
      },
      {
        "id": "report",
        "job_type": "shell",
        "payload": { "command": "echo Audit complete" },
        "depends_on": ["scan-ports", "scan-malware"],
        "payment": 25.0
      }
    ]
  }'
```

**Step fields:**

| Field        | Type     | Required | Default  | Description                        |
|--------------|----------|----------|----------|------------------------------------|
| `id`         | string   | Yes      | --       | Unique step identifier             |
| `job_type`   | string   | Yes      | `shell`  | Job type for this step             |
| `payload`    | object   | No       | `{}`     | Job payload                        |
| `payment`    | number   | No       | `50.0`   | Payment for this step              |
| `priority`   | number   | No       | `0.5`    | Priority 0.0-1.0                   |
| `depends_on` | string[] | No       | `[]`     | Step IDs that must complete first  |

**Response (201):**
```json
{
  "id": "pipeline-a1b2c3d4",
  "name": "security-audit",
  "status": "running",
  "created_at": 1711500000.0,
  "completed_at": null,
  "error": null,
  "steps": [
    {
      "id": "scan-ports",
      "job_type": "port_scan",
      "payload": { "target": "192.168.1.100" },
      "depends_on": [],
      "status": "submitted",
      "job_id": "pipe-scan-ports-a1b2c3",
      "result": null,
      "error": null
    },
    {
      "id": "scan-malware",
      "job_type": "malware_scan",
      "payload": { "target": "/opt/app" },
      "depends_on": [],
      "status": "submitted",
      "job_id": "pipe-scan-malware-d4e5f6",
      "result": null,
      "error": null
    },
    {
      "id": "report",
      "job_type": "shell",
      "payload": { "command": "echo Audit complete" },
      "depends_on": ["scan-ports", "scan-malware"],
      "status": "pending",
      "job_id": "pipe-report-g7h8i9",
      "result": null,
      "error": null
    }
  ]
}
```

**Validation errors (400):**
```json
{
  "error": ["Step 'report' depends on unknown step 'nonexistent'"]
}
```

The pipeline engine validates that all dependency references exist and that the graph contains no cycles.

**Step statuses:** `pending`, `waiting`, `submitted`, `completed`, `failed`, `skipped`

**Pipeline statuses:** `pending`, `running`, `completed`, `failed`, `cancelled`

#### `GET /api/pipelines`

List all pipelines.

```bash
curl http://localhost:3101/api/pipelines
```

**Response (200):**
```json
{
  "pipelines": [
    {
      "id": "pipeline-a1b2c3d4",
      "name": "security-audit",
      "status": "completed",
      "created_at": 1711500000.0,
      "completed_at": 1711500045.0,
      "error": null,
      "steps": [ ... ]
    }
  ],
  "total": 1
}
```

#### `GET /api/pipelines/{pipeline_id}`

Get a single pipeline's status and step results.

```bash
curl http://localhost:3101/api/pipelines/pipeline-a1b2c3d4
```

**Response (200):** Same shape as the pipeline object shown above in the `POST` response.

**Response (404):**
```json
{
  "error": "Pipeline not found"
}
```

---

### Job Groups (Batch)

Job groups let you submit multiple independent jobs at once and track their combined progress. Unlike pipelines, group jobs have no dependency ordering -- they all run in parallel.

#### `POST /api/groups`

Submit a batch of jobs as a group.

```bash
curl -X POST http://localhost:3101/api/groups \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": "my-batch-001",
    "jobs": [
      {
        "job_type": "shell",
        "payload": { "command": "uname -a" },
        "payment": 25.0
      },
      {
        "job_type": "shell",
        "payload": { "command": "df -h" },
        "payment": 25.0
      },
      {
        "job_type": "port_scan",
        "payload": { "target": "10.0.0.1" },
        "payment": 50.0
      }
    ]
  }'
```

**Request body:**

| Field      | Type     | Required | Default        | Description              |
|------------|----------|----------|----------------|--------------------------|
| `jobs`     | array    | Yes      | --             | Array of job specs       |
| `group_id` | string   | No       | auto-generated | Custom group identifier  |

Each job in the `jobs` array supports the same fields as `POST /api/jobs` (`job_type`, `payload`, `payment`, `priority`, `deadline`, `job_id`).

**Response (201):**
```json
{
  "group_id": "my-batch-001",
  "status": "running",
  "total_jobs": 3,
  "completed_jobs": 0,
  "progress": 0.0,
  "created_at": 1711500000.0,
  "completed_at": null,
  "results": {}
}
```

#### `GET /api/groups`

List all job groups.

```bash
curl http://localhost:3101/api/groups
```

**Response (200):**
```json
{
  "groups": [
    {
      "group_id": "my-batch-001",
      "status": "completed",
      "total_jobs": 3,
      "completed_jobs": 3,
      "progress": 1.0,
      "created_at": 1711500000.0,
      "completed_at": 1711500012.5,
      "results": { ... }
    }
  ],
  "total": 1
}
```

#### `GET /api/groups/{group_id}`

Get group status and individual job results.

```bash
curl http://localhost:3101/api/groups/my-batch-001
```

**Response (200):**
```json
{
  "group_id": "my-batch-001",
  "status": "completed",
  "total_jobs": 3,
  "completed_jobs": 3,
  "progress": 1.0,
  "created_at": 1711500000.0,
  "completed_at": 1711500012.5,
  "results": {
    "grp-my-batch-001-a1b2c3": {
      "status": "success",
      "result": { "stdout": "Linux dev 5.15.0\n", "exit_code": 0 },
      "duration": 0.12
    },
    "grp-my-batch-001-d4e5f6": {
      "status": "success",
      "result": { "stdout": "Filesystem  Size  Used ...\n", "exit_code": 0 },
      "duration": 0.15
    },
    "grp-my-batch-001-g7h8i9": {
      "status": "success",
      "result": { "open_ports": [22, 80, 443] },
      "duration": 5.23
    }
  }
}
```

**Group statuses:** `pending`, `running`, `partial`, `completed`, `failed`

**Response (404):**
```json
{
  "error": "Group not found"
}
```

---

### Network and Peers

#### `GET /api/peers`

List all connected peers with capabilities and trust scores.

```bash
curl http://localhost:3101/api/peers
```

**Response (200):**
```json
{
  "peers": [
    {
      "node_id": "node-alpha",
      "capabilities": ["shell", "docker"],
      "ip": "192.168.1.100",
      "trust": 0.920
    },
    {
      "node_id": "node-beta",
      "capabilities": ["shell", "port_scan", "malware_scan"],
      "ip": "192.168.1.101",
      "trust": 0.815
    }
  ],
  "count": 2
}
```

---

### Economy

#### `GET /api/wallet`

Get this node's wallet information.

```bash
curl http://localhost:3101/api/wallet
```

**Response (200):**
```json
{
  "balance": 1250.50,
  "staked": 200.00,
  "total_value": 1450.50,
  "lifetime_earned": 5430.00,
  "lifetime_spent": 4179.50
}
```

#### `GET /api/trust`

Get trust/reputation information for this node and all known peers.

```bash
curl http://localhost:3101/api/trust
```

**Response (200):**
```json
{
  "my_trust": 0.850,
  "quarantined": false,
  "peer_scores": {
    "node-alpha": 0.920,
    "node-beta": 0.815,
    "node-gamma": 0.150
  }
}
```

Trust scores range from 0.0 to 1.0. Nodes with trust below 0.2 are quarantined.

---

### RL Stats

#### `GET /api/rl`

Get reinforcement learning and online learning statistics.

```bash
curl http://localhost:3101/api/rl
```

**Response (200):**
```json
{
  "online_learning": true,
  "buffer_size": 256,
  "updates_performed": 47,
  "exploration_rate": 0.15
}
```

---

## MCP Server (for Claude / AI Agents)

The MCP (Model Context Protocol) server exposes MarlOS capabilities as tools that AI agents such as Claude can call directly. It acts as a bridge: Claude invokes MCP tools, and the MCP server translates them into REST API calls against a running MarlOS node.

### MCP Configuration

Add the following to your Claude Desktop configuration file (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "marlos": {
      "command": "python",
      "args": ["-m", "agent.mcp.server"],
      "env": {
        "MARLOS_API_URL": "http://localhost:3101"
      }
    }
  }
}
```

**Prerequisites:**
- A MarlOS node must be running (`NODE_ID=my-node python -m agent.main`)
- The `MARLOS_API_URL` environment variable points to the node's REST API (default: `http://localhost:3101`)
- The `mcp` and `httpx` Python packages must be installed

You can also run the MCP server standalone for testing:

```bash
python -m agent.mcp.server
```

### MCP Available Tools

#### `submit_job`

Submit a compute job to the MarlOS distributed network.

**Parameters:**

| Parameter  | Type   | Required | Description                                            |
|------------|--------|----------|--------------------------------------------------------|
| `job_type` | string | Yes      | `shell`, `docker`, `port_scan`, `malware_scan`, `hash_crack`, `threat_intel` |
| `payload`  | object | Yes      | Job-specific payload                                   |
| `payment`  | number | No       | Payment in AC tokens (default: 100.0)                  |
| `priority` | number | No       | Priority 0.0-1.0 (default: 0.5)                       |

**Example invocation (as seen by Claude):**
```
Tool: submit_job
Arguments: {
  "job_type": "shell",
  "payload": { "command": "whoami" },
  "payment": 50.0
}
```

**Response text:**
```
Job submitted successfully!
  Job ID: job-a1b2c3d4
  Status: submitted
  Type: shell
  Payment: 50.0 AC

The job is now being auctioned across the network. Use get_job_status with job_id 'job-a1b2c3d4' to check results.
```

#### `get_job_status`

Check the status and result of a previously submitted job.

**Parameters:**

| Parameter | Type   | Required | Description              |
|-----------|--------|----------|--------------------------|
| `job_id`  | string | Yes      | The job ID to query      |

**Example invocation:**
```
Tool: get_job_status
Arguments: { "job_id": "job-a1b2c3d4" }
```

**Response text:**
```
Job: job-a1b2c3d4
Status: success
Result: {
  "stdout": "root\n",
  "exit_code": 0
}
Duration: 0.15s
```

#### `list_jobs`

List all jobs known to this node.

**Parameters:** None

**Response text:**
```
Total jobs: 3

  job-a1b2c3d4: success
  job-e5f6g7h8: executing
  job-i9j0k1l2: auctioning
```

#### `get_network_status`

Get the full status of the MarlOS network from this node's perspective.

**Parameters:** None

**Response text:**
```
MarlOS Network Status
==============================
Node ID: dev-node
Node Name: MarlOS-dev
Peers: 3
Trust Score: 0.850
Quarantined: No
Balance: 1250.50 AC
Jobs Completed: 42
Jobs Failed: 2
Capabilities: shell, docker, port_scan
```

#### `get_peers`

List all connected peers with trust scores and capabilities.

**Parameters:** None

**Response text:**
```
Connected peers: 2

  node-alpha: trust=0.920, caps=[shell, docker]
  node-beta: trust=0.815, caps=[shell, port_scan]
```

#### `get_wallet`

Get wallet balance and token economy information.

**Parameters:** None

**Response text:**
```
MarlOS Wallet
=========================
Balance: 1250.50 AC
Staked: 200.00 AC
Total Value: 1450.50 AC
Lifetime Earned: 5430.00 AC
Lifetime Spent: 4179.50 AC
```

### Example: Claude Submitting a Security Scan

Below is a realistic multi-turn interaction where Claude uses MarlOS via MCP to perform a security audit:

**Turn 1 -- Claude submits a port scan:**
```
Tool: submit_job
Arguments: {
  "job_type": "port_scan",
  "payload": { "target": "192.168.1.0/24" },
  "payment": 150.0,
  "priority": 0.8
}
```

Response:
```
Job submitted successfully!
  Job ID: job-sec-9f3a
  Status: submitted
  Type: port_scan
  Payment: 150.0 AC
```

**Turn 2 -- Claude checks the result:**
```
Tool: get_job_status
Arguments: { "job_id": "job-sec-9f3a" }
```

Response:
```
Job: job-sec-9f3a
Status: success
Result: {
  "open_ports": {
    "192.168.1.1": [22, 80, 443],
    "192.168.1.50": [22, 3306, 8080]
  }
}
Duration: 12.45s
```

**Turn 3 -- Claude submits a follow-up threat intel lookup:**
```
Tool: submit_job
Arguments: {
  "job_type": "threat_intel",
  "payload": { "indicator": "192.168.1.50", "type": "ip" },
  "payment": 75.0
}
```

Claude can then analyze the combined results and provide a security report to the user.

---

## JavaScript SDK

### Installation

```bash
npm install marlos-sdk
```

Or include directly:

```javascript
// CommonJS
const { MarlOSClient } = require('marlos-sdk');

// ESM
import { MarlOSClient } from 'marlos-sdk';
```

### Quick Start

```javascript
import { MarlOSClient } from 'marlos-sdk';

const client = new MarlOSClient('http://localhost:3101');

// Check node health
const health = await client.health();
console.log(health);
// { status: "ok", node_id: "dev-node" }

// Submit a job and get result
const result = await client.submitAndWait('shell', { command: 'echo hello' });
console.log(result);
// { job_id: "job-...", status: "success", result: { stdout: "hello\n", exit_code: 0 }, duration: 0.12 }
```

### Constructor Options

```javascript
const client = new MarlOSClient('http://localhost:3101', {
  timeout: 30000,       // Request timeout in ms (default: 30000)
  headers: {            // Additional headers for all requests
    'X-Custom': 'value'
  }
});
```

### SDK Jobs

#### `submitJob(jobType, payload, options?)`

Submit a job to the network. Returns immediately with a job ID.

```javascript
const { job_id, status } = await client.submitJob('shell', {
  command: 'ls -la /tmp'
}, {
  payment: 75,
  priority: 0.8,
  jobId: 'my-custom-id'    // optional
});

console.log(job_id);    // "my-custom-id"
console.log(status);    // "submitted"
```

#### `getJob(jobId)`

Get the current status and result of a job.

```javascript
const job = await client.getJob('job-a1b2c3d4');

console.log(job.status);    // "success" | "executing" | "auctioning" | "failed"
console.log(job.result);    // { stdout: "...", exit_code: 0 }
console.log(job.duration);  // 0.342
console.log(job.error);     // null or error string
```

#### `listJobs()`

List all known jobs on this node.

```javascript
const { jobs, total } = await client.listJobs();

for (const job of jobs) {
  console.log(`${job.job_id}: ${job.status}`);
}
```

### submitAndWait Pattern

The most common pattern: submit a job and block until it completes (or times out).

#### `submitAndWait(jobType, payload, options?)`

```javascript
// Simple usage
const result = await client.submitAndWait('shell', {
  command: 'python3 -c "print(2**100)"'
});
console.log(result.result.stdout);  // "1267650600228229401496703205376\n"

// With custom poll settings
const result = await client.submitAndWait('docker', {
  image: 'node:20',
  command: 'node -e "console.log(JSON.stringify({v: process.version}))"'
}, {
  payment: 200,
  priority: 0.9,
  pollInterval: 2000,   // check every 2 seconds (default: 1000)
  maxWait: 120000        // wait up to 2 minutes (default: 60000)
});
```

#### `waitForJob(jobId, options?)`

Poll an already-submitted job until completion.

```javascript
const { job_id } = await client.submitJob('hash_crack', {
  hash: '5f4dcc3b5aa765d61d8327deb882cf99',
  algorithm: 'md5'
});

// Do other work...

const result = await client.waitForJob(job_id, {
  pollInterval: 5000,
  maxWait: 300000
});
```

Throws `Error` if the job does not complete within `maxWait` milliseconds.

### SDK Pipelines

#### `submitPipeline(pipeline)`

Submit a DAG pipeline. Steps run in dependency order; steps with no dependencies run in parallel.

```javascript
const pipeline = await client.submitPipeline({
  name: 'data-processing',
  steps: [
    {
      id: 'fetch',
      job_type: 'shell',
      payload: { command: 'curl -s https://api.example.com/data' },
      payment: 30
    },
    {
      id: 'parse',
      job_type: 'shell',
      payload: { command: 'python3 parse.py' },
      depends_on: ['fetch'],
      payment: 50
    },
    {
      id: 'store',
      job_type: 'shell',
      payload: { command: 'python3 store.py' },
      depends_on: ['parse'],
      payment: 40
    }
  ]
});

console.log(pipeline.id);      // "pipeline-a1b2c3d4"
console.log(pipeline.status);  // "running"
```

#### `getPipeline(pipelineId)`

Poll a pipeline's status and step results.

```javascript
const status = await client.getPipeline(pipeline.id);

for (const step of status.steps) {
  console.log(`${step.id}: ${step.status}`);
  if (step.result) console.log('  Result:', step.result);
  if (step.error) console.log('  Error:', step.error);
}
```

#### `listPipelines()`

```javascript
const { pipelines, total } = await client.listPipelines();
console.log(`${total} pipelines`);
```

### SDK Job Groups

#### `submitGroup(jobs, groupId?)`

Submit multiple independent jobs as a batch. All jobs run in parallel.

```javascript
const group = await client.submitGroup([
  { job_type: 'shell', payload: { command: 'uname -a' }, payment: 20 },
  { job_type: 'shell', payload: { command: 'df -h' }, payment: 20 },
  { job_type: 'shell', payload: { command: 'free -m' }, payment: 20 },
], 'system-check-001');

console.log(group.group_id);       // "system-check-001"
console.log(group.total_jobs);     // 3
console.log(group.progress);       // 0.0
```

#### `getGroup(groupId)`

Check group progress and collect results.

```javascript
const group = await client.getGroup('system-check-001');

console.log(group.status);          // "completed" | "running" | "partial" | "failed"
console.log(group.progress);        // 1.0 (all done)
console.log(group.completed_jobs);  // 3

for (const [jobId, result] of Object.entries(group.results)) {
  console.log(`${jobId}: ${result.status} (${result.duration}s)`);
}
```

### SDK Network and Economy

```javascript
// Full node status
const status = await client.getStatus();
console.log(`Node: ${status.node_id}, Peers: ${status.peers}`);

// Health check
const health = await client.health();
console.log(health.status);  // "ok"

// Connected peers
const { peers, count } = await client.getPeers();
for (const peer of peers) {
  console.log(`${peer.node_id}: trust=${peer.trust}, caps=${peer.capabilities}`);
}

// Wallet balance
const wallet = await client.getWallet();
console.log(`Balance: ${wallet.balance} AC, Staked: ${wallet.staked} AC`);

// Trust scores
const trust = await client.getTrust();
console.log(`My trust: ${trust.my_trust}, Quarantined: ${trust.quarantined}`);

// RL / learning stats
const rl = await client.getRLStats();
console.log(`Online learning: ${rl.online_learning}, Updates: ${rl.updates_performed}`);
```

### Error Handling

The SDK throws `MarlOSError` for non-2xx HTTP responses:

```javascript
import { MarlOSClient, MarlOSError } from 'marlos-sdk';

const client = new MarlOSClient('http://localhost:3101');

try {
  const job = await client.getJob('nonexistent-job');
} catch (err) {
  if (err instanceof MarlOSError) {
    console.log(err.message);      // "Job not found"
    console.log(err.statusCode);   // 404
  }
}

// Timeout on waitForJob
try {
  const result = await client.submitAndWait('shell', {
    command: 'sleep 999'
  }, { maxWait: 5000 });
} catch (err) {
  console.log(err.message);  // "Job job-... did not complete within 5000ms"
}
```

Network errors (node unreachable) throw standard `fetch` errors. Wrap calls in try/catch for production use.
