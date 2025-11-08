const Overview = ({ agentState }) => {
  if (!agentState) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400">Waiting for agent connection...</div>
      </div>
    );
  }

  const statusClass = agentState.quarantined ? 'bg-red-900 text-red-200' : 'bg-green-900 text-green-200';

  const totalJobs = (agentState.jobs_completed || 0) + (agentState.jobs_failed || 0);
  const successRate = totalJobs > 0 ? ((agentState.jobs_completed / totalJobs) * 100).toFixed(1) : 0;

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-3xl font-bold text-white">Agent Overview</h2>

      <div className="grid grid-cols-2 gap-4">
        {/* Agent Identity */}
        <div className="bg-black border border-gray-800 rounded p-6">
          <h3 className="text-xl font-bold text-white mb-4">Identity</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Node ID</span>
              <span className="text-white font-mono text-sm">{agentState.node_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Name</span>
              <span className="text-white">{agentState.node_name || 'Unnamed'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Public Key</span>
              <span className="text-white font-mono text-xs">{agentState.public_key?.substring(0, 32)}...</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Status</span>
              <span className={`px-2 py-1 rounded text-xs ${statusClass}`}>
                {agentState.quarantined ? 'Quarantined' : 'Active'}
              </span>
            </div>
          </div>
        </div>

        {/* Wallet Summary */}
        <div className="bg-black border border-gray-800 rounded p-6">
          <h3 className="text-xl font-bold text-white mb-4">Wallet</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Available</span>
              <span className="text-white">{agentState.wallet?.balance?.toFixed(2)} AC</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Staked</span>
              <span className="text-white">{agentState.wallet?.staked?.toFixed(2)} AC</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Total Value</span>
              <span className="text-white font-bold">{agentState.wallet?.total_value?.toFixed(2)} AC</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Net Profit</span>
              <span className={`${agentState.wallet?.net_profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {agentState.wallet?.net_profit >= 0 ? '+' : ''}{agentState.wallet?.net_profit?.toFixed(2)} AC
              </span>
            </div>
          </div>
        </div>

        {/* Trust & Reputation */}
        <div className="bg-black border border-gray-800 rounded p-6">
          <h3 className="text-xl font-bold text-white mb-4">Trust & Reputation</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Trust Score</span>
              <span className="text-white text-xl font-bold">{(agentState.trust_score * 100).toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-900 rounded-full h-3 overflow-hidden">
              <div
                className="h-full bg-blue-400 transition-all duration-500"
                style={{ width: `${agentState.trust_score * 100}%` }}
              ></div>
            </div>
            {agentState.reputation_stats && (
              <>
                <div className="flex justify-between">
                  <span className="text-gray-400">Success Events</span>
                  <span className="text-green-400">{agentState.reputation_stats.success_count || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Failure Events</span>
                  <span className="text-red-400">{agentState.reputation_stats.failure_count || 0}</span>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Job Statistics */}
        <div className="bg-black border border-gray-800 rounded p-6">
          <h3 className="text-xl font-bold text-white mb-4">Job Statistics</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Completed</span>
              <span className="text-green-400 font-bold">{agentState.jobs_completed || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Failed</span>
              <span className="text-red-400 font-bold">{agentState.jobs_failed || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Active</span>
              <span className="text-white font-bold">{agentState.active_jobs || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Success Rate</span>
              <span className="text-white font-bold">{successRate}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Capabilities */}
      <div className="bg-black border border-gray-800 rounded p-6">
        <h3 className="text-xl font-bold text-white mb-4">Capabilities</h3>
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

      {/* Network */}
      <div className="bg-black border border-gray-800 rounded p-6">
        <h3 className="text-xl font-bold text-white mb-4">Network</h3>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="text-gray-400 text-sm mb-1">Connected Peers</div>
            <div className="text-2xl font-bold text-white">{agentState.peers || 0}</div>
          </div>
          {agentState.watchdog_stats && (
            <>
              <div>
                <div className="text-gray-400 text-sm mb-1">Quarantined Peers</div>
                <div className="text-2xl font-bold text-orange-400">{agentState.watchdog_stats.quarantined_count || 0}</div>
              </div>
              <div>
                <div className="text-gray-400 text-sm mb-1">Blacklisted</div>
                <div className="text-2xl font-bold text-red-400">{agentState.watchdog_stats.blacklisted_count || 0}</div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Overview;
