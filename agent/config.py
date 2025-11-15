"""
MarlOS Agent Configuration
"""

import os
from dataclasses import dataclass, field
from typing import List
from enum import Enum


class NetworkMode(Enum):
    """Network operation mode"""
    PRIVATE = "private"  # Manual peer management, user's own devices
    PUBLIC = "public"    # DHT-based global network, automatic discovery



@dataclass
class PredictiveConfig:
    """Predictive pre-execution configuration"""
    # Feature toggle
    enabled: bool = False  # Enable predictive pre-execution

    # Pattern detection
    min_pattern_confidence: float = 0.75  # Min confidence to predict (75%)
    min_occurrences: int = 3  # Min times pattern must occur

    # Economic constraints
    max_speculation_ratio: float = 0.2  # Max 20% of capacity on speculation
    min_expected_value: float = 3.0  # Min expected profit in AC tokens

    # Rewards/penalties
    correct_prediction_reward: int = 20  # Huge reward for cache hit!
    wrong_prediction_penalty: int = 5  # Penalty for wasted compute

    # Cache settings
    cache_ttl: int = 300  # Cache results for 5 minutes
    max_cache_size: int = 100  # Max cached results

    # RL Speculation
    rl_speculation_enabled: bool = True  # Use RL for speculation decisions
    rl_model_path: str = "rl_trainer/models/speculation_policy.zip"


@dataclass
class RLConfig:
    """Reinforcement learning configuration"""
    model_path: str = "rl_trainer/models/policy_v1.zip"
    state_dim: int = 35  # Extended for prediction features
    action_dim: int = 3  # BID, FORWARD, DEFER

    # Learning
    online_learning: bool = False
    exploration_rate: float = 0.1
    enabled: bool = True


@dataclass
class TokenConfig:
    """Token economy configuration"""
    starting_balance: float = 100.0
    network_fee: float = 0.05  # 5%
    idle_reward: float = 1.0  # per hour
    stake_requirement: float = 10.0  # minimum stake
    
    # Rewards
    success_bonus: float = 0.20  # 20% bonus
    late_penalty: float = 0.10   # 10% penalty
    failure_penalty: float = 1.0  # full stake



@dataclass
class DashboardConfig:
    """Dashboard server configuration"""
    host: str = "0.0.0.0"
    port: int = 3001
    cors_origins: List[str] = None
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["http://localhost:3000", "http://localhost:5173"]


@dataclass
class TrustConfig:
    """Trust system configuration"""
    starting_trust: float = 0.5
    max_trust: float = 1.0
    min_trust: float = 0.0
    
    # Quarantine
    quarantine_threshold: float = 0.2
    rehabilitation_jobs: int = 10
    rehabilitation_threshold: float = 0.3
    
    # Rewards/Penalties
    success_reward: float = 0.02
    late_reward: float = 0.01
    failure_penalty: float = 0.05
    malicious_penalty: float = 0.50


@dataclass
class NetworkConfig:
    """P2P Network configuration"""
    # Network Mode
    mode: NetworkMode = NetworkMode.PRIVATE

    # ZMQ Ports
    pub_port: int = 5555
    sub_port: int = 5556
    beacon_port: int = 5557

    # Discovery
    discovery_interval: int = 5  # seconds
    heartbeat_interval: int = 3  # seconds

    # Network
    broadcast_address: str = "tcp://*"
    max_peers: int = 50

    # PRIVATE MODE Configuration
    bootstrap_peers: List[str] = field(default_factory=list)  # Manual peer list
    saved_peers_file: str = "~/.marlos/peers.json"  # Saved peers location
    enable_local_bootstrap: bool = False  # Run bootstrap server on this node

    # PUBLIC MODE Configuration
    dht_enabled: bool = False  # Enable DHT for public mode
    dht_port: int = 5559  # DHT listens on separate port
    dht_bootstrap_nodes: List[tuple] = field(default_factory=list)  # Global DHT bootstrap nodes




@dataclass
class ExecutorConfig:
    """Job executor configuration"""
    max_concurrent_jobs: int = 3
    job_timeout: int = 300  # seconds
    docker_enabled: bool = True
    sandbox_enabled: bool = True


@dataclass
class JobDistributionStats:
    """Track job distribution across nodes"""
    node_id: str
    jobs_won: int
    jobs_lost: int
    total_earnings: float
    last_win_time: float
    win_rate: float





@dataclass
class AgentConfig:
    """Main agent configuration"""
    node_id: str = None
    node_name: str = None

    # Sub-configs
    network: NetworkConfig = None
    token: TokenConfig = None
    trust: TrustConfig = None
    rl: RLConfig = None
    executor: ExecutorConfig = None
    dashboard: DashboardConfig = None
    predictive: PredictiveConfig = None
    mqtt_broker_host: str = "mosquitto"
    mqtt_broker_port: int = 1883

    # Storage
    data_dir: str = "./data"
    
    def __post_init__(self):
        import uuid
        if self.node_id is None:
            self.node_id = str(uuid.uuid4())[:8]
        if self.node_name is None:
            self.node_name = f"agent-{self.node_id}"
        
        # Initialize sub-configs
        if self.network is None:
            self.network = NetworkConfig()
        if self.token is None:
            self.token = TokenConfig()
        if self.trust is None:
            self.trust = TrustConfig()
        if self.rl is None:
            self.rl = RLConfig()
        if self.executor is None:
            self.executor = ExecutorConfig()
        if self.dashboard is None:
            self.dashboard = DashboardConfig()
        if self.predictive is None:
            self.predictive = PredictiveConfig()
        
        # Create data directory
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(f"{self.data_dir}/keys", exist_ok=True)
        os.makedirs(f"{self.data_dir}/jobs", exist_ok=True)


def load_config(config_file: str = None) -> AgentConfig:
    """
    Load configuration with two-tier precedence system:
    1. System defaults (from dataclass defaults in this file)
    2. Node config file (from ~/.marlos/nodes/{node_id}/config.json)
    3. Environment variable overrides (highest priority)

    Args:
        config_file: Optional explicit path to config file. If not provided,
                    will look for node config based on NODE_ID env var.

    Returns:
        AgentConfig with all settings merged according to precedence
    """
    import json
    from pathlib import Path

    # Get NODE_ID from environment
    node_id = os.getenv('NODE_ID')

    # Determine config file path
    if config_file is None and node_id:
        # Use node config if NODE_ID is set
        home = Path.home()
        config_file = home / ".marlos" / "nodes" / node_id / "config.json"
        if not config_file.exists():
            print(f"Warning: Node config not found at {config_file}, using defaults")
            config_file = None

    # Start with system defaults
    config_dict = {}

    # Layer 2: Load from node config file if exists
    if config_file and os.path.exists(str(config_file)):
        try:
            with open(config_file) as f:
                config_dict = json.load(f)
            print(f"Loaded config from {config_file}")
        except Exception as e:
            print(f"Error loading config from {config_file}: {e}")
            config_dict = {}

    # Layer 3: Apply environment variable overrides
    # These take highest priority for temporary overrides
    if os.getenv('NODE_ID'):
        config_dict['node_id'] = os.getenv('NODE_ID')
    if os.getenv('PUB_PORT'):
        config_dict.setdefault('network', {})['pub_port'] = int(os.getenv('PUB_PORT'))
    if os.getenv('SUB_PORT'):
        config_dict.setdefault('network', {})['sub_port'] = int(os.getenv('SUB_PORT'))
    if os.getenv('DASHBOARD_PORT'):
        config_dict.setdefault('dashboard', {})['port'] = int(os.getenv('DASHBOARD_PORT'))
    if os.getenv('NETWORK_MODE'):
        mode_str = os.getenv('NETWORK_MODE', 'private').lower()
        config_dict.setdefault('network', {})['mode'] = mode_str
    if os.getenv('DHT_ENABLED'):
        dht = os.getenv('DHT_ENABLED', 'false').lower() == 'true'
        config_dict.setdefault('network', {})['dht_enabled'] = dht
    if os.getenv('BOOTSTRAP_PEERS'):
        peers_str = os.getenv('BOOTSTRAP_PEERS', '')
        peers = [p.strip() for p in peers_str.split(',') if p.strip()]
        config_dict.setdefault('network', {})['bootstrap_peers'] = peers

    # Build config from merged dictionary
    try:
        # Main config
        node_id = config_dict.get('node_id')
        node_name = config_dict.get('node_name')
        data_dir = config_dict.get('data_dir', './data')

        # Network config
        network_dict = config_dict.get('network', {})
        mode_str = network_dict.get('mode', 'private')
        network_mode = NetworkMode.PUBLIC if mode_str == 'public' else NetworkMode.PRIVATE

        network = NetworkConfig(
            mode=network_mode,
            pub_port=network_dict.get('pub_port', 5555),
            sub_port=network_dict.get('sub_port', 5556),
            beacon_port=network_dict.get('beacon_port', 5557),
            discovery_interval=network_dict.get('discovery_interval', 5),
            heartbeat_interval=network_dict.get('heartbeat_interval', 3),
            broadcast_address=network_dict.get('broadcast_address', 'tcp://*'),
            max_peers=network_dict.get('max_peers', 50),
            bootstrap_peers=network_dict.get('bootstrap_peers', []),
            dht_enabled=network_dict.get('dht_enabled', False),
            dht_port=network_dict.get('dht_port', 5559)
        )

        # Token config
        token_dict = config_dict.get('token', {})
        token = TokenConfig(
            starting_balance=token_dict.get('starting_balance', 100.0),
            network_fee=token_dict.get('network_fee', 0.05),
            idle_reward=token_dict.get('idle_reward', 1.0),
            stake_requirement=token_dict.get('stake_requirement', 10.0),
            success_bonus=token_dict.get('success_bonus', 0.20),
            late_penalty=token_dict.get('late_penalty', 0.10),
            failure_penalty=token_dict.get('failure_penalty', 1.0)
        )

        # Trust config
        trust_dict = config_dict.get('trust', {})
        trust = TrustConfig(
            starting_trust=trust_dict.get('starting_trust', 0.5),
            max_trust=trust_dict.get('max_trust', 1.0),
            min_trust=trust_dict.get('min_trust', 0.0),
            quarantine_threshold=trust_dict.get('quarantine_threshold', 0.2),
            rehabilitation_jobs=trust_dict.get('rehabilitation_jobs', 10),
            rehabilitation_threshold=trust_dict.get('rehabilitation_threshold', 0.3),
            success_reward=trust_dict.get('success_reward', 0.02),
            late_reward=trust_dict.get('late_reward', 0.01),
            failure_penalty=trust_dict.get('failure_penalty', 0.05),
            malicious_penalty=trust_dict.get('malicious_penalty', 0.50)
        )

        # RL config
        rl_dict = config_dict.get('rl', {})
        rl = RLConfig(
            model_path=rl_dict.get('model_path', 'rl_trainer/models/policy_v1.zip'),
            state_dim=rl_dict.get('state_dim', 35),
            action_dim=rl_dict.get('action_dim', 3),
            online_learning=rl_dict.get('online_learning', False),
            exploration_rate=rl_dict.get('exploration_rate', 0.1),
            enabled=rl_dict.get('enabled', True)
        )

        # Executor config
        executor_dict = config_dict.get('executor', {})
        executor = ExecutorConfig(
            max_concurrent_jobs=executor_dict.get('max_concurrent_jobs', 3),
            job_timeout=executor_dict.get('job_timeout', 300),
            docker_enabled=executor_dict.get('docker_enabled', True),
            sandbox_enabled=executor_dict.get('sandbox_enabled', True)
        )

        # Dashboard config
        dashboard_dict = config_dict.get('dashboard', {})
        dashboard = DashboardConfig(
            host=dashboard_dict.get('host', '0.0.0.0'),
            port=dashboard_dict.get('port', 3001),
            cors_origins=dashboard_dict.get('cors_origins', None)
        )

        # Predictive config
        predictive_dict = config_dict.get('predictive', {})
        predictive = PredictiveConfig(
            enabled=predictive_dict.get('enabled', False),
            min_pattern_confidence=predictive_dict.get('min_pattern_confidence', 0.75),
            min_occurrences=predictive_dict.get('min_occurrences', 3),
            max_speculation_ratio=predictive_dict.get('max_speculation_ratio', 0.2),
            min_expected_value=predictive_dict.get('min_expected_value', 3.0),
            correct_prediction_reward=predictive_dict.get('correct_prediction_reward', 20),
            wrong_prediction_penalty=predictive_dict.get('wrong_prediction_penalty', 5),
            cache_ttl=predictive_dict.get('cache_ttl', 300),
            max_cache_size=predictive_dict.get('max_cache_size', 100),
            rl_speculation_enabled=predictive_dict.get('rl_speculation_enabled', True),
            rl_model_path=predictive_dict.get('rl_model_path', 'rl_trainer/models/speculation_policy.zip')
        )

        # Create and return AgentConfig
        return AgentConfig(
            node_id=node_id,
            node_name=node_name,
            network=network,
            token=token,
            trust=trust,
            rl=rl,
            executor=executor,
            dashboard=dashboard,
            predictive=predictive,
            data_dir=data_dir
        )

    except Exception as e:
        print(f"Error building config: {e}")
        print("Using system defaults")
        return AgentConfig()
