/**
 * MarlOS JavaScript SDK
 * Thin client for interacting with MarlOS nodes via REST API.
 *
 * Usage:
 *   import { MarlOSClient } from 'marlos-sdk';
 *
 *   const client = new MarlOSClient('http://localhost:3101');
 *   const { job_id } = await client.submitJob('shell', { command: 'echo hello' });
 *   const result = await client.waitForJob(job_id);
 */

class MarlOSClient {
  /**
   * @param {string} baseUrl - MarlOS REST API URL (e.g., 'http://localhost:3101')
   * @param {object} [options]
   * @param {number} [options.timeout=30000] - Request timeout in ms
   * @param {object} [options.headers] - Additional headers
   */
  constructor(baseUrl, options = {}) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.timeout = options.timeout || 30000;
    this.headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
  }

  // ── Jobs ──────────────────────────────────────────────────────

  /**
   * Submit a job to the MarlOS network.
   * @param {string} jobType - Job type: 'shell', 'docker', 'port_scan', etc.
   * @param {object} payload - Job payload (e.g., { command: 'echo hello' })
   * @param {object} [options]
   * @param {number} [options.payment=100] - Payment in AC tokens
   * @param {number} [options.priority=0.5] - Priority 0-1
   * @param {string} [options.jobId] - Custom job ID
   * @returns {Promise<{job_id: string, status: string}>}
   */
  async submitJob(jobType, payload, options = {}) {
    return this._post('/api/jobs', {
      job_type: jobType,
      payload,
      payment: options.payment || 100,
      priority: options.priority || 0.5,
      job_id: options.jobId,
    });
  }

  /**
   * Get status and result of a job.
   * @param {string} jobId
   * @returns {Promise<{job_id: string, status: string, result?: any, duration?: number, error?: string}>}
   */
  async getJob(jobId) {
    return this._get(`/api/jobs/${jobId}`);
  }

  /**
   * List all known jobs.
   * @returns {Promise<{jobs: Array, total: number}>}
   */
  async listJobs() {
    return this._get('/api/jobs');
  }

  /**
   * Submit a job and wait for completion.
   * @param {string} jobType
   * @param {object} payload
   * @param {object} [options]
   * @param {number} [options.pollInterval=1000] - Poll interval in ms
   * @param {number} [options.maxWait=60000] - Max wait time in ms
   * @returns {Promise<object>} Job result
   */
  async submitAndWait(jobType, payload, options = {}) {
    const { job_id } = await this.submitJob(jobType, payload, options);
    return this.waitForJob(job_id, options);
  }

  /**
   * Poll until a job completes.
   * @param {string} jobId
   * @param {object} [options]
   * @param {number} [options.pollInterval=1000]
   * @param {number} [options.maxWait=60000]
   * @returns {Promise<object>}
   */
  async waitForJob(jobId, options = {}) {
    const pollInterval = options.pollInterval || 1000;
    const maxWait = options.maxWait || 60000;
    const start = Date.now();

    while (Date.now() - start < maxWait) {
      const job = await this.getJob(jobId);
      if (job.status === 'success' || job.status === 'failed' || job.status === 'JobStatus.SUCCESS' || job.status === 'JobStatus.FAILURE') {
        return job;
      }
      await new Promise((r) => setTimeout(r, pollInterval));
    }

    throw new Error(`Job ${jobId} did not complete within ${maxWait}ms`);
  }

  // ── Pipelines ─────────────────────────────────────────────────

  /**
   * Submit a pipeline (DAG of jobs).
   * @param {object} pipeline - Pipeline definition with steps
   * @returns {Promise<object>} Pipeline status
   */
  async submitPipeline(pipeline) {
    return this._post('/api/pipelines', pipeline);
  }

  /**
   * Get pipeline status.
   * @param {string} pipelineId
   * @returns {Promise<object>}
   */
  async getPipeline(pipelineId) {
    return this._get(`/api/pipelines/${pipelineId}`);
  }

  /**
   * List all pipelines.
   * @returns {Promise<{pipelines: Array, total: number}>}
   */
  async listPipelines() {
    return this._get('/api/pipelines');
  }

  // ── Job Groups (Batch) ────────────────────────────────────────

  /**
   * Submit a batch of jobs as a group.
   * @param {Array<object>} jobs - Array of job specs
   * @param {string} [groupId] - Optional group ID
   * @returns {Promise<object>} Group status
   */
  async submitGroup(jobs, groupId) {
    return this._post('/api/groups', { jobs, group_id: groupId });
  }

  /**
   * Get group status and results.
   * @param {string} groupId
   * @returns {Promise<object>}
   */
  async getGroup(groupId) {
    return this._get(`/api/groups/${groupId}`);
  }

  // ── Network ───────────────────────────────────────────────────

  /**
   * Get full node status.
   * @returns {Promise<object>}
   */
  async getStatus() {
    return this._get('/api/status');
  }

  /**
   * Health check.
   * @returns {Promise<{status: string, node_id: string}>}
   */
  async health() {
    return this._get('/api/health');
  }

  /**
   * List connected peers.
   * @returns {Promise<{peers: Array, count: number}>}
   */
  async getPeers() {
    return this._get('/api/peers');
  }

  // ── Economy ───────────────────────────────────────────────────

  /**
   * Get wallet info.
   * @returns {Promise<{balance: number, staked: number, total_value: number}>}
   */
  async getWallet() {
    return this._get('/api/wallet');
  }

  /**
   * Get trust scores.
   * @returns {Promise<{my_trust: number, quarantined: boolean, peer_scores: object}>}
   */
  async getTrust() {
    return this._get('/api/trust');
  }

  /**
   * Get RL / online learning stats.
   * @returns {Promise<object>}
   */
  async getRLStats() {
    return this._get('/api/rl');
  }

  // ── HTTP helpers ──────────────────────────────────────────────

  async _get(path) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const resp = await fetch(`${this.baseUrl}${path}`, {
        method: 'GET',
        headers: this.headers,
        signal: controller.signal,
      });
      const data = await resp.json();
      if (!resp.ok) throw new MarlOSError(data.error || `HTTP ${resp.status}`, resp.status);
      return data;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  async _post(path, body) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const resp = await fetch(`${this.baseUrl}${path}`, {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      const data = await resp.json();
      if (!resp.ok) throw new MarlOSError(data.error || `HTTP ${resp.status}`, resp.status);
      return data;
    } finally {
      clearTimeout(timeoutId);
    }
  }
}

class MarlOSError extends Error {
  constructor(message, statusCode) {
    super(message);
    this.name = 'MarlOSError';
    this.statusCode = statusCode;
  }
}

// CommonJS + ESM dual export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { MarlOSClient, MarlOSError };
}

export { MarlOSClient, MarlOSError };
