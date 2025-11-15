"""
Main Agent Node
Integrates all components into a cohesive autonomous agent
WITH COMPLETE JOB STATISTICS TRACKING AND FIXED BIDDING DATA
"""
import asyncio
import signal
import sys
from pathlib import Path
import time
from typing import Dict, List
import paho.mqtt.client as mqtt

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        # Fallback for older Python versions
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from .executor.hardware import HardwareRunner
from .config import AgentConfig, load_config
from .crypto.signing import SigningKey, sign_message, verify_message
from .p2p.node import P2PNode
from .p2p.protocol import MessageType, JobBroadcastMessage
from .tokens.wallet import Wallet
from .tokens.economy import TokenEconomy
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
from .predictive.integration import PredictiveExtension
from .p2p.peer_manager import PeerManager
from .p2p.dht_manager import DHTManager
from .config import NetworkMode
import os  # <-- ADD THIS

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

        self.has_hardware = os.getenv('ENABLE_HARDWARE_RUNNER', 'false').lower() == 'true'

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
            signing_key=self.signing_key
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
        self.auction.coordinator = self.coordinator
        
        # Execution System
        self.executor = ExecutionEngine(self.node_id, config.executor)
        self.recovery = RecoveryManager(self.node_id)

       # 3. ADD MQTT CLIENT (near the end of __init__)
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        mqtt_host = getattr(config, 'mqtt_broker_host', 'mosquitto')
        mqtt_port = getattr(config, 'mqtt_broker_port', 1883)
        self.mqtt_connected = False
        
        try:
            # The healthcheck should make this connect on the first try
            print(f"[MQTT] Attempting to connect to broker at {mqtt_host}:{mqtt_port}...")
            self.mqtt_client.connect(mqtt_host, mqtt_port, 60)
            self.mqtt_client.loop_start() # Start background loop
            self.mqtt_connected = True
            print(f"🛰️  MQTT client connected.")
        
        except Exception as e:
            # This will catch any error, including ConnectionRefused
            print(f"⚠️  CRITICAL: Failed to connect to MQTT broker: {e}")
            print("   Hardware runner will NOT be registered.")
        
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
        self.rl_policy.online_learner = self.online_learner

        # Predictive Pre-Execution System (RL-powered speculation)
        self.predictive = PredictiveExtension(self)

        # Network Mode - Private or Public
        self.peer_manager = None
        self.dht = None

        if self.config.network.mode == NetworkMode.PRIVATE:
            # PRIVATE MODE: Manual peer management
            print(f"📋 [NETWORK] Private Mode - Manual peer management")
            self.peer_manager = PeerManager(self.config.network.saved_peers_file)
            print(f"📋 [NETWORK] Loaded {len(self.peer_manager.peers)} saved peers")

            # Auto-connect to saved peers on startup
            auto_connect_peers = self.peer_manager.get_auto_connect_peers()
            if auto_connect_peers:
                print(f"📋 [NETWORK] Will auto-connect to {len(auto_connect_peers)} peers")

        elif self.config.network.mode == NetworkMode.PUBLIC:
            # PUBLIC MODE: DHT-based automatic discovery
            print(f"🌐 [NETWORK] Public Mode - DHT automatic discovery")
            if self.config.network.dht_enabled:
                self.dht = DHTManager(
                    self.node_id,
                    self.config.network.dht_port,
                    self.config.network.dht_bootstrap_nodes
                )
                print(f"🌐 [NETWORK] DHT enabled on port {self.config.network.dht_port}")
            else:
                print(f"⚠️  [NETWORK] Public mode selected but DHT disabled")

        # State
        self.running = False
        self.jobs_completed = 0
        self.jobs_failed = 0

        # === JOB TRACKING FOR DASHBOARD ===
        self.job_results: Dict[str, JobResult] = {}  # Store completed job results
        self.start_time = time.time()  # Track uptime

        # Job metadata tracking
        self.active_job_metadata: Dict[str, dict] = {}
        
        # === BIDDING TRACKING FOR DASHBOARD (FIXED) ===
        self.won_bids: List[dict] = []  # Track won auctions
        self.lost_bids: List[dict] = []  # Track lost auctions
        
        # Register job runners
        self._register_job_runners()
        
        # Register message handlers
        self._register_message_handlers()
        
        # Setup callbacks
        self._setup_callbacks()
    
    def _register_job_runners(self):
        """Register all job type runners"""
        shell_runner = ShellRunner()
        self.executor.register_runner('shell', shell_runner.run)
        
        docker_runner = DockerRunner()
        if docker_runner.available:
            self.executor.register_runner('docker', docker_runner.run)
        
        docker_build_runner = DockerBuildRunner()
        if docker_build_runner.available:
            self.executor.register_runner('docker_build', docker_build_runner.run)
        
        malware_runner = MalwareScanRunner()
        self.executor.register_runner('malware_scan', malware_runner.run)
        
        port_scan_runner = PortScanRunner()
        self.executor.register_runner('port_scan', port_scan_runner.run)
        
        hash_crack_runner = HashCrackRunner()
        self.executor.register_runner('hash_crack', hash_crack_runner.run)
        
        threat_intel_runner = ThreatIntelRunner()
        self.executor.register_runner('threat_intel', threat_intel_runner.run)
        
       # 4. REGISTER THE HARDWARE RUNNER (ONLY IF ENABLED)
        if self.has_hardware:
            print("✨ This is a HARDWARE AGENT. Registering led_control...")
            hardware_command_topic = "marlos/devices/uno-01/command"
            hardware_runner = HardwareRunner(self.mqtt_client, hardware_command_topic)
            self.executor.register_runner('led_control', hardware_runner.run)
        else:
            print("Standard agent. Skipping hardware runner.")
        print(f"✅ Registered {len(self.executor.get_capabilities())} job runners")
    
    def _register_message_handlers(self):
        """Register P2P message handlers"""
        
        @self.p2p.on_message(MessageType.PEER_ANNOUNCE)
        async def on_peer_announce(message: dict):
            peer_id = message['node_id']
            peer_address = f"tcp://{message['ip']}:{message['port']}"
            
            self.p2p.connect_to_peer(peer_address)
            
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
            await self._handle_new_job(message)
        
        @self.p2p.on_message(MessageType.JOB_BID)
        async def on_job_bid(message: dict):
            self.auction.receive_bid(message)
        
        @self.p2p.on_message(MessageType.AUCTION_COORDINATE)
        async def on_auction_coordinate(message: dict):
            job_id = message.get('job_id')
            coordinator_id = message.get('coordinator_id')
            bid_deadline = message.get('bid_deadline')

            print(f"[COORDINATOR] {coordinator_id} is coordinating auction for {job_id}")
            print(f"[COORDINATOR] Bid deadline: {bid_deadline - time.time():.1f}s from now")

            if job_id and coordinator_id:
                self.auction.job_coordinators[job_id] = coordinator_id

        @self.p2p.on_message(MessageType.JOB_CLAIM)
        async def on_job_claim(message: dict):
            is_backup = self.auction.receive_claim(message)
            if is_backup:
                job_id = message['job_id']
                print(f"🔄 Registered as backup for job {job_id}")
        
        @self.p2p.on_message(MessageType.JOB_HEARTBEAT)
        async def on_job_heartbeat(message: dict):
            job_id = message['job_id']
            progress = message.get('progress', 0.0)
            self.recovery.update_heartbeat(job_id, progress)
        
        @self.p2p.on_message(MessageType.JOB_RESULT)
        async def on_job_result(message: dict):
            peer_id = message['node_id']
            job_id = message['job_id']
            status = message['status']
            
            if status == 'success':
                self.watchdog.report_job_success(peer_id, job_id, on_time=True)
            elif status == 'failure':
                self.watchdog.report_job_failure(peer_id, job_id, "Job failed")
            elif status == 'timeout':
                self.watchdog.report_job_timeout(peer_id, job_id)
        
        @self.p2p.on_message(MessageType.REPUTATION_UPDATE)
        async def on_reputation_update(message: dict):
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
            from_node = message.get('from_node')
            to_node = message.get('to_node')
            amount = message.get('amount', 0.0)
            reason = message.get('reason', '')
            job_id = message.get('job_id')

            if to_node == self.node_id or from_node == self.node_id:
                print(f"[LEDGER] Syncing transaction: {from_node} → {to_node} ({amount} AC)")

                # Create ledger entry
                from .tokens.ledger import LedgerEntry

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

                self.wallet.ledger.add_entry(entry)
                print(f"[LEDGER] Transaction recorded in distributed ledger")
    
    def _setup_callbacks(self):
        """Setup callbacks between components"""

        async def on_job_result(result: JobResult):
            await self._handle_job_result(result)

        self.executor.set_result_callback(on_job_result)

        async def on_heartbeat(job_id: str, progress: float):
            await self.p2p.broadcast_message(
                MessageType.JOB_HEARTBEAT,
                job_id=job_id,
                progress=progress
            )

        self.executor.add_heartbeat_callback(on_heartbeat)

        async def on_takeover_job(job: dict):
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
        
        await self.p2p.start()
        await self.watchdog.start()
        await self.recovery.start()
        await self.online_learner.start()

        # Start predictive system (if enabled in config)
        await self.predictive.start()

        # Start network mode specific components
        if self.config.network.mode == NetworkMode.PRIVATE and self.peer_manager:
            # Auto-connect to saved peers
            auto_connect_peers = self.peer_manager.get_auto_connect_peers()
            for peer_address in auto_connect_peers:
                try:
                    self.p2p.connect_to_peer(peer_address)
                    print(f"📋 [NETWORK] Connected to saved peer: {peer_address}")
                except Exception as e:
                    print(f"⚠️  [NETWORK] Failed to connect to {peer_address}: {e}")

        elif self.config.network.mode == NetworkMode.PUBLIC and self.dht:
            # Start DHT and announce ourselves
            try:
                local_ip = self.p2p.local_ip
                capabilities = self.executor.get_capabilities()
                success = await self.dht.start(local_ip, self.config.network.pub_port, capabilities)

                if success:
                    print(f"🌐 [NETWORK] Joined global DHT network")

                    # Set up DHT callback for discovered peers
                    async def on_peer_discovered(peer_info):
                        peer_address = f"tcp://{peer_info['ip']}:{peer_info['port']}"
                        self.p2p.connect_to_peer(peer_address)
                        print(f"🌐 [NETWORK] Auto-connected to DHT peer: {peer_info['node_id']}")

                    self.dht.on_peer_discovered = on_peer_discovered
                else:
                    print(f"⚠️  [NETWORK] Failed to join DHT network")
            except Exception as e:
                print(f"⚠️  [NETWORK] DHT error: {e}")

        print(f"\n✅ Agent {self.node_name} is ONLINE")

        asyncio.create_task(self.dashboard.start())
        asyncio.create_task(self._stats_reporter())
        asyncio.create_task(self._idle_reward_task())

        print(f"   Public Key: {self.signing_key.public_key_hex()}")
        print(f"   Trust Score: {self.reputation.get_my_trust_score():.3f}")
        print(f"   Token Balance: {self.wallet.balance:.2f} AC")
        print(f"   Capabilities: {', '.join(self.executor.get_capabilities())}")

        # Display dashboard URLs for both local and network access
        local_ip = self.p2p.local_ip
        print(f"   Network Mode: {self.config.network.mode.value.upper()}")

        if self.config.network.mode == NetworkMode.PRIVATE:
            print(f"   Saved Peers: {len(self.peer_manager.peers) if self.peer_manager else 0}")
        elif self.config.network.mode == NetworkMode.PUBLIC:
            print(f"   DHT: {'Active' if self.dht and self.dht.running else 'Inactive'}")

        print(f"   Dashboard URLs:")
        print(f"     - Local:   http://localhost:{self.config.dashboard.port}")
        print(f"     - Network: http://{local_ip}:{self.config.dashboard.port}")
        print(f"   P2P Address: tcp://{local_ip}:{self.config.network.pub_port}\n")
    
    async def stop(self):
        """Stop the agent"""
        print(f"\n🛑 Stopping agent {self.node_name}...")

        self.running = False

        # Stop network mode specific components
        if self.dht:
            await self.dht.stop()

        await self.p2p.stop()
        await self.watchdog.stop()
        await self.recovery.stop()
        await self.dashboard.stop()
        await self.predictive.stop()

        print("✅ Agent stopped cleanly")
    
    async def _handle_new_job(self, job_message: dict):
        """Handle new job broadcast - decide whether to bid"""
        job_id = job_message['job_id']
        job_type = job_message['job_type']

        print(f"\n📥 New job received: {job_id} ({job_type})")

        if job_id in self.auction.active_auctions or job_id in self.auction.my_bids:
            print(f"   ⏭️  Already bidding on {job_id} - ignoring duplicate")
            return

        if job_id in self.active_job_metadata:
            print(f"   ⏭️  Already executing {job_id} - ignoring duplicate")
            return

        if job_type not in self.executor.get_capabilities():
            print(f"   ⚠️  Cannot handle job type: {job_type}")
            return

        if self.reputation.am_i_quarantined():
            print(f"   🚫 Cannot bid - currently quarantined")
            return

        # Observe job for pattern learning (predictive system)
        self.predictive.observe_job_submission(job_message)

        # Calculate base score
        score = self.scorer.calculate_score(
            job=job_message,
            capabilities=self.executor.get_capabilities(),
            trust_score=self.reputation.get_my_trust_score(),
            active_jobs=self.executor.get_active_job_count(),
            job_history=self.rl_policy.state_calc.job_type_history
        )
        
        print(f"   📊 Base Score: {score:.3f}")
        
        action, confidence = self.rl_policy.decide(
            job=job_message,
            wallet_balance=self.wallet.balance,
            trust_score=self.reputation.get_my_trust_score(),
            peer_count=self.p2p.get_peer_count(),
            active_jobs=self.executor.get_active_job_count()
        )
        
        print(f"   🧠 RL Decision: {action.name} (confidence: {confidence:.2f})")
        
        if action == Action.BID:
            payment = job_message.get('payment', 100.0)
            priority = job_message.get('priority', 0.5)
            stake = self.economy.calculate_stake_requirement(payment, priority)

            if not self.wallet.can_afford(stake):
                print(f"   ❌ Cannot afford stake: {stake:.2f} AC (have {self.wallet.balance:.2f} AC)")
                return

            estimated_time = self.scorer.estimate_completion_time(
                job_message,
                self.rl_policy.state_calc.job_type_history
            )

            def auction_callback(won: bool):
                if won:
                    self.scorer.mark_won_auction()
                    
                    # === TRACK WON BID ===
                    self.won_bids.append({
                        'job_id': job_id,
                        'job_type': job_message.get('job_type', 'unknown'),
                        'payment': job_message.get('payment', 100.0),
                        'score': score,
                        'timestamp': time.time()
                    })
                    # Keep only last 100
                    if len(self.won_bids) > 100:
                        self.won_bids = self.won_bids[-100:]
                    
                    print(f"   🏆 WON AUCTION - Total wins: {len(self.won_bids)}")

                    if self.wallet.stake(stake, job_id):
                        self.active_job_metadata[job_id] = {
                            'payment': job_message.get('payment', 100.0),
                            'deadline': job_message.get('deadline', time.time() + 300),
                            'stake': stake,
                            'job_type': job_message.get('job_type', 'unknown'),
                            'priority': job_message.get('priority', 0.5),
                            'start_time': time.time()
                        }
                        asyncio.create_task(self._execute_job(job_message, stake))
                    else:
                        print(f"   ❌ Failed to stake tokens")
                else:
                    self.scorer.mark_lost_auction()
                    
                    # === TRACK LOST BID ===
                    self.lost_bids.append({
                        'job_id': job_id,
                        'job_type': job_message.get('job_type', 'unknown'),
                        'score': score,
                        'timestamp': time.time()
                    })
                    # Keep only last 100
                    if len(self.lost_bids) > 100:
                        self.lost_bids = self.lost_bids[-100:]
                    
                    print(f"   ❌ LOST AUCTION - Total losses: {len(self.lost_bids)}")

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
            self.scorer.mark_lost_auction()

            best_peer = await self.router.forward_job(
                job_message,
                "RL decided to forward - peer better suited"
            )

            if best_peer:
                print(f"   ✅ Forwarded to {best_peer}")

                next_state = self.rl_policy.state_calc.calculate_state(
                    job=job_message,
                    wallet_balance=self.wallet.balance,
                    trust_score=self.reputation.get_my_trust_score(),
                    peer_count=self.p2p.get_peer_count(),
                    active_jobs=self.executor.get_active_job_count()
                )

                self.rl_policy.record_outcome(
                    success=True,
                    reward=0.2,
                    new_state=next_state,
                    done=True
                )
            else:
                print(f"   ❌ No suitable peer found for forwarding")

        elif action == Action.DEFER:
            print(f"   ⏸️  Deferring job")
            self.scorer.mark_lost_auction()

            next_state = self.rl_policy.state_calc.calculate_state(
                job=job_message,
                wallet_balance=self.wallet.balance,
                trust_score=self.reputation.get_my_trust_score(),
                peer_count=self.p2p.get_peer_count(),
                active_jobs=self.executor.get_active_job_count()
            )

            self.rl_policy.record_outcome(
                success=False,
                reward=-0.05,
                new_state=next_state,
                done=True
            )
    
    async def _execute_job(self, job: dict, stake_amount: float):
        """Execute a job we won"""
        job_id = job['job_id'] # This is the REAL job_id

        print(f"\n▶️  Executing job {job_id}")

        # Check cache for pre-executed result
        cached_result = self.predictive.check_cache(job)

        if cached_result:
            print(f"*** [CACHE] CACHE HIT! Using pre-executed result for job {job_id} ***")

            fingerprint = job.get('fingerprint')
            if fingerprint:
                self.predictive.speculation_engine.report_cache_hit(fingerprint)

            # --- THIS IS THE FIX ---
            # We must create a NEW JobResult object using the REAL job_id.
            # Do NOT use the cached_result object directly, as it has the
            # speculative job's ID and a FAILURE status.

            # We use the *output* from the cache, but the *identity* of the real job.

            # Handle both JobResult objects and dicts from cache
            final_output = {}
            final_error = None
            final_status = JobStatus.SUCCESS # Default to success for a cache hit

            if isinstance(cached_result, JobResult):
                # If the cached result was a FAILURE (e.g., 'No command'),
                # we must re-run the job. We can't use a failed cached result.
                if cached_result.status == JobStatus.FAILURE:
                    print(f"⚠️  [CACHE] Cached result was a FAILURE. Re-executing job {job_id} normally.")
                    await self.executor.execute_job(job) # This will call _handle_job_result on its own
                    return

                final_output = cached_result.output
                final_error = cached_result.error
                final_status = cached_result.status # Use the cached status (should be SUCCESS)

            elif isinstance(cached_result, dict):
                final_output = cached_result.get('output', {})
                final_error = cached_result.get('error')
                final_status = cached_result.get('status', JobStatus.SUCCESS)

            # Create the final result with the REAL job_id
            result = JobResult(
                job_id=job_id,  # Use the REAL job_id
                status=final_status,
                output=final_output,
                error=final_error,
                start_time=time.time(), # Mark as instant
                end_time=time.time(),
                duration=0.0 
            )

            # Handle this new, correct result
            await self._handle_job_result(result)
            return

        # Not in cache - execute normally
        await self.executor.execute_job(job)

    async def _handle_job_result(self, result: JobResult):
        """
        Handle job completion result
        Stores results for dashboard tracking
        """
        job_id = result.job_id

        print(f"\n📊 Job {job_id} completed: {result.status}")

        # === STORE JOB RESULT FOR DASHBOARD ===
        self.job_results[result.job_id] = result
        
        # Keep only last 100 results
        if len(self.job_results) > 100:
            sorted_results = sorted(
                self.job_results.items(),
                key=lambda x: x[1].end_time
            )
            self.job_results = dict(sorted_results[-100:])

        if result.status == JobStatus.SUCCESS:
            self.jobs_completed += 1
        else:
            self.jobs_failed += 1

        await self.p2p.broadcast_message(
            MessageType.JOB_RESULT,
            job_id=job_id,
            status=result.status,
            duration=result.duration,
            output=result.output,
            error=result.error
        )

        job_metadata = self.active_job_metadata.get(job_id, {})
        payment = job_metadata.get('payment', 100.0)
        deadline = job_metadata.get('deadline', result.start_time + 300)
        stake = job_metadata.get('stake', 10.0)
        job_type = job_metadata.get('job_type', 'unknown')

        if result.status == JobStatus.SUCCESS:
            
            payment_amount, bonus, reason = self.economy.calculate_job_payment(
                base_payment=payment,
                completion_time=result.end_time,
                deadline=deadline,
                success=True
            )
            # Release stake
            self.wallet.unstake(stake, job_id, success=True)
            
            if payment_amount >0:
                self.wallet.deposit(payment_amount,reason,job_id=job_id)
                print(f"   Earned {payment_amount:.2f} MC")
            else:
                print(f"    Speculative job success, no payment")
            
            on_time = result.end_time < deadline
            self.reputation.reward_success(job_id, on_time)
            
            await self.p2p.broadcast_message(
                MessageType.REPUTATION_UPDATE,
                subject_node_id=self.node_id,
                new_score=self.reputation.get_my_trust_score(),
                event='success',
                reason=reason
            )
            
            print(f"   ⭐ Trust: {self.reputation.get_my_trust_score():.3f}")

        else:
            self.wallet.unstake(stake, job_id, success=False)
            self.reputation.punish_failure(job_id, result.error or "Job failed")
            self.economy.replenish_reward_pool(stake)
            
            await self.p2p.broadcast_message(
                MessageType.REPUTATION_UPDATE,
                subject_node_id=self.node_id,
                new_score=self.reputation.get_my_trust_score(),
                event='failure',
                reason=result.error or "Job failed"
            )
            
            print(f"   💀 Lost stake: {stake:.2f} AC")
            print(f"   ⭐ Trust: {self.reputation.get_my_trust_score():.3f}")

        success = result.status == JobStatus.SUCCESS
        self.rl_policy.update_job_history(job_type, success, result.duration)

        # === BROADCAST TO DASHBOARD ===
        if self.dashboard:
            await self.dashboard.broadcast({
                'type': 'job_completed',
                'data': {
                    'job_id': result.job_id,
                    'status': result.status.value,
                    'duration': result.duration,
                    'timestamp': result.end_time
                }
            })

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

            # Add predictive stats if enabled
            predictive_stats = self.predictive.get_stats()
            if predictive_stats.get('enabled'):
                cache_stats = predictive_stats.get('cache', {})
                speculation_stats = predictive_stats.get('speculation', {})
                stats['cache_hit_rate'] = cache_stats.get('hit_rate', 0)
                stats['speculations'] = speculation_stats.get('speculations_attempted', 0)

            print(f"\n📊 Stats: {stats['peers']} peers | "
                  f"{stats['active_jobs']} active | "
                  f"{stats['completed']} completed | "
                  f"Trust: {stats['trust']:.3f} | "
                  f"Balance: {stats['balance']:.2f} AC")

            # Print predictive stats if enabled
            if predictive_stats.get('enabled'):
                print(f"   🔮 Predictive: Cache Hit Rate {stats.get('cache_hit_rate', 0):.1f}% | "
                      f"Speculations: {stats.get('speculations', 0)}")
    
    async def _idle_reward_task(self):
        """Give idle rewards for being online"""
        while self.running:
            await asyncio.sleep(3600)
            
            if not self.reputation.am_i_quarantined():
                if self.executor.get_active_job_count() == 0:
                    idle_reward = self.economy.calculate_idle_reward(1.0)
                    self.wallet.deposit(idle_reward, "Idle availability reward")
    
    def get_state(self) -> dict:
        """
        Get comprehensive agent state for dashboard
        WITH FIXED BIDDING DATA AND REPUTATION EVENTS
        """
        # === CALCULATE JOB STATISTICS ===
        active_jobs = self.executor.get_active_job_count()
        
        completed_jobs = sum(
            1 for r in self.job_results.values()
            if r.status == JobStatus.SUCCESS
        )
        failed_jobs = sum(
            1 for r in self.job_results.values()
            if r.status in [JobStatus.FAILURE, JobStatus.TIMEOUT]
        )
        total_jobs = len(self.job_results)
        success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
        
        # Build recent jobs list
        recent_jobs = sorted(
            [
                {
                    'job_id': r.job_id,
                    'status': r.status.value,
                    'duration': round(r.duration, 2),
                    'timestamp': r.end_time,
                    'error': r.error
                }
                for r in self.job_results.values()
            ],
            key=lambda x: x['timestamp'],
            reverse=True
        )[:10]
        
        # Get peer list
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

        fairness_stats = self.coordinator.get_fairness_statistics() if self.coordinator else {}

        # === FIXED: BIDDING/AUCTION DATA ===
        # Active auctions (jobs currently in bidding phase)
        active_auctions = []
        for job_id, bids in self.auction.active_auctions.items():
            if bids:  # Only include auctions with bids
                highest_bid = max(bids, key=lambda b: b.score) if bids else None
                active_auctions.append({
                    'job_id': job_id,
                    'job_type': 'unknown',
                    'payment': 100.0,
                    'bids_count': len(bids),
                    'highest_bid': {
                        'node_id': highest_bid.node_id,
                        'score': highest_bid.score,
                    } if highest_bid else None,
                    'bids': [
                        {
                            'node_id': bid.node_id,
                            'score': bid.score,
                            'stake_amount': bid.stake_amount,
                        }
                        for bid in bids
                    ]
                })
        
        # My active bids
        my_bids = []
        for job_id, bid in self.auction.my_bids.items():
            # Calculate rank (how many bids beat us)
            all_bids = self.auction.active_auctions.get(job_id, [])
            if all_bids:
                sorted_bids = sorted(all_bids + [bid], key=lambda b: b.score, reverse=True)
                rank = sorted_bids.index(bid) + 1 if bid in sorted_bids else None
            else:
                rank = 1
            
            my_bids.append({
                'job_id': job_id,
                'job_type': 'unknown',
                'score': bid.score,
                'stake': bid.stake_amount,
                'rank': rank,
                'timestamp': bid.timestamp
            })
        
        # Won/Lost bids (from tracking lists) - FIXED
        won_bids = self.won_bids[-20:] if self.won_bids else []
        lost_bids = self.lost_bids[-20:] if self.lost_bids else []
        
        # Calculate win rate
        total_auctions = len(self.won_bids) + len(self.lost_bids)
        win_rate = (len(self.won_bids) / total_auctions * 100) if total_auctions > 0 else 0

        return {
            'node_id': self.node_id,
            'node_name': self.node_name,
            'public_key': self.signing_key.public_key_hex(),
            'status': 'running' if self.running else 'stopped',
            'uptime': time.time() - self.start_time,
            
            # === JOB STATISTICS ===
            'jobs': {
                'active': active_jobs,
                'completed': completed_jobs,
                'failed': failed_jobs,
                'total': total_jobs,
                'success_rate': round(success_rate, 1)
            },
            
            # === RECENT JOBS ===
            'recent_jobs': recent_jobs,
            
            # === BIDDING DATA (FIXED) ===
            'bidding': {
                'active_auctions': active_auctions,
                'my_bids': my_bids,
                'won_bids': won_bids,
                'lost_bids': lost_bids,
                'total_won': len(self.won_bids),
                'total_lost': len(self.lost_bids),
                'win_rate': round(win_rate, 1)
            },
            
            # Existing fields
            'trust_score': self.reputation.get_my_trust_score(),
            'wallet': self.wallet.get_stats(),
            'peers': self.p2p.get_peer_count(),
            'peer_list': peer_list,
            'active_jobs': self.executor.get_active_job_count(),
            'jobs_completed': self.jobs_completed,
            'jobs_failed': self.jobs_failed,
            'capabilities': self.executor.get_capabilities(),
            'quarantined': self.reputation.am_i_quarantined(),
            'reputation_stats': self.reputation.get_reputation_stats(),
            'watchdog_stats': self.watchdog.get_watchdog_stats(),
            'fairness_stats': fairness_stats,  # Add fairness statistics
            'predictive_stats': self.predictive.get_stats()  # Add predictive system stats
        }
    
    def _get_cpu_usage(self) -> float:
        """Get CPU usage percentage"""
        try:
            import psutil
            return round(psutil.cpu_percent(interval=0.1), 1)
        except:
            return 0.0

    def _get_memory_usage(self) -> float:
        """Get memory usage percentage"""
        try:
            import psutil
            return round(psutil.virtual_memory().percent, 1)
        except:
            return 0.0

    def _get_disk_usage(self) -> float:
        """Get disk usage percentage"""
        try:
            import psutil
            return round(psutil.disk_usage('/').percent, 1)
        except:
            return 0.0


async def main():
    """Main entry point"""
    config = load_config()
    agent = MarlOSAgent(config)

    loop = asyncio.get_event_loop()

    def handle_shutdown(sig):
        print(f"\n⚠️  Received signal {sig}, shutting down gracefully...")
        asyncio.create_task(agent.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: handle_shutdown(s))

    await agent.start()

    try:
        while agent.running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())