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
    state_dim: int = 25  # Updated to match new fairness features
    action_dim: int = 3  # BID, FORWARD, DEFER

    # Learning
    online_learning: bool = False
    exploration_rate: float = 0.1
    enabled: bool = False  # Disable RL until model is retrained


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

