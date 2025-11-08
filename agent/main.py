"""
Main Agent Node
Integrates all components into a cohesive autonomous agent
"""
import asyncio
import signal
import sys
from pathlib import Path
import time
from typing import Dict

from .config import AgentConfig, load_config
from .crypto.signing import SigningKey, sign_message, verify_message
from .p2p.node import P2PNode
from .p2p.protocol import MessageType, JobBroadcastMessage
from .token.wallet import Wallet
from .token.economy import TokenEconomy
from .trust.reputation import ReputationSystem
from .trust.watchdog import TrustWatchdog
from .rl.policy import RLPolicy, Action
from .bidding.scorer import BidScorer
from .bidding.auction import BiddingAuction
from .executor.engine import ExecutionEngine, JobResult, JobStatus
from .executor.shell import ShellRunner
from .executor.docker import DockerRunner, DockerBuildRunner
from .executor.security import (
    MalwareScanRunner, 
    PortScanRunner, 
    HashCrackRunner,
    ThreatIntelRunner
)
from .executor.recovery import RecoveryManager
from .dashboard.server import DashboardServer
from .bidding.router import JobRouter
from .rl.online_learner import OnlineLearner
from .p2p.coordinator import CoordinatorElection


class MarlOSAgent:
    """
    Main MarlOS Agent Node
    Autonomous, self-organizing, self-improving compute node
    """
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = load_config()
        
        self.config = config
        self.node_id = config.node_id
        self.node_name = config.node_name

        print(f"🌌 Initializing MarlOS Agent: {self.node_name}")

        # Cryptography
        key_file = f"{config.data_dir}/keys/{self.node_id}.key"
        self.signing_key = SigningKey.load_or_generate(key_file)
        print(f"🔐 Public Key: {self.signing_key.public_key_hex()[:16]}...")

        # P2P Network
        self.p2p = P2PNode(self.node_id, self.signing_key, config.network)

        # Coordinator Election System
        self.coordinator = CoordinatorElection(self.p2p)
        print(f"🗳️  Coordinator election system initialized")

        # Job Router (needs p2p to be initialized first)
        self.router = JobRouter(self.node_id, self.p2p)
        
        # Token System
        self.wallet = Wallet(
            self.node_id,
            config.token.starting_balance,
            config.data_dir,
            signing_key=self.signing_key  # Inject signing key for transaction signing
        )
        self.economy = TokenEconomy(config.token)
        
        # Trust System
        self.reputation = ReputationSystem(
            self.node_id,
            config.trust,
            config.data_dir
        )
        self.watchdog = TrustWatchdog(self.reputation, config.trust)
        
        # RL System
        self.rl_policy = RLPolicy(self.node_id, config.rl)
        
        # Bidding System
        self.scorer = BidScorer(node_id=self.node_id, coordinator=self.coordinator)
        self.auction = BiddingAuction(self.node_id, self.p2p)
        # Link coordinator to auction for fairness tracking
        self.auction.coordinator = self.coordinator
        
        # Execution System
        self.executor = ExecutionEngine(self.node_id, config.executor)
        self.recovery = RecoveryManager(self.node_id)
        
        # Dashboard
        self.dashboard = DashboardServer(
            self.node_id,
            config.dashboard,
            self
        )
        self.online_learner = OnlineLearner(
            self.node_id,
            config.rl,
            self.rl_policy,
            config.data_dir
        )
        # Connect online learner to RL policy
        self.rl_policy.online_learner = self.online_learner
        
        
        # State
        self.running = False
        self.jobs_completed = 0
        self.jobs_failed = 0

        # Job metadata tracking (stores payment, deadline, stake for active jobs)
        self.active_job_metadata: Dict[str, dict] = {}  # job_id -> {payment, deadline, stake, job_type, etc}
        
        # Register job runners
        self._register_job_runners()
        
        # Register message handlers
        self._register_message_handlers()
        
        # Setup callbacks
        self._setup_callbacks()
    
    def _register_job_runners(self):
        """Register all job type runners"""
        # Shell
        shell_runner = ShellRunner()
        self.executor.register_runner('shell', shell_runner.run)
        
        # Docker
        docker_runner = DockerRunner()
        if docker_runner.available:
            self.executor.register_runner('docker', docker_runner.run)
        
        docker_build_runner = DockerBuildRunner()
        if docker_build_runner.available:
            self.executor.register_runner('docker_build', docker_build_runner.run)
        
        # Security
        malware_runner = MalwareScanRunner()
        self.executor.register_runner('malware_scan', malware_runner.run)
        
        port_scan_runner = PortScanRunner()
        self.executor.register_runner('port_scan', port_scan_runner.run)
        
        hash_crack_runner = HashCrackRunner()
        self.executor.register_runner('hash_crack', hash_crack_runner.run)
        
        threat_intel_runner = ThreatIntelRunner()
        self.executor.register_runner('threat_intel', threat_intel_runner.run)
        
        print(f"✅ Registered {len(self.executor.get_capabilities())} job runners")
    
    def _register_message_handlers(self):
        """Register P2P message handlers"""
        
        @self.p2p.on_message(MessageType.PEER_ANNOUNCE)
        async def on_peer_announce(message: dict):
            """Handle peer discovery"""
            peer_id = message['node_id']
            peer_address = f"tcp://{message['ip']}:{message['port']}"
            
            # Connect to peer
            self.p2p.connect_to_peer(peer_address)
            
            # Update reputation
            if peer_id not in self.reputation.peer_trust_scores:
                self.reputation.update_peer_trust(
                    peer_id,
                    self.config.trust.starting_trust,
                    "discovery",
                    "New peer discovered"
                )
            
            print(f"👋 Peer discovered: {peer_id}")
        
        @self.p2p.on_message(MessageType.JOB_BROADCAST)
        async def on_job_broadcast(message: dict):
            """Handle new job broadcast"""
            await self._handle_new_job(message)
        
        @self.p2p.on_message(MessageType.JOB_BID)
        async def on_job_bid(message: dict):
            """Handle bid from another node"""
            self.auction.receive_bid(message)
        
        @self.p2p.on_message(MessageType.AUCTION_COORDINATE)
        async def on_auction_coordinate(message: dict):
            """Handle coordinator announcement"""
            job_id = message.get('job_id')
            coordinator_id = message.get('coordinator_id')
            bid_deadline = message.get('bid_deadline')

            print(f"[COORDINATOR] {coordinator_id} is coordinating auction for {job_id}")
            print(f"[COORDINATOR] Bid deadline: {bid_deadline - time.time():.1f}s from now")

            # Store coordinator assignment (all nodes should already know this via election)
            if job_id and coordinator_id:
                self.auction.job_coordinators[job_id] = coordinator_id

        @self.p2p.on_message(MessageType.JOB_CLAIM)
        async def on_job_claim(message: dict):
            """Handle job claim by winner"""
            is_backup = self.auction.receive_claim(message)

            if is_backup:
                # Register as backup node
                job_id = message['job_id']
                # TODO: Get job details
                print(f"🔄 Registered as backup for job {job_id}")
        
        @self.p2p.on_message(MessageType.JOB_HEARTBEAT)
        async def on_job_heartbeat(message: dict):
            """Handle job heartbeat from primary"""
            job_id = message['job_id']
            progress = message.get('progress', 0.0)
            self.recovery.update_heartbeat(job_id, progress)
        
        @self.p2p.on_message(MessageType.JOB_RESULT)
        async def on_job_result(message: dict):
            """Handle job result from another node"""
            peer_id = message['node_id']
            job_id = message['job_id']
            status = message['status']
            
            # Update peer reputation
            if status == 'success':
                self.watchdog.report_job_success(peer_id, job_id, on_time=True)
            elif status == 'failure':
                self.watchdog.report_job_failure(peer_id, job_id, "Job failed")
            elif status == 'timeout':
                self.watchdog.report_job_timeout(peer_id, job_id)
        
        @self.p2p.on_message(MessageType.REPUTATION_UPDATE)
        async def on_reputation_update(message: dict):
            """Handle reputation update gossip"""
            subject_node = message.get('subject_node_id')
            new_score = message.get('new_score')
            event = message.get('event')
            reason = message.get('reason', '')
            
            if subject_node and new_score is not None:
                self.reputation.update_peer_trust(
                    subject_node,
                    new_score,
                    event,
                    reason
                )
        
        @self.p2p.on_message(MessageType.TOKEN_TRANSACTION)
        async def on_token_transaction(message: dict):
            """Handle token transaction - sync to distributed ledger"""
            from_node = message.get('from_node')
            to_node = message.get('to_node')
            amount = message.get('amount', 0.0)
            reason = message.get('reason', '')
            job_id = message.get('job_id')

            # Only process transactions involving this node
            if to_node == self.node_id or from_node == self.node_id:
                print(f"[LEDGER] Syncing transaction: {from_node} → {to_node} ({amount} AC)")

                # Create ledger entry
                from .token.ledger import LedgerEntry

                entry = LedgerEntry(
                    entry_id=message.get('message_id', f"tx-{job_id}"),
                    timestamp=message.get('timestamp', time.time()),
                    from_node=from_node,
                    to_node=to_node,
                    amount=amount,
                    tx_type="TRANSFER",
                    reason=reason,
                    job_id=job_id,
                    balance_after=self.wallet.balance,
                    signature=message.get('signature', '')
                )

                # Add to ledger
                self.wallet.ledger.add_entry(entry)

                print(f"[LEDGER] Transaction recorded in distributed ledger")
    
    def _setup_callbacks(self):
        """Setup callbacks between components"""

        # Executor result callback
        async def on_job_result(result: JobResult):
            await self._handle_job_result(result)

        self.executor.set_result_callback(on_job_result)

        # Executor heartbeat callback
        async def on_heartbeat(job_id: str, progress: float):
            await self.p2p.broadcast_message(
                MessageType.JOB_HEARTBEAT,
                job_id=job_id,
                progress=progress
            )

        self.executor.add_heartbeat_callback(on_heartbeat)

        # Recovery manager callback for job takeover
        async def on_takeover_job(job: dict):
            """Execute job when taking over from failed primary"""
            print(f"[RECOVERY] Executing takeover job {job['job_id']}")
            result = await self.executor.execute_job(job)
            return result

        self.recovery.set_executor_callback(on_takeover_job)
    
    async def start(self):
        """Start the agent"""
        print(f"\n{'='*60}")
        print(f"🚀 Starting MarlOS Agent: {self.node_name}")
        print(f"{'='*60}\n")
        
        self.running = True
        
        # Start components
        await self.p2p.start()
        await self.watchdog.start()
        await self.recovery.start()

        await self.online_learner.start()
    
        print(f"\n✅ Agent {self.node_name} is ONLINE")
        
        # Start dashboard server
        asyncio.create_task(self.dashboard.start())
        
        # Start background tasks
        asyncio.create_task(self._stats_reporter())
        asyncio.create_task(self._idle_reward_task())
        
        print(f"\n✅ Agent {self.node_name} is ONLINE")
        print(f"   Public Key: {self.signing_key.public_key_hex()}")
        print(f"   Trust Score: {self.reputation.get_my_trust_score():.3f}")
        print(f"   Token Balance: {self.wallet.balance:.2f} AC")
        print(f"   Capabilities: {', '.join(self.executor.get_capabilities())}")
        print(f"   Dashboard: http://localhost:{self.config.dashboard.port}\n")
    
    async def stop(self):
        """Stop the agent"""
        print(f"\n🛑 Stopping agent {self.node_name}...")
        
        self.running = False
        
        # Stop components
        await self.p2p.stop()
        await self.watchdog.stop()
        await self.recovery.stop()
        await self.dashboard.stop()
        
        print("✅ Agent stopped cleanly")
    
    async def _handle_new_job(self, job_message: dict):
        """
        Handle new job broadcast - decide whether to bid
        """
        job_id = job_message['job_id']
        job_type = job_message['job_type']

        print(f"\n📥 New job received: {job_id} ({job_type})")

        # CRITICAL: Check if we're already bidding on or executing this job
        if job_id in self.auction.active_auctions or job_id in self.auction.my_bids:
            print(f"   ⏭️  Already bidding on {job_id} - ignoring duplicate")
            return

        # Check if job is already being executed
        if job_id in self.active_job_metadata:
            print(f"   ⏭️  Already executing {job_id} - ignoring duplicate")
            return

        # Check if we can handle this job type
        if job_type not in self.executor.get_capabilities():
            print(f"   ⚠️  Cannot handle job type: {job_type}")
            return

        # Check if quarantined
        if self.reputation.am_i_quarantined():
            print(f"   🚫 Cannot bid - currently quarantined")
            return
        
        # Calculate base score
        score = self.scorer.calculate_score(
            job=job_message,
            capabilities=self.executor.get_capabilities(),
            trust_score=self.reputation.get_my_trust_score(),
            active_jobs=self.executor.get_active_job_count(),
            job_history=self.rl_policy.state_calc.job_type_history
        )
        
        print(f"   📊 Base Score: {score:.3f}")
        
        # RL decision
        action, confidence = self.rl_policy.decide(
            job=job_message,
            wallet_balance=self.wallet.balance,
            trust_score=self.reputation.get_my_trust_score(),
            peer_count=self.p2p.get_peer_count(),
            active_jobs=self.executor.get_active_job_count()
        )
        
        print(f"   🧠 RL Decision: {action.name} (confidence: {confidence:.2f})")
        
        if action == Action.BID:
            # Calculate stake requirement
            payment = job_message.get('payment', 100.0)
            priority = job_message.get('priority', 0.5)
            stake = self.economy.calculate_stake_requirement(payment, priority)

            # Check if we can afford stake
            if not self.wallet.can_afford(stake):
                print(f"   ❌ Cannot afford stake: {stake:.2f} AC (have {self.wallet.balance:.2f} AC)")
                return

            # Estimate completion time
            estimated_time = self.scorer.estimate_completion_time(
                job_message,
                self.rl_policy.state_calc.job_type_history
            )

            # NON-BLOCKING: Place bid with callback - returns immediately
            # This allows _message_receiver to continue processing incoming bids
            def auction_callback(won: bool):
                """Called when auction completes (runs in background task)"""
                if won:
                    # We won! Mark for fairness tracking
                    self.scorer.mark_won_auction()

                    # Stake tokens and execute
                    if self.wallet.stake(stake, job_id):
                        # Store job metadata for later use
                        self.active_job_metadata[job_id] = {
                            'payment': job_message.get('payment', 100.0),
                            'deadline': job_message.get('deadline', time.time() + 300),
                            'stake': stake,
                            'job_type': job_message.get('job_type', 'unknown'),
                            'priority': job_message.get('priority', 0.5),
                            'start_time': time.time()
                        }
                        # Schedule job execution in event loop
                        asyncio.create_task(self._execute_job(job_message, stake))
                    else:
                        print(f"   ❌ Failed to stake tokens")
                else:
                    # Lost auction - track for idle bonus
                    self.scorer.mark_lost_auction()

            # Launch non-blocking auction (returns immediately)
            await self.auction.place_bid_nonblocking(
                job=job_message,
                score=score,
                stake_amount=stake,
                estimated_time=estimated_time,
                p2p_node=self.p2p,
                callback=auction_callback
            )

            print(f"   ✅ Bid placed - auction running in background (non-blocking)")
        
        elif action == Action.FORWARD:
            print(f"   📤 Forwarding job to better peer...")

            # Track for idle bonus
            self.scorer.mark_lost_auction()

            # Forward to better-suited peer
            best_peer = await self.router.forward_job(
                job_message,
                "RL decided to forward - peer better suited"
            )

            if best_peer:
                print(f"   ✅ Forwarded to {best_peer}")

                # Small reward for smart forwarding
                # Calculate state after forward
                next_state = self.rl_policy.state_calc.calculate_state(
                    job=job_message,
                    wallet_balance=self.wallet.balance,
                    trust_score=self.reputation.get_my_trust_score(),
                    peer_count=self.p2p.get_peer_count(),
                    active_jobs=self.executor.get_active_job_count()
                )

                # Record outcome for RL learning
                self.rl_policy.record_outcome(
                    success=True,
                    reward=0.2,  # Small positive reward for forwarding
                    new_state=next_state,
                    done=True
                )
            else:
                print(f"   ❌ No suitable peer found for forwarding")

        elif action == Action.DEFER:
            print(f"   ⏸️  Deferring job")

            # Track for idle bonus
            self.scorer.mark_lost_auction()

            # Record defer decision for RL learning
            next_state = self.rl_policy.state_calc.calculate_state(
                job=job_message,
                wallet_balance=self.wallet.balance,
                trust_score=self.reputation.get_my_trust_score(),
                peer_count=self.p2p.get_peer_count(),
                active_jobs=self.executor.get_active_job_count()
            )

            # Small negative reward for deferring (could have earned tokens)
            self.rl_policy.record_outcome(
                success=False,
                reward=-0.05,
                new_state=next_state,
                done=True
            )
    
    async def _execute_job(self, job: dict, stake_amount: float):
        """Execute a job we won"""
        job_id = job['job_id']
        
        print(f"\n▶️  Executing job {job_id}")
        
        # Execute
        result = await self.executor.execute_job(job)
        
        # Result already handled by callback
    
    async def _handle_job_result(self, result: JobResult):
        """Handle job completion result"""
        job_id = result.job_id

        print(f"\n📊 Job {job_id} completed: {result.status}")

        # Update counters
        if result.status == JobStatus.SUCCESS:
            self.jobs_completed += 1
        else:
            self.jobs_failed += 1

        # Broadcast result
        await self.p2p.broadcast_message(
            MessageType.JOB_RESULT,
            job_id=job_id,
            status=result.status,
            duration=result.duration,
            output=result.output,
            error=result.error
        )

        # Get job metadata
        job_metadata = self.active_job_metadata.get(job_id, {})
        payment = job_metadata.get('payment', 100.0)
        deadline = job_metadata.get('deadline', result.start_time + 300)
        stake = job_metadata.get('stake', 10.0)
        job_type = job_metadata.get('job_type', 'unknown')

        # Token handling
        if result.status == JobStatus.SUCCESS:
            
            payment_amount, bonus, reason = self.economy.calculate_job_payment(
                base_payment=payment,
                completion_time=result.end_time,
                deadline=deadline,
                success=True
            )

            # Release stake
            self.wallet.unstake(stake, job_id, success=True)
            
            # Deposit payment
            self.wallet.deposit(payment_amount, reason, job_id=job_id)
            
            # Update reputation
            on_time = result.end_time < deadline
            self.reputation.reward_success(job_id, on_time)

            
            
            # Broadcast reputation update
            await self.p2p.broadcast_message(
                MessageType.REPUTATION_UPDATE,
                subject_node_id=self.node_id,
                new_score=self.reputation.get_my_trust_score(),
                event='success',
                reason=reason
            )
            
            print(f"   💰 Earned {payment_amount:.2f} AC")
            print(f"   ⭐ Trust: {self.reputation.get_my_trust_score():.3f}")


        else:
            # Failure - slash stake
            self.wallet.unstake(stake, job_id, success=False)
            
            # Update reputation
            self.reputation.punish_failure(job_id, result.error or "Job failed")
            
            # Replenish reward pool with slashed stake
            self.economy.replenish_reward_pool(stake)
            
            # Broadcast reputation update
            await self.p2p.broadcast_message(
                MessageType.REPUTATION_UPDATE,
                subject_node_id=self.node_id,
                new_score=self.reputation.get_my_trust_score(),
                event='failure',
                reason=result.error or "Job failed"
            )
            
            print(f"   💀 Lost stake: {stake:.2f} AC")
            print(f"   ⭐ Trust: {self.reputation.get_my_trust_score():.3f}")

        # Update RL history
        success = result.status == JobStatus.SUCCESS
        self.rl_policy.update_job_history(job_type, success, result.duration)

        # Clean up job metadata
        self.active_job_metadata.pop(job_id, None)
    
    async def _stats_reporter(self):
        """Periodically report stats"""
        while self.running:
            await asyncio.sleep(30)
            
            stats = {
                'node_id': self.node_id,
                'peers': self.p2p.get_peer_count(),
                'active_jobs': self.executor.get_active_job_count(),
                'completed': self.jobs_completed,
                'failed': self.jobs_failed,
                'trust': self.reputation.get_my_trust_score(),
                'balance': self.wallet.balance,
                'staked': self.wallet.staked
            }
            
            print(f"\n📊 Stats: {stats['peers']} peers | "
                  f"{stats['active_jobs']} active | "
                  f"{stats['completed']} completed | "
                  f"Trust: {stats['trust']:.3f} | "
                  f"Balance: {stats['balance']:.2f} AC")
    
    async def _idle_reward_task(self):
        """Give idle rewards for being online"""
        while self.running:
            await asyncio.sleep(3600)  # Every hour
            
            # Only reward if not quarantined and idle
            if not self.reputation.am_i_quarantined():
                if self.executor.get_active_job_count() == 0:
                    idle_reward = self.economy.calculate_idle_reward(1.0)
                    self.wallet.deposit(idle_reward, "Idle availability reward")
    
    def get_state(self) -> dict:
        """Get current agent state for dashboard"""
        # Get peer list with details
        peers_dict = self.p2p.get_peers()
        peer_list = [
            {
                'node_id': peer_id,
                'last_seen': peer_info.get('last_seen', 0),
                'public_key': peer_info.get('public_key', '')[:16] + '...' if peer_info.get('public_key') else 'unknown',
                'connected': True,
                'trust_score': self.reputation.peer_trust_scores.get(peer_id, 0.5)
            }
            for peer_id, peer_info in peers_dict.items()
        ]

        # Get fairness statistics
        fairness_stats = self.coordinator.get_fairness_statistics() if self.coordinator else {}

        return {
            'node_id': self.node_id,
            'node_name': self.node_name,
            'public_key': self.signing_key.public_key_hex(),
            'trust_score': self.reputation.get_my_trust_score(),
            'wallet': self.wallet.get_stats(),
            'peers': self.p2p.get_peer_count(),
            'peer_list': peer_list,  # Add detailed peer list
            'active_jobs': self.executor.get_active_job_count(),
            'jobs_completed': self.jobs_completed,
            'jobs_failed': self.jobs_failed,
            'capabilities': self.executor.get_capabilities(),
            'quarantined': self.reputation.am_i_quarantined(),
            'reputation_stats': self.reputation.get_reputation_stats(),
            'watchdog_stats': self.watchdog.get_watchdog_stats(),
            'fairness_stats': fairness_stats  # Add fairness statistics
        }


async def main():
    """Main entry point"""
    # Load config
    config = load_config()

    # Create agent
    agent = MarlOSAgent(config)

    # Handle shutdown
    loop = asyncio.get_event_loop()

    def handle_shutdown(sig):
        print(f"\n⚠️  Received signal {sig}, shutting down gracefully...")
        # Create stop task - don't call loop.stop() as it prevents cleanup
        asyncio.create_task(agent.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: handle_shutdown(s))

    # Start agent
    await agent.start()

    # Keep running
    try:
        while agent.running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())