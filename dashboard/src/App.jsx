import { useState } from 'react';
import { useMultiAgentWebSocket } from './hooks/useMultiAgentWebSocket';
import Sidebar from './components/Layout/Sidebar';
import Header from './components/Layout/Header';
import Overview from './components/Views/Overview';
import Network from './components/Views/Network';
import Jobs from './components/Views/Jobs';
import Bidding from './components/Views/Bidding';
import Wallet from './components/Views/Wallet';
import Trust from './components/Views/Trust';
import Metrics from './components/Views/Metrics';

function App() {
  const [activeView, setActiveView] = useState('overview');
  const [selectedAgent, setSelectedAgent] = useState(8081); // Default to first agent
  const { agentsState, connections, connectedCount, totalAgents, error } = useMultiAgentWebSocket();

  // Get the currently selected agent's state
  const agentState = agentsState[selectedAgent] || null;
  const connected = connections[selectedAgent] || false;

  const renderView = () => {
    switch (activeView) {
      case 'overview':
        return <Overview agentState={agentState} />;
      case 'network':
        return <Network agentState={agentState} />;
      case 'jobs':
        return <Jobs agentState={agentState} />;
      case 'bidding':
        return <Bidding agentState={agentState} />;
      case 'wallet':
        return <Wallet agentState={agentState} />;
      case 'trust':
        return <Trust agentState={agentState} />;
      case 'metrics':
        return <Metrics agentState={agentState} />;
      default:
        return <Overview agentState={agentState} />;
    }
  };

  return (
    <div className="flex h-screen bg-black text-white overflow-hidden">
      <Sidebar activeView={activeView} setActiveView={setActiveView} connected={connected} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header agentState={agentState} />

        {/* Agent Selector */}
        <div className="bg-zinc-900 border-b border-zinc-800 px-6 py-3">
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-400">Select Agent:</span>
            <div className="flex gap-2">
              {[8081, 8082, 8083].map((port, index) => {
                const isConnected = connections[port];
                const isSelected = selectedAgent === port;
                const state = agentsState[port];

                return (
                  <button
                    key={port}
                    onClick={() => setSelectedAgent(port)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      isSelected
                        ? 'bg-blue-600 text-white'
                        : isConnected
                        ? 'bg-zinc-800 text-white hover:bg-zinc-700'
                        : 'bg-zinc-800 text-gray-500'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${
                        isConnected ? 'bg-green-500' : 'bg-red-500'
                      }`} />
                      <span>
                        {state?.node_name || `Agent ${index + 1}`}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
            <div className="ml-auto text-sm text-gray-400">
              {connectedCount}/{totalAgents} agents connected
            </div>
          </div>
        </div>

        <main className="flex-1 overflow-y-auto">
          {error && (
            <div className="bg-red-900 border-l-4 border-red-500 text-red-200 p-4 m-4">
              <p className="font-bold">Connection Error</p>
              <p>{error}</p>
            </div>
          )}
          {!agentState && connected && (
            <div className="flex items-center justify-center h-full">
              <div className="text-gray-400">Loading agent data...</div>
            </div>
          )}
          {!connected && (
            <div className="flex items-center justify-center h-full">
              <div className="text-gray-400">Connecting to agent...</div>
            </div>
          )}
          {agentState && renderView()}
        </main>
      </div>
    </div>
  );
}

export default App;
