import { useState } from 'react';

const Network = ({ agentState }) => {
  const [selectedPeer, setSelectedPeer] = useState(null);

  if (!agentState) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400">Waiting for agent connection...</div>
      </div>
    );
  }

  // Get peer data from agentState - NO HARDCODED DATA
  const peers = agentState.peer_list || [];
  const connectedPeers = peers.filter(p => p.connected !== false);
  const disconnectedPeers = peers.filter(p => p.connected === false);

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-3xl font-bold text-white">Network Topology</h2>

      {/* Network Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-black border border-gray-800 p-4 rounded">
          <div className="text-gray-400 text-sm mb-1">Total Peers</div>
          <div className="text-2xl font-bold text-white">{agentState.peers || 0}</div>
        </div>
        <div className="bg-black border border-gray-800 p-4 rounded">
          <div className="text-gray-400 text-sm mb-1">Connected</div>
          <div className="text-2xl font-bold text-green-400">{connectedPeers.length}</div>
        </div>
        <div className="bg-black border border-gray-800 p-4 rounded">
          <div className="text-gray-400 text-sm mb-1">Disconnected</div>
          <div className="text-2xl font-bold text-red-400">{disconnectedPeers.length}</div>
        </div>
        {agentState.watchdog_stats && (
          <div className="bg-black border border-gray-800 p-4 rounded">
            <div className="text-gray-400 text-sm mb-1">Quarantined</div>
            <div className="text-2xl font-bold text-orange-400">{agentState.watchdog_stats.quarantined_count || 0}</div>
          </div>
        )}
      </div>

      {/* Network Visualization */}
      <div className="bg-black border border-gray-800 rounded p-6">
        <h3 className="text-xl font-bold text-white mb-4">Network Graph</h3>
        <div className="relative h-96 flex items-center justify-center">
          {/* Central Node (This Agent) */}
          <div className="absolute z-10">
            <div className="bg-white text-black rounded-full w-24 h-24 flex flex-col items-center justify-center border-4 border-gray-800">
              <div className="text-3xl">●</div>
              <div className="text-xs font-bold">
                {agentState.node_name || agentState.node_id?.substring(0, 8)}
              </div>
              <div className="text-xs">{(agentState.trust_score * 100).toFixed(0)}%</div>
            </div>
          </div>

          {/* Connected Peers in a Circle */}
          {peers.length === 0 ? (
            <div className="text-gray-500 text-center">No peers discovered yet</div>
          ) : (
            <div className="absolute w-full h-full">
              {peers.map((peer, index) => {
                const angle = (index * 360) / peers.length;
                const radius = 140;
                const x = Math.cos((angle * Math.PI) / 180) * radius;
                const y = Math.sin((angle * Math.PI) / 180) * radius;

                return (
                  <div
                    key={peer.node_id || index}
                    className="absolute"
                    style={{
                      left: `calc(50% + ${x}px)`,
                      top: `calc(50% + ${y}px)`,
                      transform: 'translate(-50%, -50%)',
                    }}
                  >
                    <div
                      className={`rounded-full w-16 h-16 flex flex-col items-center justify-center border-2 cursor-pointer transition-all ${
                        peer.connected !== false
                          ? 'bg-green-900 border-green-400 hover:scale-110'
                          : 'bg-red-900 border-red-400 hover:scale-110'
                      } ${peer.quarantined ? 'border-yellow-500' : ''}`}
                      onClick={() => setSelectedPeer(peer)}
                    >
                      <div className="text-xl">{peer.connected !== false ? '●' : '○'}</div>
                      <div className="text-xs font-mono">{peer.node_id?.substring(0, 6)}</div>
                      {peer.trust_score !== undefined && (
                        <div className="text-xs">{(peer.trust_score * 100).toFixed(0)}%</div>
                      )}
                    </div>
                    {/* Connection Line */}
                    <svg className="absolute top-1/2 left-1/2 -z-10" style={{ width: `${radius + 50}px`, height: `${radius + 50}px`, transform: 'translate(-50%, -50%)' }}>
                      <line
                        x1={radius + 25}
                        y1={radius + 25}
                        x2={radius + 25 - x}
                        y2={radius + 25 - y}
                        stroke={peer.connected !== false ? '#4ade80' : '#f87171'}
                        strokeWidth="2"
                        opacity="0.3"
                      />
                    </svg>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Peer Lists */}
      <div className="grid grid-cols-2 gap-4">
        {/* Connected Peers List */}
        <div className="bg-black border border-gray-800 rounded p-6">
          <h3 className="text-xl font-bold text-white mb-4">Connected Peers ({connectedPeers.length})</h3>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {connectedPeers.length === 0 ? (
              <div className="text-center text-gray-500 py-8">No connected peers</div>
            ) : (
              connectedPeers.map((peer, index) => (
                <div
                  key={peer.node_id || index}
                  className="border border-gray-800 p-3 rounded hover:border-gray-700 cursor-pointer transition-colors"
                  onClick={() => setSelectedPeer(peer)}
                >
                  <div className="flex items-center gap-3">
                    <div className="text-green-400 text-xl">●</div>
                    <div className="flex-1">
                      <div className="text-white font-mono text-sm">{peer.node_id || `Peer ${index + 1}`}</div>
                      <div className="text-gray-400 text-xs">
                        {peer.ip && <span>{peer.ip}:{peer.port} • </span>}
                        {peer.trust_score !== undefined && (
                          <span>Trust: {(peer.trust_score * 100).toFixed(0)}%</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Disconnected Peers List */}
        <div className="bg-black border border-gray-800 rounded p-6">
          <h3 className="text-xl font-bold text-white mb-4">Disconnected Peers ({disconnectedPeers.length})</h3>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {disconnectedPeers.length === 0 ? (
              <div className="text-center text-gray-500 py-8">No disconnected peers</div>
            ) : (
              disconnectedPeers.map((peer, index) => (
                <div
                  key={peer.node_id || index}
                  className="border border-gray-800 p-3 rounded hover:border-gray-700 cursor-pointer transition-colors"
                  onClick={() => setSelectedPeer(peer)}
                >
                  <div className="flex items-center gap-3">
                    <div className="text-red-400 text-xl">○</div>
                    <div className="flex-1">
                      <div className="text-white font-mono text-sm">{peer.node_id || `Peer ${index + 1}`}</div>
                      <div className="text-gray-400 text-xs">
                        {peer.last_seen && (
                          <span>Last seen: {new Date(peer.last_seen * 1000).toLocaleTimeString()}</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Selected Peer Details Modal */}
      {selectedPeer && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" onClick={() => setSelectedPeer(null)}>
          <div className="bg-black border border-gray-800 rounded-lg p-6 max-w-2xl w-full m-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-white">Peer Details</h3>
              <button className="text-gray-400 hover:text-white text-2xl" onClick={() => setSelectedPeer(null)}>×</button>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-400">Node ID</span>
                <span className="text-white font-mono">{selectedPeer.node_id}</span>
              </div>
              {selectedPeer.public_key && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Public Key</span>
                  <span className="text-white font-mono text-xs">{selectedPeer.public_key.substring(0, 32)}...</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-400">Status</span>
                <span className={`px-2 py-1 rounded text-xs ${selectedPeer.connected !== false ? 'bg-green-900 text-green-200' : 'bg-red-900 text-red-200'}`}>
                  {selectedPeer.connected !== false ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              {selectedPeer.trust_score !== undefined && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Trust Score</span>
                  <span className="text-white">{(selectedPeer.trust_score * 100).toFixed(1)}%</span>
                </div>
              )}
              {selectedPeer.capabilities && selectedPeer.capabilities.length > 0 && (
                <div>
                  <div className="text-gray-400 mb-2">Capabilities</div>
                  <div className="flex flex-wrap gap-2">
                    {selectedPeer.capabilities.map((cap) => (
                      <span key={cap} className="px-2 py-1 bg-gray-900 border border-gray-800 rounded text-white text-xs">{cap}</span>
                    ))}
                  </div>
                </div>
              )}
              {selectedPeer.ip && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Address</span>
                  <span className="text-white">{selectedPeer.ip}:{selectedPeer.port}</span>
                </div>
              )}
              {selectedPeer.last_seen && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Last Seen</span>
                  <span className="text-white">{new Date(selectedPeer.last_seen * 1000).toLocaleString()}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Network;
