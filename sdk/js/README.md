# MarlOS JavaScript SDK

Thin client for interacting with MarlOS distributed compute nodes via REST API.

## Install

```bash
npm install marlos-sdk
# or copy sdk/js/src/index.js into your project
```

## Quick Start

```javascript
import { MarlOSClient } from 'marlos-sdk';

const client = new MarlOSClient('http://localhost:3101');

// Submit a job and wait for result
const result = await client.submitAndWait('shell', { command: 'echo hello' });
console.log(result);

// Check network status
const status = await client.getStatus();
console.log(`Peers: ${status.peers}, Trust: ${status.trust_score}`);
```

## API

### Jobs

```javascript
// Submit a job (returns immediately)
const { job_id } = await client.submitJob('shell', { command: 'ls -la' }, {
  payment: 50,
  priority: 0.8,
});

// Check job status
const job = await client.getJob(job_id);

// Submit and wait for completion
const result = await client.submitAndWait('port_scan', { target: '192.168.1.0/24' });
```

### Pipelines (DAGs)

```javascript
const pipeline = await client.submitPipeline({
  name: 'security-scan',
  steps: [
    { id: 'scan', job_type: 'port_scan', payload: { target: '10.0.0.0/24' } },
    { id: 'analyze', job_type: 'shell', payload: { command: 'python analyze.py' }, depends_on: ['scan'] },
  ],
});
```

### Batch Jobs

```javascript
const group = await client.submitGroup([
  { job_type: 'shell', payload: { command: 'echo 1' } },
  { job_type: 'shell', payload: { command: 'echo 2' } },
  { job_type: 'shell', payload: { command: 'echo 3' } },
]);

// Check progress
const status = await client.getGroup(group.group_id);
console.log(`Progress: ${status.progress * 100}%`);
```

### Network

```javascript
const peers = await client.getPeers();
const wallet = await client.getWallet();
const trust = await client.getTrust();
const rl = await client.getRLStats();
```

## Supported Job Types

- `shell` — Execute shell commands
- `docker` — Run Docker containers
- `port_scan` — Network port scanning
- `malware_scan` — File malware analysis
- `hash_crack` — Hash cracking
- `threat_intel` — Threat intelligence lookups
- Any custom type registered via the plugin system
