"""
Bidding Auction System
Manages competitive bidding for jobs
"""
import asyncio
import time
import random
from typing import Dict, Optional, List, Callable
from dataclasses import dataclass

from ..p2p.protocol import MessageType
from ..schema.schema import Bid


class BiddingAuction:
    """
    Manages bidding wars for jobs with consensus and security features
    """

    def __init__(self, node_id: str, p2p_node=None):
        self.node_id = node_id
        self.p2p_node = p2p_node  # Reference to P2P node for consensus

        # Active auctions (job_id -> list of bids)
        self.active_auctions: Dict[str, List[Bid]] = {}

        # My bids
        self.my_bids: Dict[str, Bid] = {}  # job_id -> my_bid

        # Track if we claimed victory (to detect conflicts during grace period)
        self.claimed_jobs: Dict[str, float] = {}  # job_id -> my_score

        # Auction config (adjusted for Docker networking latency)
        self.bidding_window = 2.0  # seconds (reduced - bids sent early)
        self.backoff_base = 0.1  # base delay (minimal - send bids fast)
        self.backoff_max = 0.3  # max delay (send bids fast)

        # Track message latencies for dynamic grace period
        self.message_latencies: List[float] = []

        # Claim confirmations (for quorum)
        self.claim_confirmations: Dict[str, set] = {}  # job_id -> set of confirming nodes

        # Coordinator reference (injected from main agent)
        self.coordinator = None

        # Track coordinator assignments per job
        self.job_coordinators: Dict[str, str] = {}  # job_id -> coordinator_node_id

        # NON-BLOCKING REDESIGN: Track auction completion callbacks
        self.auction_callbacks: Dict[str, Callable] = {}  # job_id -> callback(won: bool)
    
    async def place_bid_nonblocking(self,
                                    job: dict,
                                    score: float,
                                    stake_amount: float,
                                    estimated_time: float,
                                    p2p_node,
                                    callback: Callable = None):
        """
        NON-BLOCKING: Place a bid and return immediately
        Launches background task to handle backoff, bid sending, and auction monitoring

        Args:
            callback: Called with (won: bool) when auction completes
        """
        job_id = job['job_id']

        # CRITICAL: Prevent duplicate auctions for the same job
        if job_id in self.my_bids:
            print(f"[AUCTION] ⏭️  Already bidding on {job_id} - ignoring duplicate call")
            if callback:
                callback(False)
            return

        # Initialize auction tracking for this job
        if job_id not in self.active_auctions:
            self.active_auctions[job_id] = []
            print(f"[AUCTION] Initialized auction for {job_id}")

        # Mark that we're bidding IMMEDIATELY to prevent race conditions
        # Create a placeholder bid that will be updated when bid is sent
        placeholder_bid = Bid(
            job_id=job_id,
            node_id=self.node_id,
            score=score,
            stake_amount=stake_amount,
            estimated_time=estimated_time,
            timestamp=time.time()
        )
        self.my_bids[job_id] = placeholder_bid

        # Calculate absolute bidding deadline (from job timestamp, not local receive time)
        job_timestamp = job.get('timestamp', time.time())
        auction_deadline = job_timestamp + self.bidding_window
        time_until_deadline = auction_deadline - time.time()

        # If we're already past the deadline (due to network delays), skip bidding
        if time_until_deadline <= 0:
            print(f"[AUCTION] Too late to bid on {job_id} (deadline passed)")
            if callback:
                callback(False)
            return

        # Calculate backoff (higher score = shorter delay)
        delay = self._calculate_backoff(score)

        # Don't delay longer than time remaining
        delay = min(delay, time_until_deadline - 0.5)  # Leave 0.5s for processing

        print(f"[AUCTION] Bidding on {job_id} with score {score:.3f}, delay {delay:.2f}s (deadline in {time_until_deadline:.2f}s)")

        # NON-BLOCKING: Store callback and launch background task immediately
        if callback:
            self.auction_callbacks[job_id] = callback

        # Launch background task that handles: delay, coordinator announcement, bid send, and monitoring
        # This returns control immediately to the caller
        asyncio.create_task(self._bid_and_monitor_auction(
            job=job,
            job_id=job_id,
            score=score,
            stake_amount=stake_amount,
            estimated_time=estimated_time,
            auction_deadline=auction_deadline,
            delay=delay,
            p2p_node=p2p_node
        ))

        print(f"✅ [AUCTION] Background bidding task launched for {job_id} (non-blocking)")

    async def _bid_and_monitor_auction(self,
                                       job: dict,
                                       job_id: str,
                                       score: float,
                                       stake_amount: float,
                                       estimated_time: float,
                                       auction_deadline: float,
                                       delay: float,
                                       p2p_node):
        """
        Background task: Handles backoff delay, coordinator announcement, bid broadcast, and auction monitoring
        This runs independently without blocking the main message receiver
        """
        # COORDINATOR ELECTION: All nodes independently elect same coordinator
        if self.coordinator:
            coordinator_id = self.coordinator.elect_coordinator_for_job(job_id)
            self.job_coordinators[job_id] = coordinator_id

            am_coordinator = (coordinator_id == self.node_id)
            print(f"[COORDINATOR] Elected {coordinator_id} for {job_id} (I am coordinator: {am_coordinator})")

            # If I'm the coordinator, announce it
            if am_coordinator:
                await p2p_node.broadcast_message(
                    MessageType.AUCTION_COORDINATE,
                    job_id=job_id,
                    coordinator_id=self.node_id,
                    bid_deadline=auction_deadline
                )
        else:
            # No coordinator system - fall back to decentralized auction
            coordinator_id = None
            am_coordinator = False

        # Wait for backoff delay (allows high-score bids to go first)
        await asyncio.sleep(delay)

        # Update our bid timestamp to reflect actual bid time
        bid_send_time = time.time()
        self.my_bids[job_id].timestamp = bid_send_time

        # Broadcast bid
        print(f"📤 [BID SENT] {self.node_id} → ALL: job={job_id}, score={score:.3f} at {bid_send_time:.3f}")
        await p2p_node.broadcast_message(
            MessageType.JOB_BID,
            job_id=job_id,
            bid_score=score,
            estimated_time=estimated_time,
            stake_amount=stake_amount
        )
        print(f"✅ [BID BROADCAST] Sent to network successfully")

        # Continue with auction monitoring
        await self._monitor_auction(
            job_id=job_id,
            auction_deadline=auction_deadline,
            score=score,
            stake_amount=stake_amount,
            p2p_node=p2p_node
        )

    async def _monitor_auction(self, job_id: str, auction_deadline: float, score: float, stake_amount: float, p2p_node):
        """
        Background task that monitors auction and determines winner
        This runs without blocking the message receiver
        """
        # Wait until absolute auction deadline
        time_remaining = auction_deadline - time.time()
        if time_remaining > 0:
            print(f"⏰ [AUCTION TIMER] Waiting {time_remaining:.2f}s until auction deadline...")
            await asyncio.sleep(time_remaining)
            print(f"⏰ [AUCTION DEADLINE] Auction window closed at {time.time():.3f}")

        # Buffer period to ensure all bids have propagated
        # Keep this minimal since messages process immediately now
        bid_collection_buffer = 0.5  # Just 500ms to let final messages arrive
        collection_end = time.time() + bid_collection_buffer
        print(f"⏳ [BID COLLECTION] Waiting {bid_collection_buffer:.1f}s for bid propagation...")
        print(f"   Current bids received: {len(self.active_auctions.get(job_id, []))}")

        # Poll every 0.1s to allow messages to be processed
        while time.time() < collection_end:
            await asyncio.sleep(0.1)
            current_bids = len(self.active_auctions.get(job_id, []))
            if current_bids > 0:
                print(f"   📊 Bids received so far: {current_bids}")

        print(f"✅ [BID COLLECTION] Collection period ended at {time.time():.3f}")

        # Log all received bids for debugging
        received_bids = self.active_auctions.get(job_id, [])
        print(f"[AUCTION] Received {len(received_bids)} bids from other nodes for {job_id}")
        for bid in received_bids:
            print(f"  - {bid.node_id}: score={bid.score:.3f}")

        # Determine winner - coordinator or decentralized
        coordinator_id = self.job_coordinators.get(job_id)
        am_coordinator = (coordinator_id == self.node_id) if coordinator_id else False

        winner = self._determine_winner(job_id)

        if winner == self.node_id:
            print(f"🏆 [AUCTION] WON job {job_id}!")
            print(f"   My score: {score:.3f}")
            print(f"   Competing against {len(received_bids)} other bids")

            # Mark that we claimed this job
            self.claimed_jobs[job_id] = score

            # Record fairness tracking
            if self.coordinator:
                self.coordinator.record_job_won(self.node_id)

            # Broadcast claim with quorum requirement
            claim_time = time.time()
            print(f"📤 [CLAIM SENT] Broadcasting job claim at {claim_time:.3f}")
            claim_success = await p2p_node.broadcast_reliable(
                MessageType.JOB_CLAIM,
                job_id=job_id,
                winner_node_id=self.node_id,
                backup_node_id=self._select_backup(job_id),
                stake_amount=stake_amount,
                winning_score=score
            )

            if not claim_success:
                print(f"⚠️  [AUCTION] Failed to get quorum for claim broadcast")
                print(f"[AUCTION] Network partition detected - aborting execution")
                return False

            # Grace period: Wait for conflicting claims
            # CRITICAL: Use polling loop instead of sleep to allow message processing
            grace_period = 5.0  # Fixed for Docker reliability
            grace_start = time.time()
            grace_end_time = grace_start + grace_period
            print(f"⏳ [GRACE PERIOD START] Waiting {grace_period:.1f}s for conflicting claims...")
            print(f"   Started at: {grace_start:.3f}")

            # Poll every 0.5s to allow messages to be processed
            while time.time() < grace_end_time:
                await asyncio.sleep(0.5)

            grace_end = time.time()
            print(f"✅ [GRACE PERIOD END] Ended at {grace_end:.3f} (elapsed: {grace_end-grace_start:.2f}s)")

            # NOTE: Quorum was already verified by broadcast_reliable() above
            # The reliable broadcast ensures 2/3 ACK quorum, so no need to check again

            # Check if we were outbid during grace period
            if job_id not in self.claimed_jobs:
                print(f"⚠️  [AUCTION] Claim was REVOKED during grace period!")
                print(f"[AUCTION] Another node with higher priority claimed this job")
                return False

            # Re-evaluate to ensure we're still the winner
            print(f"[AUCTION] Re-evaluating winner after grace period...")
            final_winner = self._determine_winner(job_id)
            print(f"[AUCTION] Final winner determination: {final_winner} (me: {self.node_id})")

            if final_winner != self.node_id:
                print(f"⚠️  [AUCTION] Lost to {final_winner} after grace period")
                self.claimed_jobs.pop(job_id, None)
                # Call callback with loss
                callback = self.auction_callbacks.pop(job_id, None)
                if callback:
                    callback(False)
                return

            # Victory confirmed!
            print(f"✅ [AUCTION] Victory confirmed for {job_id}")
            # Call callback with win
            callback = self.auction_callbacks.pop(job_id, None)
            if callback:
                callback(True)

        else:
            print(f"❌ [AUCTION] Lost job {job_id} to {winner}")
            print(f"   My score: {score:.3f}")
            if winner:
                winner_bid = next((b for b in received_bids if b.node_id == winner), None)
                if winner_bid:
                    print(f"   Winner score: {winner_bid.score:.3f}")
            # Call callback with loss
            callback = self.auction_callbacks.pop(job_id, None)
            if callback:
                callback(False)
            # Clean up auction data for lost auctions
            self.active_auctions.pop(job_id, None)
            self.my_bids.pop(job_id, None)
            self.claimed_jobs.pop(job_id, None)
    
    def receive_bid(self, bid_message: dict):
        """
        Receive a bid from another node
        """
        receive_time = time.time()
        job_id = bid_message['job_id']
        node_id = bid_message['node_id']
        bid_score = bid_message['bid_score']
        bid_timestamp = bid_message['timestamp']

        # Calculate network latency
        latency = receive_time - bid_timestamp

        if job_id not in self.active_auctions:
            self.active_auctions[job_id] = []

        bid = Bid(
            job_id=job_id,
            node_id=node_id,
            score=bid_score,
            stake_amount=bid_message.get('stake_amount', 10.0),
            estimated_time=bid_message.get('estimated_time', 60.0),
            timestamp=bid_timestamp
        )

        self.active_auctions[job_id].append(bid)
        total_bids = len(self.active_auctions[job_id])
        print(f"📥 [BID RECEIVED] {node_id} → {self.node_id}: job={job_id}, score={bid_score:.3f}, latency={latency*1000:.1f}ms")
        print(f"   Total bids for {job_id}: {total_bids}")
    
    def receive_claim(self, claim_message: dict) -> bool:
        """
        Receive job claim from winner

        Returns True if we are the backup node
        """
        job_id = claim_message['job_id']
        winner = claim_message['winner_node_id']
        backup = claim_message.get('backup_node_id')
        winning_score = claim_message.get('winning_score', 1.0)

        print(f"[AUCTION] Job {job_id} claimed by {winner} with score {winning_score:.3f} (backup: {backup})")

        # Check if we also claimed this job (conflict!)
        if job_id in self.claimed_jobs:
            my_score = self.claimed_jobs[job_id]
            print(f"")
            print(f"🚨 [AUCTION] CONFLICT DETECTED!")
            print(f"   Job: {job_id}")
            print(f"   My claim: {self.node_id} with score {my_score:.3f}")
            print(f"   Their claim: {winner} with score {winning_score:.3f}")

            # Deterministic tie-breaking: higher score wins, then lower node_id wins
            should_back_down = False
            if winning_score > my_score:
                print(f"   Decision: Back down (their score is higher)")
                should_back_down = True
            elif winning_score < my_score:
                print(f"   Decision: Maintain claim (my score is higher)")
                should_back_down = False
            else:  # Scores are equal
                if winner < self.node_id:
                    print(f"   Decision: Back down (tie-break: {winner} < {self.node_id})")
                    should_back_down = True
                else:
                    print(f"   Decision: Maintain claim (tie-break: {self.node_id} < {winner})")
                    should_back_down = False

            if should_back_down:
                print(f"   ✅ Revoking claim and backing down")
                # Revoke our claim
                self.claimed_jobs.pop(job_id, None)
                self.active_auctions.pop(job_id, None)
                self.my_bids.pop(job_id, None)
                print(f"")
                return False
            else:
                print(f"   ✅ Maintaining claim - will continue execution")
                print(f"")

        # Add claim as a bid for conflict resolution during grace period
        if job_id in self.active_auctions:
            claim_bid = Bid(
                job_id=job_id,
                node_id=winner,
                score=winning_score,
                stake_amount=claim_message.get('stake_amount', 10.0),
                estimated_time=60.0,
                timestamp=claim_message['timestamp']
            )
            self.active_auctions[job_id].append(claim_bid)
            print(f"[AUCTION] Added claim bid from {winner}")

        return backup == self.node_id
    
    def _determine_winner(self, job_id: str) -> Optional[str]:
        """
        Determine auction winner based on highest score
        Uses deterministic tie-breaking to ensure all nodes agree on winner
        """
        # Create a copy to avoid modifying the original list
        bids = list(self.active_auctions.get(job_id, []))

        # Include own bid
        if job_id in self.my_bids:
            bids.append(self.my_bids[job_id])

        if not bids:
            return None

        # Remove duplicates (same node_id appears multiple times)
        seen_nodes = {}
        unique_bids = []
        for bid in bids:
            if bid.node_id not in seen_nodes or bid.score > seen_nodes[bid.node_id].score:
                seen_nodes[bid.node_id] = bid
        unique_bids = list(seen_nodes.values())

        if not unique_bids:
            return None

        # Sort by score (descending), then by node_id (ascending) for deterministic tie-breaking
        # This ensures all nodes agree on the winner even with identical scores
        sorted_bids = sorted(unique_bids, key=lambda b: (-b.score, b.node_id))

        winner_bid = sorted_bids[0]
        return winner_bid.node_id
    
    def _select_backup(self, job_id: str) -> Optional[str]:
        """
        Select backup node (second highest bidder)
        """
        # Create a copy to avoid modifying the original list
        bids = list(self.active_auctions.get(job_id, []))

        # Include own bid if we're determining backup for our win
        if job_id in self.my_bids:
            bids.append(self.my_bids[job_id])

        # Remove duplicates
        seen_nodes = {}
        for bid in bids:
            if bid.node_id not in seen_nodes or bid.score > seen_nodes[bid.node_id].score:
                seen_nodes[bid.node_id] = bid
        unique_bids = list(seen_nodes.values())

        if len(unique_bids) < 2:
            return None

        # Sort by score (descending), then by node_id for deterministic tie-breaking
        sorted_bids = sorted(unique_bids, key=lambda b: (-b.score, b.node_id))

        # Second highest is backup (if it's not us)
        for bid in sorted_bids[1:]:
            if bid.node_id != self.node_id:
                return bid.node_id

        return None
    
    def _calculate_backoff(self, score: float) -> float:
        """
        Calculate randomized backoff based on score
        Higher score = shorter delay
        OPTIMIZED FOR DOCKER: Minimal delays to ensure bids propagate
        """
        # Minimal delay - priority is getting bids out fast for Docker networking
        base_delay = self.backoff_base + (1.0 - score) * (self.backoff_max - self.backoff_base)

        # Add tiny random jitter to prevent ties
        jitter = random.uniform(-0.05, 0.05)

        delay = max(0.05, base_delay + jitter)

        return delay

    def _calculate_dynamic_grace_period(self) -> float:
        """
        Calculate dynamic grace period based on observed network latency
        Returns P99 latency * 2 + buffer

        SECURITY FIX: Prevents missing claims due to network delays
        """
        if not self.message_latencies:
            # Default: Conservative estimate for Docker networks
            return 3.5

        # Calculate P99 latency
        sorted_latencies = sorted(self.message_latencies)
        p99_index = int(len(sorted_latencies) * 0.99)
        p99_latency = sorted_latencies[p99_index] if p99_index < len(sorted_latencies) else sorted_latencies[-1]

        # Grace period = P99 * 2 + 1s buffer
        grace_period = (p99_latency * 2) + 1.0

        # Clamp between reasonable bounds
        return max(1.5, min(grace_period, 10.0))

    def record_message_latency(self, latency: float):
        """
        Record observed message latency for dynamic grace period calculation

        Args:
            latency: Message RTT in seconds
        """
        self.message_latencies.append(latency)

        # Keep last 100 samples
        if len(self.message_latencies) > 100:
            self.message_latencies.pop(0)

    def confirm_claim(self, job_id: str, confirming_node_id: str):
        """
        Record claim confirmation from peer

        Args:
            job_id: Job being claimed
            confirming_node_id: Node confirming the claim
        """
        if job_id not in self.claim_confirmations:
            self.claim_confirmations[job_id] = set()

        self.claim_confirmations[job_id].add(confirming_node_id)

    def _has_claim_quorum(self, job_id: str, min_confirmations: int = 2) -> bool:
        """
        Check if claim has quorum

        Args:
            job_id: Job ID
            min_confirmations: Minimum confirmations required

        Returns:
            True if quorum reached
        """
        confirmations = self.claim_confirmations.get(job_id, set())
        return len(confirmations) >= min_confirmations