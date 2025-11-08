const Metrics = ({ agentState }) => {
  if (!agentState) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400">Waiting for agent connection...</div>
      </div>
    );
  }

  const performanceMetrics = agentState.performance_metrics || {};
  const rlStats = agentState.rl_stats || {};

  // Calculate success rate
  const totalJobs = (agentState.jobs_completed || 0) + (agentState.jobs_failed || 0);
  const successRate = totalJobs > 0
    ? ((agentState.jobs_completed || 0) / totalJobs) * 100
    : 0;

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-3xl font-bold text-white">Performance Metrics</h2>

      {/* Key Performance Indicators */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-black border border-gray-800 p-6 rounded">
          <div className="text-gray-400 text-sm mb-2">Success Rate</div>
          <div className="text-3xl font-bold text-green-400">{successRate.toFixed(1)}%</div>
          <div className="text-gray-500 text-xs mt-1">
            {agentState.jobs_completed || 0} / {totalJobs} jobs
          </div>
        </div>
        <div className="bg-black border border-gray-800 p-6 rounded">
          <div className="text-gray-400 text-sm mb-2">Avg Completion Time</div>
          <div className="text-3xl font-bold text-white">
            {performanceMetrics.avg_completion_time?.toFixed(1) || '0.0'}s
          </div>
        </div>
        <div className="bg-black border border-gray-800 p-6 rounded">
          <div className="text-gray-400 text-sm mb-2">Trust Score</div>
          <div className="text-3xl font-bold text-blue-400">
            {((agentState.trust_score || 0) * 100).toFixed(0)}%
          </div>
        </div>
        <div className="bg-black border border-gray-800 p-6 rounded">
          <div className="text-gray-400 text-sm mb-2">Total Earnings</div>
          <div className="text-3xl font-bold text-green-400">
            {agentState.wallet?.lifetime_earned?.toFixed(0) || 0} AC
          </div>
        </div>
      </div>

      {/* Job Performance */}
      <div className="bg-black border border-gray-800 rounded p-6">
        <h3 className="text-xl font-bold text-white mb-4">Job Performance</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="border border-gray-800 p-4 rounded">
            <div className="text-gray-400 text-sm mb-1">Completed</div>
            <div className="text-3xl font-bold text-green-400">
              {agentState.jobs_completed || 0}
            </div>
          </div>
          <div className="border border-gray-800 p-4 rounded">
            <div className="text-gray-400 text-sm mb-1">Failed</div>
            <div className="text-3xl font-bold text-red-400">
              {agentState.jobs_failed || 0}
            </div>
          </div>
          <div className="border border-gray-800 p-4 rounded">
            <div className="text-gray-400 text-sm mb-1">Active</div>
            <div className="text-3xl font-bold text-yellow-400">
              {agentState.active_jobs || 0}
            </div>
          </div>
        </div>

        {/* Success Rate Bar */}
        <div className="mt-6">
          <div className="flex justify-between text-sm text-gray-400 mb-2">
            <span>Success Rate</span>
            <span>{successRate.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-900 rounded-full h-3 overflow-hidden">
            <div
              className="h-full bg-green-400 transition-all duration-500"
              style={{ width: `${successRate}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* RL Learning Stats */}
      {Object.keys(rlStats).length > 0 && (
        <div className="bg-black border border-gray-800 rounded p-6">
          <h3 className="text-xl font-bold text-white mb-4">Reinforcement Learning</h3>
          <div className="grid grid-cols-3 gap-4">
            {rlStats.exploration_rate !== undefined && (
              <div className="border border-gray-800 p-4 rounded">
                <div className="text-gray-400 text-sm mb-1">Exploration Rate</div>
                <div className="text-2xl font-bold text-white">
                  {(rlStats.exploration_rate * 100).toFixed(1)}%
                </div>
              </div>
            )}
            {rlStats.episode_count !== undefined && (
              <div className="border border-gray-800 p-4 rounded">
                <div className="text-gray-400 text-sm mb-1">Episodes</div>
                <div className="text-2xl font-bold text-white">
                  {rlStats.episode_count}
                </div>
              </div>
            )}
            {rlStats.buffer_size !== undefined && (
              <div className="border border-gray-800 p-4 rounded">
                <div className="text-gray-400 text-sm mb-1">Experience Buffer</div>
                <div className="text-2xl font-bold text-white">
                  {rlStats.buffer_size}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Network Stats */}
      <div className="bg-black border border-gray-800 rounded p-6">
        <h3 className="text-xl font-bold text-white mb-4">Network Statistics</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="border border-gray-800 p-4 rounded">
            <div className="text-gray-400 text-sm mb-1">Connected Peers</div>
            <div className="text-3xl font-bold text-white">
              {agentState.peers || 0}
            </div>
          </div>
          {agentState.watchdog_stats && (
            <>
              <div className="border border-gray-800 p-4 rounded">
                <div className="text-gray-400 text-sm mb-1">Quarantined Peers</div>
                <div className="text-3xl font-bold text-orange-400">
                  {agentState.watchdog_stats.quarantined_count || 0}
                </div>
              </div>
              <div className="border border-gray-800 p-4 rounded">
                <div className="text-gray-400 text-sm mb-1">Blacklisted Peers</div>
                <div className="text-3xl font-bold text-red-400">
                  {agentState.watchdog_stats.blacklisted_count || 0}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Job Type Distribution */}
      {performanceMetrics.job_type_stats && (
        <div className="bg-black border border-gray-800 rounded p-6">
          <h3 className="text-xl font-bold text-white mb-4">Job Type Distribution</h3>
          <div className="space-y-3">
            {Object.entries(performanceMetrics.job_type_stats).map(([jobType, stats]) => (
              <div key={jobType} className="border border-gray-800 p-4 rounded">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-white font-medium">{jobType}</span>
                  <span className="text-gray-400">{stats.count} jobs</span>
                </div>
                <div className="flex gap-4 text-sm">
                  <div>
                    <span className="text-gray-400">Success: </span>
                    <span className="text-green-400">{stats.success || 0}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Failed: </span>
                    <span className="text-red-400">{stats.failed || 0}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Avg Time: </span>
                    <span className="text-white">{stats.avg_time?.toFixed(1) || '0.0'}s</span>
                  </div>
                </div>
                <div className="mt-2">
                  <div className="w-full bg-gray-900 rounded-full h-2 overflow-hidden">
                    <div
                      className="h-full bg-blue-400 transition-all duration-500"
                      style={{
                        width: `${stats.count > 0 ? (stats.success / stats.count) * 100 : 0}%`
                      }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Capabilities */}
      <div className="bg-black border border-gray-800 rounded p-6">
        <h3 className="text-xl font-bold text-white mb-4">Agent Capabilities</h3>
        <div className="flex flex-wrap gap-2">
          {agentState.capabilities?.map((cap) => (
            <span
              key={cap}
              className="px-3 py-1 bg-gray-900 border border-gray-800 rounded text-white text-sm"
            >
              {cap}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Metrics;
