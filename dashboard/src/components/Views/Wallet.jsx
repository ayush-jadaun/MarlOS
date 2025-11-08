import { useState } from 'react';

const Wallet = ({ agentState }) => {
  const [filter, setFilter] = useState('all'); // all, deposit, withdraw, stake, slash

  if (!agentState) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400">Waiting for agent connection...</div>
      </div>
    );
  }

  const wallet = agentState.wallet || {};
  const transactions = agentState.transactions || [];

  const filteredTransactions = filter === 'all'
    ? transactions
    : transactions.filter(t => t.tx_type?.toLowerCase() === filter);

  const getTransactionIcon = (type) => {
    const icons = {
      deposit: '↓',
      withdraw: '↑',
      stake: '◆',
      unstake: '◇',
      slash: '✕',
      transfer: '→',
    };
    return icons[type?.toLowerCase()] || '•';
  };

  const getTransactionColor = (type) => {
    const colors = {
      deposit: 'text-green-400',
      withdraw: 'text-red-400',
      stake: 'text-yellow-400',
      unstake: 'text-blue-400',
      slash: 'text-red-600',
      transfer: 'text-gray-400',
    };
    return colors[type?.toLowerCase()] || 'text-gray-400';
  };

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-3xl font-bold text-white">Wallet & Transactions</h2>

      {/* Wallet Overview */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-black border border-gray-800 p-6 rounded">
          <div className="text-gray-400 text-sm mb-1">Available Balance</div>
          <div className="text-3xl font-bold text-white">{wallet.balance?.toFixed(2) || '0.00'}</div>
          <div className="text-gray-500 text-xs mt-1">AC</div>
        </div>
        <div className="bg-black border border-gray-800 p-6 rounded">
          <div className="text-gray-400 text-sm mb-1">Staked</div>
          <div className="text-3xl font-bold text-yellow-400">{wallet.staked?.toFixed(2) || '0.00'}</div>
          <div className="text-gray-500 text-xs mt-1">AC</div>
        </div>
        <div className="bg-black border border-gray-800 p-6 rounded">
          <div className="text-gray-400 text-sm mb-1">Total Value</div>
          <div className="text-3xl font-bold text-white">{wallet.total_value?.toFixed(2) || '0.00'}</div>
          <div className="text-gray-500 text-xs mt-1">AC</div>
        </div>
        <div className="bg-black border border-gray-800 p-6 rounded">
          <div className="text-gray-400 text-sm mb-1">Net Profit</div>
          <div className={`text-3xl font-bold ${wallet.net_profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {wallet.net_profit >= 0 ? '+' : ''}{wallet.net_profit?.toFixed(2) || '0.00'}
          </div>
          <div className="text-gray-500 text-xs mt-1">AC</div>
        </div>
      </div>

      {/* Lifetime Stats */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-black border border-gray-800 p-6 rounded">
          <div className="text-gray-400 text-sm mb-2">Lifetime Earned</div>
          <div className="text-2xl font-bold text-green-400">
            +{wallet.lifetime_earned?.toFixed(2) || '0.00'} AC
          </div>
        </div>
        <div className="bg-black border border-gray-800 p-6 rounded">
          <div className="text-gray-400 text-sm mb-2">Lifetime Spent</div>
          <div className="text-2xl font-bold text-red-400">
            -{wallet.lifetime_spent?.toFixed(2) || '0.00'} AC
          </div>
        </div>
      </div>

      {/* Transaction History */}
      <div className="bg-black border border-gray-800 rounded p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-bold text-white">Transaction History</h3>
          <div className="flex gap-2">
            <button
              className={`px-3 py-1 rounded text-sm ${filter === 'all' ? 'bg-white text-black' : 'bg-gray-800 text-gray-400'}`}
              onClick={() => setFilter('all')}
            >
              All
            </button>
            <button
              className={`px-3 py-1 rounded text-sm ${filter === 'deposit' ? 'bg-white text-black' : 'bg-gray-800 text-gray-400'}`}
              onClick={() => setFilter('deposit')}
            >
              Deposits
            </button>
            <button
              className={`px-3 py-1 rounded text-sm ${filter === 'withdraw' ? 'bg-white text-black' : 'bg-gray-800 text-gray-400'}`}
              onClick={() => setFilter('withdraw')}
            >
              Withdrawals
            </button>
            <button
              className={`px-3 py-1 rounded text-sm ${filter === 'stake' ? 'bg-white text-black' : 'bg-gray-800 text-gray-400'}`}
              onClick={() => setFilter('stake')}
            >
              Stakes
            </button>
            <button
              className={`px-3 py-1 rounded text-sm ${filter === 'slash' ? 'bg-white text-black' : 'bg-gray-800 text-gray-400'}`}
              onClick={() => setFilter('slash')}
            >
              Slashes
            </button>
          </div>
        </div>

        <div className="space-y-2">
          {filteredTransactions.length === 0 ? (
            <div className="text-center text-gray-500 py-8">No transactions to display</div>
          ) : (
            filteredTransactions.map((tx, index) => (
              <div
                key={tx.entry_id || index}
                className="border border-gray-800 p-4 rounded hover:border-gray-700 transition-colors"
              >
                <div className="flex justify-between items-start">
                  <div className="flex items-start gap-3">
                    <div className={`text-2xl ${getTransactionColor(tx.tx_type)}`}>
                      {getTransactionIcon(tx.tx_type)}
                    </div>
                    <div>
                      <div className="text-white font-medium">{tx.tx_type?.toUpperCase()}</div>
                      <div className="text-gray-400 text-sm">{tx.reason}</div>
                      {tx.job_id && (
                        <div className="text-gray-500 text-xs font-mono mt-1">{tx.job_id}</div>
                      )}
                      {tx.timestamp && (
                        <div className="text-gray-600 text-xs mt-1">
                          {new Date(tx.timestamp * 1000).toLocaleString()}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-lg font-bold ${
                      tx.amount > 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {tx.amount > 0 ? '+' : ''}{tx.amount?.toFixed(2)} AC
                    </div>
                    {tx.balance_after !== undefined && (
                      <div className="text-gray-500 text-sm">
                        Balance: {tx.balance_after.toFixed(2)} AC
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default Wallet;
