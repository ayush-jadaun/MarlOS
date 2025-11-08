const Trust = ({ agentState }) => {
  if (!agentState) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400">Waiting for agent connection...</div>
      </div>
    );
  }

  const trustScore = agentState.trust_score || 0;
  const reputation = agentState.reputation_stats || {};
  const reputationEvents = agentState.reputation_events || [];

  const getTrustLevel = (score) => {
    if (score >= 0.8) return { label: 'Excellent', color: 'text-green-400' };
    if (score >= 0.6) return { label: 'Good', color: 'text-blue-400' };
    if (score >= 0.4) return { label: 'Fair', color: 'text-yellow-400' };
    if (score >= 0.2) return { label: 'Poor', color: 'text-orange-400' };
    return { label: 'Quarantined', color: 'text-red-400' };
  };

  const trustLevel = getTrustLevel(trustScore);

  const getEventIcon = (event) => {
    const icons = {
      job_success: '✓',
      job_failure: '✕',
      malicious: '⚠',
      reward: '↑',
      punish: '↓',
    };
    return icons[event] || '•';
  };

  const getEventColor = (event) => {
    const colors = {
      job_success: 'text-green-400',
      job_failure: 'text-red-400',
      malicious: 'text-red-600',
      reward: 'text-green-400',
      punish: 'text-red-400',
    };
    return colors[event] || 'text-gray-400';
  };

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-3xl font-bold text-white">Trust & Reputation</h2>

      {/* Trust Score Display */}
      <div className="bg-black border border-gray-800 rounded p-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="text-gray-400 text-sm mb-2">Current Trust Score</div>
            <div className="flex items-baseline gap-3">
              <span className="text-6xl font-bold text-white">
                {(trustScore * 100).toFixed(1)}
              </span>
              <span className="text-2xl text-gray-400">%</span>
            </div>
            <div className={`text-lg font-medium ${trustLevel.color} mt-2`}>
              {trustLevel.label}
            </div>
          </div>

          {/* Trust Circle */}
          <div className="relative w-48 h-48">
            <svg className="w-full h-full transform -rotate-90">
              <circle
                cx="96"
                cy="96"
                r="80"
                stroke="currentColor"
                strokeWidth="12"
                fill="none"
                className="text-gray-800"
              />
              <circle
                cx="96"
                cy="96"
                r="80"
                stroke="currentColor"
                strokeWidth="12"
                fill="none"
                strokeDasharray={`${trustScore * 502.65} 502.65`}
                className={trustLevel.color}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className={`text-3xl font-bold ${trustLevel.color}`}>
                  {(trustScore * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Trust Progress Bar */}
        <div className="w-full bg-gray-900 rounded-full h-4 overflow-hidden">
          <div
            className={`h-full ${trustLevel.color.replace('text', 'bg')} transition-all duration-500`}
            style={{ width: `${trustScore * 100}%` }}
          ></div>
        </div>

        {/* Quarantine Warning */}
        {agentState.quarantined && (
          <div className="mt-4 bg-red-900 bg-opacity-20 border border-red-800 rounded p-4">
            <div className="flex items-center gap-2">
              <span className="text-red-400 text-xl">⚠</span>
              <div className="text-red-400 font-medium">
                Node is currently quarantined due to low trust score
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Reputation Statistics */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-black border border-gray-800 p-6 rounded">
          <div className="text-gray-400 text-sm mb-2">Success Events</div>
          <div className="text-3xl font-bold text-green-400">
            {reputation.success_count || 0}
          </div>
        </div>
        <div className="bg-black border border-gray-800 p-6 rounded">
          <div className="text-gray-400 text-sm mb-2">Failure Events</div>
          <div className="text-3xl font-bold text-red-400">
            {reputation.failure_count || 0}
          </div>
        </div>
        <div className="bg-black border border-gray-800 p-6 rounded">
          <div className="text-gray-400 text-sm mb-2">Total Events</div>
          <div className="text-3xl font-bold text-white">
            {(reputation.success_count || 0) + (reputation.failure_count || 0)}
          </div>
        </div>
      </div>

      {/* Reputation Events Timeline */}
      <div className="bg-black border border-gray-800 rounded p-6">
        <h3 className="text-xl font-bold text-white mb-4">Reputation Events</h3>
        <div className="space-y-3">
          {reputationEvents.length === 0 ? (
            <div className="text-center text-gray-500 py-8">No reputation events yet</div>
          ) : (
            reputationEvents.map((event, index) => (
              <div
                key={index}
                className="border border-gray-800 p-4 rounded"
              >
                <div className="flex justify-between items-start">
                  <div className="flex items-start gap-3">
                    <div className={`text-2xl ${getEventColor(event.event)}`}>
                      {getEventIcon(event.event)}
                    </div>
                    <div>
                      <div className="text-white font-medium">{event.event.replace(/_/g, ' ').toUpperCase()}</div>
                      <div className="text-gray-400 text-sm">{event.reason}</div>
                      {event.job_id && (
                        <div className="text-gray-500 text-xs font-mono mt-1">{event.job_id}</div>
                      )}
                      {event.timestamp && (
                        <div className="text-gray-600 text-xs mt-1">
                          {new Date(event.timestamp * 1000).toLocaleString()}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-lg font-bold ${
                      event.delta > 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {event.delta > 0 ? '+' : ''}{(event.delta * 100).toFixed(1)}%
                    </div>
                    {event.new_score !== undefined && (
                      <div className="text-gray-500 text-sm">
                        Score: {(event.new_score * 100).toFixed(1)}%
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Watchdog Stats */}
      {agentState.watchdog_stats && (
        <div className="bg-black border border-gray-800 rounded p-6">
          <h3 className="text-xl font-bold text-white mb-4">Watchdog Statistics</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="border border-gray-800 p-4 rounded">
              <div className="text-gray-400 text-sm mb-1">Quarantined Peers</div>
              <div className="text-2xl font-bold text-orange-400">
                {agentState.watchdog_stats.quarantined_count || 0}
              </div>
            </div>
            <div className="border border-gray-800 p-4 rounded">
              <div className="text-gray-400 text-sm mb-1">Blacklisted Peers</div>
              <div className="text-2xl font-bold text-red-400">
                {agentState.watchdog_stats.blacklisted_count || 0}
              </div>
            </div>
            <div className="border border-gray-800 p-4 rounded">
              <div className="text-gray-400 text-sm mb-1">Warnings Issued</div>
              <div className="text-2xl font-bold text-yellow-400">
                {agentState.watchdog_stats.warnings_count || 0}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Trust;
