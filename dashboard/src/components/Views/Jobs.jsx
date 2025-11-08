import { Activity, CheckCircle, XCircle, Clock, TrendingUp } from 'lucide-react';

export default function Jobs({ agentState }) {
  if (!agentState) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400">No agent data available</div>
      </div>
    );
  }

  // Extract job statistics - with fallbacks
  const jobs = agentState.jobs || {
    active: 0,
    completed: 0,
    failed: 0,
    total: 0,
    success_rate: 0
  };

  const recentJobs = agentState.recent_jobs || [];

  // Calculate stats
  const activeJobs = jobs.active || 0;
  const completedJobs = jobs.completed || 0;
  const failedJobs = jobs.failed || 0;
  const totalJobs = jobs.total || 0;
  const successRate = jobs.success_rate || 0;

  // Status badge component
  const StatusBadge = ({ status }) => {
    const styles = {
      success: 'bg-green-900/50 text-green-300 border-green-700',
      failure: 'bg-red-900/50 text-red-300 border-red-700',
      timeout: 'bg-yellow-900/50 text-yellow-300 border-yellow-700',
      running: 'bg-blue-900/50 text-blue-300 border-blue-700'
    };

    return (
      <span className={`px-2 py-1 text-xs rounded border ${styles[status] || styles.running}`}>
        {status}
      </span>
    );
  };

  // Format duration
  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    return `${(seconds / 60).toFixed(1)}m`;
  };

  // Format timestamp
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString();
  };

  return (
    <div className="p-6 space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Active Jobs */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Active Jobs</p>
              <p className="text-3xl font-bold text-blue-400 mt-2">{activeJobs}</p>
            </div>
            <div className="bg-blue-900/30 p-3 rounded-lg">
              <Activity className="w-6 h-6 text-blue-400" />
            </div>
          </div>
        </div>

        {/* Completed Jobs */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Completed</p>
              <p className="text-3xl font-bold text-green-400 mt-2">{completedJobs}</p>
            </div>
            <div className="bg-green-900/30 p-3 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-400" />
            </div>
          </div>
        </div>

        {/* Failed Jobs */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Failed</p>
              <p className="text-3xl font-bold text-red-400 mt-2">{failedJobs}</p>
            </div>
            <div className="bg-red-900/30 p-3 rounded-lg">
              <XCircle className="w-6 h-6 text-red-400" />
            </div>
          </div>
        </div>

        {/* Success Rate */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Success Rate</p>
              <p className="text-3xl font-bold text-purple-400 mt-2">{successRate.toFixed(1)}%</p>
            </div>
            <div className="bg-purple-900/30 p-3 rounded-lg">
              <TrendingUp className="w-6 h-6 text-purple-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Recent Jobs Table */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg">
        <div className="p-4 border-b border-zinc-800">
          <h3 className="text-lg font-semibold">Recent Jobs</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-zinc-800/50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Job ID</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Duration</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {recentJobs.length === 0 ? (
                <tr>
                  <td colSpan="4" className="px-4 py-8 text-center text-gray-500">
                    No jobs executed yet
                  </td>
                </tr>
              ) : (
                recentJobs.map((job, index) => (
                  <tr key={job.job_id || index} className="hover:bg-zinc-800/50">
                    <td className="px-4 py-3 text-sm font-mono">{job.job_id?.slice(0, 12)}...</td>
                    <td className="px-4 py-3 text-sm">
                      <StatusBadge status={job.status} />
                    </td>
                    <td className="px-4 py-3 text-sm">{formatDuration(job.duration)}</td>
                    <td className="px-4 py-3 text-sm text-gray-400">{formatTimestamp(job.timestamp)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Debug Info (remove in production) */}
      <details className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
        <summary className="cursor-pointer text-sm text-gray-400 hover:text-white">
          Debug: Raw Job Data
        </summary>
        <pre className="mt-4 text-xs text-gray-500 overflow-auto">
          {JSON.stringify(agentState.jobs, null, 2)}
        </pre>
      </details>
    </div>
  );
}