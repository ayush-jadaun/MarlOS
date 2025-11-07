

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

