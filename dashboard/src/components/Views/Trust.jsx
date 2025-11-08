import { useState } from 'react';

const Trust = ({ agentState }) => {
  const [showAllEvents, setShowAllEvents] = useState(false);

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
  const watchdogStats = agentState.watchdog_stats || {};

  const successCount = reputation.success_count || 0;
  const failureCount = reputation.failure_count || 0;
  const totalEvents = reputation.total_events || 0;

  const getTrustLevel = (score) => {
    if (score >= 0.8) return { label: 'Excellent', color: 'text-green-400', bgColor: 'bg-green-400' };
    if (score >= 0.6) return { label: 'Good', color: 'text-blue-400', bgColor: 'bg-blue-400' };
    if (score >= 0.4) return { label: 'Fair', color: 'text-yellow-400', bgColor: 'bg-yellow-400' };
    if (score >= 0.2) return { label: 'Poor', color: 'text-orange-400', bgColor: 'bg-orange-400' };
    return { label: 'Quarantined', color: 'text-red-400', bgColor: 'bg-red-400' };
  };

  const trustLevel = getTrustLevel(trustScore);

  const getEventIcon = (event) => {
    const icons = {
      success: '✓',
      late_success: '✓',
      failure: '✕',
      timeout: '⏱',
      malicious: '⚠',
      reward: '↑',
      punish: '↓',
    };
    return icons[event] || '•';
  };

  const getEventColor = (event) => {
    const colors = {
      success: 'text-green-400',
      late_success: 'text-green-400',
      failure: 'text-red-400',
      timeout: 'text-orange-400',
      malicious: 'text-red-600',
      reward: 'text-green-400',
      punish: 'text-red-400',
    };
    return colors[event] || 'text-gray-400';
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp * 1000);
    return date.toLocaleString();
  };

  const timeAgo = (timestamp) => {
    if (!timestamp) return 'N/A';
    const seconds = Math.floor(Date.now() / 1000 - timestamp);
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  const successRate = totalEvents > 0 ? ((successCount / totalEvents) * 100).toFixed(1) : 0;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-white">Trust & Reputation</h2>
        
        {/* Stats Summary */}
        <div className="text-sm text-gray-400 text-right">
          <div>Total Events: {totalEvents}</div>
          <div className="text-green-400">Success: {successCount}</div>
          <div className="text-red-400">Failures: {failureCount}</div>
        </div>
      </div>

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
            className={`h-full ${trustLevel.bgColor} transition-all duration-500`}
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
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-black border border-gray-800 p-6 rounded">
          <div className="text-gray-400 text-sm mb-2">Success Events</div>
          <div className="text-3xl font-bold text-green-400">
            {successCount}
          </div>
        </div>
        <div className="bg-black border border-gray-800 p-6 rounded">
          <div className="text-gray-400 text-sm mb-2">Failure Events</div>
          <div className="text-3xl font-bold text-red-400">
            {failureCount}
          </div>
        </div>
        <div className="bg-black border border-gray-800 p-6 rounded">
          <div className="text-gray-400 text-sm mb-2">Total Events</div>
          <div className="text-3xl font-bold text-white">
            {totalEvents}
          </div>
        </div>
        <div className="bg-black border border-gray-800 p-6 rounded">
          <div className="text-gray-400 text-sm mb-2">Success Rate</div>
          <div className="text-3xl font-bold text-blue-400">
            {successRate}%
          </div>
        </div>
      </div>

      {/* Success Rate Visualization */}
      {totalEvents > 0 && (
        <div className="bg-black border border-gray-800 rounded p-6">
          <h3 className="text-xl font-bold text-white mb-4">Performance Breakdown</h3>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-green-400">Success: {successCount}</span>
                <span className="text-red-400">Failure: {failureCount}</span>
              </div>
              <div className="w-full bg-gray-900 rounded-full h-6 overflow-hidden flex">
                <div
                  className="bg-green-500 h-full transition-all duration-500"
                  style={{ width: `${(successCount / totalEvents) * 100}%` }}
                />
                <div
                  className="bg-red-500 h-full transition-all duration-500"
                  style={{ width: `${(failureCount / totalEvents) * 100}%` }}
                />
              </div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-white">{successRate}%</div>
              <div className="text-xs text-gray-400">Success</div>
            </div>
          </div>
        </div>
      )}

      {/* Reputation Events Timeline */}
      <div className="bg-black border border-gray-800 rounded p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-white">Reputation Events</h3>
          {reputationEvents.length > 10 && (
            <button
              onClick={() => setShowAllEvents(!showAllEvents)}
              className="text-sm text-blue-400 hover:text-blue-300"
            >
              {showAllEvents ? 'Show Less' : `Show All (${reputationEvents.length})`}
            </button>
          )}
        </div>
        <div className="space-y-3 max-h-[600px] overflow-y-auto">
          {reputationEvents.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              No reputation events yet. Complete jobs to see events here.
            </div>
          ) : (
            (showAllEvents ? reputationEvents : reputationEvents.slice(-10))
              .slice()
              .reverse()
              .map((event, index) => (
                <div
                  key={index}
                  className={`border p-4 rounded ${
                    event.event === 'success' || event.event === 'late_success'
                      ? 'border-green-900 bg-green-950 bg-opacity-20'
                      : 'border-red-900 bg-red-950 bg-opacity-20'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex items-start gap-3 flex-1">
                      <div className={`text-2xl ${getEventColor(event.event)}`}>
                        {getEventIcon(event.event)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <div className="text-white font-medium">
                            {event.event.replace(/_/g, ' ').toUpperCase()}
                          </div>
                          <div className="text-gray-500 text-xs">
                            {timeAgo(event.timestamp)}
                          </div>
                        </div>
                        <div className="text-gray-400 text-sm mt-1">{event.reason}</div>
                        {event.job_id && (
                          <div className="text-gray-500 text-xs font-mono mt-1">
                            Job: {event.job_id}
                          </div>
                        )}
                        <div className="text-gray-600 text-xs mt-1">
                          {formatTimestamp(event.timestamp)}
                        </div>
                      </div>
                    </div>
                    <div className="text-right ml-4">
                      <div className={`text-lg font-bold ${
                        event.delta > 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {event.delta > 0 ? '+' : ''}{(event.delta * 100).toFixed(2)}%
                      </div>
                      {event.new_score !== undefined && (
                        <div className="text-gray-500 text-sm">
                          → {(event.new_score * 100).toFixed(1)}%
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
      <div className="bg-black border border-gray-800 rounded p-6">
        <h3 className="text-xl font-bold text-white mb-4">Watchdog Statistics</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="border border-gray-800 p-4 rounded">
            <div className="text-gray-400 text-sm mb-1">Quarantined Peers</div>
            <div className="text-2xl font-bold text-orange-400">
              {watchdogStats.quarantined_peers || 0}
            </div>
          </div>
          <div className="border border-gray-800 p-4 rounded">
            <div className="text-gray-400 text-sm mb-1">Monitored Peers</div>
            <div className="text-2xl font-bold text-blue-400">
              {watchdogStats.monitored_peers || 0}
            </div>
          </div>
          <div className="border border-gray-800 p-4 rounded">
            <div className="text-gray-400 text-sm mb-1">Total Failures</div>
            <div className="text-2xl font-bold text-yellow-400">
              {watchdogStats.total_failures_tracked || 0}
            </div>
          </div>
        </div>
      </div>

      {/* Trust Score History (Simplified) */}
      {reputationEvents.length > 0 && (
        <div className="bg-black border border-gray-800 rounded p-6">
          <h3 className="text-xl font-bold text-white mb-4">Trust Score Trend</h3>
          <div className="flex items-end gap-2 h-32">
            {reputationEvents.slice(-20).map((event, index) => {
              const height = (event.new_score || 0) * 100;
              const isPositive = event.delta >= 0;
              return (
                <div key={index} className="flex-1 flex flex-col justify-end">
                  <div
                    className={`w-full rounded-t transition-all ${
                      isPositive ? 'bg-green-500' : 'bg-red-500'
                    }`}
                    style={{ height: `${height}%` }}
                    title={`${(event.new_score * 100).toFixed(1)}%`}
                  />
                </div>
              );
            })}
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-2">
            <span>Older</span>
            <span>Recent</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default Trust;