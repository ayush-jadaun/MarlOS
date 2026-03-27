export interface JobSubmitOptions {
  payment?: number;
  priority?: number;
  jobId?: string;
}

export interface WaitOptions {
  pollInterval?: number;
  maxWait?: number;
}

export interface JobResult {
  job_id: string;
  status: string;
  result?: any;
  duration?: number;
  error?: string;
}

export interface PeerInfo {
  node_id: string;
  capabilities: string[];
  ip: string;
  trust: number;
}

export interface WalletInfo {
  balance: number;
  staked: number;
  total_value: number;
  lifetime_earned: number;
  lifetime_spent: number;
}

export interface TrustInfo {
  my_trust: number;
  quarantined: boolean;
  peer_scores: Record<string, number>;
}

export class MarlOSClient {
  constructor(baseUrl: string, options?: { timeout?: number; headers?: Record<string, string> });

  // Jobs
  submitJob(jobType: string, payload: object, options?: JobSubmitOptions): Promise<{ job_id: string; status: string }>;
  getJob(jobId: string): Promise<JobResult>;
  listJobs(): Promise<{ jobs: JobResult[]; total: number }>;
  submitAndWait(jobType: string, payload: object, options?: JobSubmitOptions & WaitOptions): Promise<JobResult>;
  waitForJob(jobId: string, options?: WaitOptions): Promise<JobResult>;

  // Pipelines
  submitPipeline(pipeline: object): Promise<object>;
  getPipeline(pipelineId: string): Promise<object>;
  listPipelines(): Promise<{ pipelines: object[]; total: number }>;

  // Groups
  submitGroup(jobs: object[], groupId?: string): Promise<object>;
  getGroup(groupId: string): Promise<object>;

  // Network
  getStatus(): Promise<object>;
  health(): Promise<{ status: string; node_id: string }>;
  getPeers(): Promise<{ peers: PeerInfo[]; count: number }>;

  // Economy
  getWallet(): Promise<WalletInfo>;
  getTrust(): Promise<TrustInfo>;
  getRLStats(): Promise<object>;
}

export class MarlOSError extends Error {
  statusCode: number;
  constructor(message: string, statusCode: number);
}
