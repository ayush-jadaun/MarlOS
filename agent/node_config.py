"""
Node Configuration Management
Per-node instance-specific configuration
"""
import os
import yaml
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


def generate_node_id() -> str:
    """Generate unique node ID"""
    return f"agent-{uuid.uuid4().hex[:8]}"


def get_node_directory(node_id: str) -> Path:
    """Get node directory path"""
    return Path.home() / ".marlos" / "nodes" / node_id


def create_node_config(
    node_id: Optional[str] = None,
    node_name: Optional[str] = None,
    network_mode: str = "private",
    bootstrap_peers: list = None,
    dht_enabled: bool = False,
    pub_port: int = 5555,
    dashboard_port: int = 3001,
    **kwargs
) -> tuple[str, Path]:
    """
    Create a new node configuration

    Args:
        node_id: Node ID (auto-generated if None)
        node_name: Human-readable name
        network_mode: 'private' or 'public'
        bootstrap_peers: List of bootstrap peer addresses
        dht_enabled: Enable DHT for public mode
        pub_port: Publisher port
        dashboard_port: Dashboard port
        **kwargs: Additional overrides

    Returns:
        Tuple of (node_id, config_path)
    """

    # Generate node ID if not provided
    if not node_id:
        node_id = generate_node_id()

    if not node_name:
        node_name = node_id

    # Create node directory structure
    node_dir = get_node_directory(node_id)
    node_dir.mkdir(parents=True, exist_ok=True)

    data_dir = node_dir / "data"
    data_dir.mkdir(exist_ok=True)

    keys_dir = data_dir / "keys"
    keys_dir.mkdir(exist_ok=True)

    logs_dir = node_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Create node config
    config = {
        "# MarlOS Node Configuration": None,
        "# Auto-generated per-node instance config": None,
        "# System-wide settings in: agent-config.yml": None,
        "": None,

        "node": {
            "id": node_id,
            "name": node_name,
            "created_at": datetime.now().isoformat(),
            "system_config": "./agent-config.yml"
        },

        "network": {
            "mode": network_mode,
            "bootstrap_peers": bootstrap_peers or [],
            "pub_port": pub_port,
            "sub_port": pub_port + 1,
            "dht_enabled": dht_enabled,
            "dht_port": 5559 if dht_enabled else None
        },

        "paths": {
            "data_dir": str(data_dir),
            "log_dir": str(logs_dir),
            "keys_dir": str(keys_dir)
        },

        "dashboard": {
            "port": dashboard_port
        }
    }

    # Add optional overrides
    if kwargs:
        config["overrides"] = kwargs

    # Save config
    config_path = node_dir / "config.yaml"

    # Remove None entries from config before writing
    config_clean = {k: v for k, v in config.items() if v is not None and not k.startswith("#")}

    with open(config_path, 'w') as f:
        # Write header comments
        f.write("# MarlOS Node Configuration\n")
        f.write("# Auto-generated per-node instance config\n")
        f.write(f"# Node ID: {node_id}\n")
        f.write(f"# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("#\n")
        f.write("# System-wide settings: See agent-config.yml\n")
        f.write("# This file: Node-specific overrides\n")
        f.write("\n")

        yaml.dump(config_clean, f, default_flow_style=False, sort_keys=False)

    print(f"[NODE CONFIG] Created node: {node_id}")
    print(f"[NODE CONFIG] Config: {config_path}")
    print(f"[NODE CONFIG] Data dir: {data_dir}")

    return node_id, config_path


def load_node_config(node_id: str) -> Optional[Dict[str, Any]]:
    """Load node configuration"""
    config_path = get_node_directory(node_id) / "config.yaml"

    if not config_path.exists():
        return None

    with open(config_path) as f:
        return yaml.safe_load(f)


def list_nodes() -> list[Dict[str, Any]]:
    """List all registered nodes"""
    nodes_dir = Path.home() / ".marlos" / "nodes"

    if not nodes_dir.exists():
        return []

    nodes = []
    for node_dir in nodes_dir.iterdir():
        if node_dir.is_dir():
            config_path = node_dir / "config.yaml"
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        config = yaml.safe_load(f)
                        nodes.append({
                            "id": config["node"]["id"],
                            "name": config["node"]["name"],
                            "created_at": config["node"].get("created_at"),
                            "config_path": str(config_path),
                            "network_mode": config["network"].get("mode", "unknown")
                        })
                except Exception as e:
                    print(f"[WARNING] Could not load config for {node_dir.name}: {e}")

    return sorted(nodes, key=lambda x: x.get("created_at", ""), reverse=True)


def update_node_config(node_id: str, updates: Dict[str, Any]) -> bool:
    """Update node configuration"""
    config_path = get_node_directory(node_id) / "config.yaml"

    if not config_path.exists():
        return False

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Deep merge updates
    def deep_update(d, u):
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = deep_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    config = deep_update(config, updates)

    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    return True


def delete_node(node_id: str, keep_data: bool = False) -> bool:
    """Delete node configuration and optionally data"""
    node_dir = get_node_directory(node_id)

    if not node_dir.exists():
        return False

    if keep_data:
        # Only delete config, keep data
        config_path = node_dir / "config.yaml"
        if config_path.exists():
            config_path.unlink()
    else:
        # Delete entire node directory
        import shutil
        shutil.rmtree(node_dir)

    return True
