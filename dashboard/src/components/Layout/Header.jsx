const Header = ({ agentState }) => {
  if (!agentState) return null;

  return (
    <div className="bg-black border-b border-gray-800 px-6 py-4">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-white">
            Agent: {agentState.node_name || agentState.node_id?.substring(0, 12)}
          </h2>
          <span className="text-xs text-gray-500 font-mono">{agentState.node_id}</span>
        </div>

        <div className="flex gap-6">
          <div className="text-right">
            <div className="text-xs text-gray-400">Trust</div>
            <div className="text-sm font-bold text-white">
              {(agentState.trust_score * 100).toFixed(1)}%
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-400">Balance</div>
            <div className="text-sm font-bold text-white">
              {agentState.wallet?.balance?.toFixed(2)} AC
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-400">Peers</div>
            <div className="text-sm font-bold text-white">
              {agentState.peers || 0}
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-400">Jobs</div>
            <div className="text-sm font-bold text-white">
              {agentState.active_jobs || 0} Active
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Header;
