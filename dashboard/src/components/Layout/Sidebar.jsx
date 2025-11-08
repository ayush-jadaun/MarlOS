const Sidebar = ({ activeView, setActiveView, connected }) => {
  const menuItems = [
    { id: 'overview', label: 'Overview', icon: '■' },
    { id: 'network', label: 'Network', icon: '●' },
    { id: 'jobs', label: 'Jobs', icon: '▣' },
    { id: 'bidding', label: 'Bidding', icon: '◈' },
    { id: 'wallet', label: 'Wallet', icon: '◆' },
    { id: 'trust', label: 'Trust', icon: '◇' },
    { id: 'metrics', label: 'Metrics', icon: '▤' },
  ];

  return (
    <div className="w-64 h-screen bg-black border-r border-gray-800 flex flex-col">
      <div className="p-6 border-b border-gray-800">
        <h1 className="text-2xl font-bold text-white mb-4">SwarmOPS</h1>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400' : 'bg-red-400'} animate-pulse`}></span>
          <span className="text-sm text-gray-400">{connected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {menuItems.map((item) => (
          <button
            key={item.id}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded transition-all ${
              activeView === item.id
                ? 'bg-white text-black'
                : 'text-gray-400 hover:text-white hover:bg-gray-900'
            }`}
            onClick={() => setActiveView(item.id)}
          >
            <span className="text-lg">{item.icon}</span>
            <span className="font-medium">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-800">
        <div className="text-xs text-gray-600 text-center">v0.1.0</div>
      </div>
    </div>
  );
};

export default Sidebar;
