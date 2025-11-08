import { useState } from 'react';

const Bidding = ({ agentState }) => {
  const [selectedAuction, setSelectedAuction] = useState(null);

  if (!agentState) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400">Waiting for agent connection...</div>
      </div>
    );
  }

  // Mock bidding data - in real implementation this would come from agentState
  const activeAuctions = agentState.active_auctions || [];
  const myBids = agentState.my_bids || [];
  const wonBids = agentState.won_bids || [];
  const lostBids = agentState.lost_bids || [];

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-3xl font-bold text-white">Bidding & Auctions</h2>

      {/* Bidding Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-black border border-gray-800 p-4 rounded">
          <div className="text-gray-400 text-sm mb-1">Active Auctions</div>
          <div className="text-2xl font-bold text-white">{activeAuctions.length}</div>
        </div>
        <div className="bg-black border border-gray-800 p-4 rounded">
          <div className="text-gray-400 text-sm mb-1">My Bids</div>
          <div className="text-2xl font-bold text-white">{myBids.length}</div>
        </div>
        <div className="bg-black border border-gray-800 p-4 rounded">
          <div className="text-gray-400 text-sm mb-1">Won</div>
          <div className="text-2xl font-bold text-green-400">{wonBids.length}</div>
        </div>
        <div className="bg-black border border-gray-800 p-4 rounded">
          <div className="text-gray-400 text-sm mb-1">Lost</div>
          <div className="text-2xl font-bold text-red-400">{lostBids.length}</div>
        </div>
      </div>

      {/* Active Auctions */}
      <div className="bg-black border border-gray-800 rounded p-6">
        <h3 className="text-xl font-bold text-white mb-4">Active Auctions</h3>
        <div className="space-y-3">
          {activeAuctions.length === 0 ? (
            <div className="text-center text-gray-500 py-8">No active auctions</div>
          ) : (
            activeAuctions.map((auction, index) => (
              <div
                key={auction.job_id || index}
                className="border border-gray-800 p-4 rounded hover:border-gray-700 cursor-pointer transition-colors"
                onClick={() => setSelectedAuction(auction)}
              >
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <div className="text-white font-mono text-sm">{auction.job_id}</div>
                    <div className="text-gray-400 text-sm">{auction.job_type}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-white font-bold">{auction.payment} AC</div>
                    <div className="text-gray-400 text-sm">
                      {auction.bids_count || 0} bids
                    </div>
                  </div>
                </div>
                {auction.highest_bid && (
                  <div className="mt-2 text-sm">
                    <span className="text-gray-400">Highest Bid:</span>
                    <span className="text-white ml-2">
                      {(auction.highest_bid.score * 100).toFixed(0)}% by {auction.highest_bid.node_id?.substring(0, 8)}
                    </span>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* My Bids */}
      <div className="bg-black border border-gray-800 rounded p-6">
        <h3 className="text-xl font-bold text-white mb-4">My Bids</h3>
        <div className="space-y-3">
          {myBids.length === 0 ? (
            <div className="text-center text-gray-500 py-8">No active bids</div>
          ) : (
            myBids.map((bid, index) => (
              <div
                key={bid.job_id || index}
                className="border border-gray-800 p-4 rounded"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <div className="text-white font-mono text-sm">{bid.job_id}</div>
                    <div className="text-gray-400 text-sm">{bid.job_type}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-white">Score: {(bid.score * 100).toFixed(1)}%</div>
                    <div className="text-gray-400 text-sm">Stake: {bid.stake} AC</div>
                  </div>
                </div>
                {bid.rank && (
                  <div className="mt-2">
                    <span className={`inline-block px-2 py-1 rounded text-xs ${
                      bid.rank === 1 ? 'bg-green-900 text-green-200' : 'bg-gray-800 text-gray-300'
                    }`}>
                      Rank #{bid.rank}
                    </span>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Auction Details Modal */}
      {selectedAuction && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" onClick={() => setSelectedAuction(null)}>
          <div className="bg-black border border-gray-800 rounded-lg p-6 max-w-2xl w-full m-4 max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-white">Auction Details</h3>
              <button className="text-gray-400 hover:text-white text-2xl" onClick={() => setSelectedAuction(null)}>×</button>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-400">Job ID</span>
                <span className="text-white font-mono">{selectedAuction.job_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Type</span>
                <span className="text-white">{selectedAuction.job_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Payment</span>
                <span className="text-white">{selectedAuction.payment} AC</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Total Bids</span>
                <span className="text-white">{selectedAuction.bids_count || 0}</span>
              </div>
              {selectedAuction.bids && selectedAuction.bids.length > 0 && (
                <div className="mt-4">
                  <div className="text-gray-400 mb-2">All Bids:</div>
                  <div className="space-y-2">
                    {selectedAuction.bids.map((bid, idx) => (
                      <div key={idx} className="border border-gray-800 p-3 rounded">
                        <div className="flex justify-between">
                          <span className="text-white font-mono text-sm">{bid.node_id?.substring(0, 12)}</span>
                          <span className="text-white">{(bid.score * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Bidding;
