import { useState } from 'react';

const Jobs = ({ agentState }) => {
  const [selectedJob, setSelectedJob] = useState(null);
  const [filter, setFilter] = useState('all'); // all, active, completed, failed

  if (!agentState) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400">Waiting for agent connection...</div>
      </div>
    );
  }

  // Get job data from agentState - NO HARDCODED DATA
  const activeJobs = agentState.active_jobs_list || [];
  const jobHistory = agentState.job_history || [];

  const allJobs = [
    ...activeJobs.map(j => ({ ...j, status: j.status || 'active' })),
    ...jobHistory
  ];

  const filteredJobs = filter === 'all'
    ? allJobs
    : filter === 'active'
    ? activeJobs
    : jobHistory.filter(j => j.status === filter || (filter === 'completed' && (j.status === 'success' || j.status === 'completed')) || (filter === 'failed' && (j.status === 'failed' || j.status === 'timeout')));

  const getStatusClass = (status) => {
    switch (status) {
      case 'active':
      case 'running':
        return 'bg-blue-900 text-blue-200';
      case 'completed':
      case 'success':
        return 'bg-green-900 text-green-200';
      case 'failed':
      case 'timeout':
        return 'bg-red-900 text-red-200';
      default:
        return 'bg-gray-900 text-gray-200';
    }
  };

  const getJobTypeIcon = (jobType) => {
    const icons = {
      shell: '▣',
      docker: '◈',
      malware_scan: '◆',
      port_scan: '◇',
      vuln_scan: '▤',
      hash_crack: '◉',
      threat_intel: '◎',
      log_analysis: '▥',
      forensics: '◐',
    };
    return icons[jobType] || '■';
  };

  const completedCount = jobHistory.filter(j => j.status === 'completed' || j.status === 'success').length;
  const failedCount = jobHistory.filter(j => j.status === 'failed' || j.status === 'timeout').length;

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-3xl font-bold text-white">Job Management</h2>

      {/* Job Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-black border border-gray-800 p-4 rounded">
          <div className="text-gray-400 text-sm mb-1">Active Jobs</div>
          <div className="text-2xl font-bold text-white">{agentState.active_jobs || 0}</div>
        </div>
        <div className="bg-black border border-gray-800 p-4 rounded">
          <div className="text-gray-400 text-sm mb-1">Completed</div>
          <div className="text-2xl font-bold text-green-400">{agentState.jobs_completed || 0}</div>
        </div>
        <div className="bg-black border border-gray-800 p-4 rounded">
          <div className="text-gray-400 text-sm mb-1">Failed</div>
          <div className="text-2xl font-bold text-red-400">{agentState.jobs_failed || 0}</div>
        </div>
        <div className="bg-black border border-gray-800 p-4 rounded">
          <div className="text-gray-400 text-sm mb-1">Success Rate</div>
          <div className="text-2xl font-bold text-white">
            {agentState.jobs_completed > 0
              ? ((agentState.jobs_completed / (agentState.jobs_completed + agentState.jobs_failed)) * 100).toFixed(0)
              : 0}%
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2">
        <button
          className={`px-4 py-2 rounded transition-colors ${filter === 'all' ? 'bg-white text-black' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
          onClick={() => setFilter('all')}
        >
          All ({allJobs.length})
        </button>
        <button
          className={`px-4 py-2 rounded transition-colors ${filter === 'active' ? 'bg-white text-black' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
          onClick={() => setFilter('active')}
        >
          Active ({activeJobs.length})
        </button>
        <button
          className={`px-4 py-2 rounded transition-colors ${filter === 'completed' ? 'bg-white text-black' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
          onClick={() => setFilter('completed')}
        >
          Completed ({completedCount})
        </button>
        <button
          className={`px-4 py-2 rounded transition-colors ${filter === 'failed' ? 'bg-white text-black' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
          onClick={() => setFilter('failed')}
        >
          Failed ({failedCount})
        </button>
      </div>

      {/* Job List */}
      <div className="bg-black border border-gray-800 rounded p-6">
        <div className="space-y-3 max-h-[600px] overflow-y-auto">
          {filteredJobs.length === 0 ? (
            <div className="text-center text-gray-500 py-8">No jobs to display</div>
          ) : (
            filteredJobs.map((job, index) => (
              <div
                key={job.job_id || index}
                className="border border-gray-800 p-4 rounded hover:border-gray-700 cursor-pointer transition-colors"
                onClick={() => setSelectedJob(job)}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-start gap-3">
                    <div className="text-2xl text-gray-400">{getJobTypeIcon(job.job_type)}</div>
                    <div>
                      <div className="text-white font-mono text-sm">{job.job_id || `Job ${index + 1}`}</div>
                      <div className="text-gray-400 text-sm">{job.job_type}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`px-2 py-1 rounded text-xs ${getStatusClass(job.status)}`}>
                      {job.status || 'unknown'}
                    </span>
                    {job.payment !== undefined && (
                      <div className="text-white text-sm mt-1">{job.payment} AC</div>
                    )}
                  </div>
                </div>

                {job.priority !== undefined && (
                  <div className="text-gray-400 text-sm">
                    Priority: {(job.priority * 100).toFixed(0)}%
                  </div>
                )}

                {job.status === 'active' && job.progress !== undefined && (
                  <div className="mt-3">
                    <div className="flex justify-between text-xs text-gray-400 mb-1">
                      <span>Progress</span>
                      <span>{(job.progress * 100).toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-gray-900 rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full bg-blue-400 transition-all duration-500"
                        style={{ width: `${job.progress * 100}%` }}
                      ></div>
                    </div>
                  </div>
                )}

                {job.duration !== undefined && (
                  <div className="text-gray-400 text-sm mt-2">Duration: {job.duration.toFixed(2)}s</div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Job Details Modal */}
      {selectedJob && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" onClick={() => setSelectedJob(null)}>
          <div className="bg-black border border-gray-800 rounded-lg p-6 max-w-4xl w-full m-4 max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-white">Job Details</h3>
              <button className="text-gray-400 hover:text-white text-2xl" onClick={() => setSelectedJob(null)}>×</button>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-400">Job ID</span>
                <span className="text-white font-mono">{selectedJob.job_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Type</span>
                <span className="text-white">{selectedJob.job_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Status</span>
                <span className={`px-2 py-1 rounded text-xs ${getStatusClass(selectedJob.status)}`}>
                  {selectedJob.status}
                </span>
              </div>
              {selectedJob.priority !== undefined && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Priority</span>
                  <span className="text-white">{(selectedJob.priority * 100).toFixed(0)}%</span>
                </div>
              )}
              {selectedJob.payment !== undefined && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Payment</span>
                  <span className="text-white">{selectedJob.payment} AC</span>
                </div>
              )}
              {selectedJob.stake !== undefined && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Stake</span>
                  <span className="text-white">{selectedJob.stake} AC</span>
                </div>
              )}
              {selectedJob.deadline && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Deadline</span>
                  <span className="text-white">{new Date(selectedJob.deadline * 1000).toLocaleString()}</span>
                </div>
              )}
              {selectedJob.start_time && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Started</span>
                  <span className="text-white">{new Date(selectedJob.start_time * 1000).toLocaleString()}</span>
                </div>
              )}
              {selectedJob.duration !== undefined && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Duration</span>
                  <span className="text-white">{selectedJob.duration.toFixed(2)}s</span>
                </div>
              )}
              {selectedJob.payload && Object.keys(selectedJob.payload).length > 0 && (
                <div>
                  <div className="text-gray-400 mb-2">Payload</div>
                  <pre className="bg-gray-900 p-3 rounded text-white text-xs overflow-x-auto">
                    {JSON.stringify(selectedJob.payload, null, 2)}
                  </pre>
                </div>
              )}
              {selectedJob.output && (
                <div>
                  <div className="text-gray-400 mb-2">Output</div>
                  <pre className="bg-gray-900 p-3 rounded text-white text-xs overflow-x-auto">
                    {typeof selectedJob.output === 'string' ? selectedJob.output : JSON.stringify(selectedJob.output, null, 2)}
                  </pre>
                </div>
              )}
              {selectedJob.error && (
                <div>
                  <div className="text-gray-400 mb-2">Error</div>
                  <pre className="bg-red-900 bg-opacity-20 border border-red-800 p-3 rounded text-red-200 text-xs overflow-x-auto">
                    {selectedJob.error}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Jobs;
