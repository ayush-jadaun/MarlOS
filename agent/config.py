"""
MarlOS Agent Configuration
"""

import os
from dataclasses import dataclass
from typing import List



@dataclass
class RLConfig:
    """Reinforcement learning configuration"""
    model_path: str = "rl_trainer/models/policy_v1.zip"
    state_dim: int = 25  
    action_dim: int = 3  # BID, FORWARD, DEFER

    # Learning
    online_learning: bool = False
    exploration_rate: float = 0.1
    enabled: bool = False 


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
        
        # Create data directory
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(f"{self.data_dir}/keys", exist_ok=True)
        os.makedirs(f"{self.data_dir}/jobs", exist_ok=True)


def load_config(config_file: str = None) -> AgentConfig:
        """Load configuration from file or environment"""
        # First, check for environment variables
        node_id = os.getenv('NODE_ID')
        pub_port = int(os.getenv('PUB_PORT', '5555'))
        sub_port = int(os.getenv('SUB_PORT', '5556'))
        dashboard_port = int(os.getenv('DASHBOARD_PORT', '3001'))

        if config_file and os.path.exists(config_file):
            import yaml
            with open(config_file) as f:
                config_dict = yaml.safe_load(f)

            # Parse YAML into AgentConfig
            try:
                # Main config
                node_id = config_dict.get('node_id')
                node_name = config_dict.get('node_name')
                data_dir = config_dict.get('data_dir', './data')

                # Network config
                network_dict = config_dict.get('network', {})
                network = NetworkConfig(
                    pub_port=network_dict.get('pub_port', 5555),
                    sub_port=network_dict.get('sub_port', 5556),
                    beacon_port=network_dict.get('beacon_port', 5557),
                    discovery_interval=network_dict.get('discovery_interval', 5),
                    heartbeat_interval=network_dict.get('heartbeat_interval', 3),
                    broadcast_address=network_dict.get('broadcast_address', 'tcp://*'),
                    max_peers=network_dict.get('max_peers', 50)
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
                    state_dim=rl_dict.get('state_dim', 18),
                    action_dim=rl_dict.get('action_dim', 3),
                    online_learning=rl_dict.get('online_learning', False),
                    exploration_rate=rl_dict.get('exploration_rate', 0.1)
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

                # Create AgentConfig
                return AgentConfig(
                    node_id=node_id,
                    node_name=node_name,
                    network=network,
                    token=token,
                    trust=trust,
                    rl=rl,
                    executor=executor,
                    dashboard=dashboard,
                    data_dir=data_dir
                )

            except Exception as e:
                print(f"Error parsing YAML config: {e}")
                print("Using default configuration")

        network = NetworkConfig(
            pub_port=pub_port,
            sub_port=sub_port
        )
        dashboard = DashboardConfig(
            port=dashboard_port
        )

        return AgentConfig(
            node_id=node_id,
            network=network,
            dashboard=dashboard
        )
