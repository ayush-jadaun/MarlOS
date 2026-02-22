"""
Tests for the node configuration system (v1.0.5)
Tests the two-tier configuration architecture with precedence
"""

import pytest
import yaml
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from agent import node_config
from agent.config import load_config, NetworkMode


class TestNodeConfigCreation:
    """Test node configuration file creation"""

    def setup_method(self):
        """Set up test environment"""
        # Create a temporary directory for test configs
        self.test_dir = tempfile.mkdtemp()
        self.orig_home = Path.home()

    def teardown_method(self):
        """Clean up test environment"""
        # Remove temporary directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('pathlib.Path.home')
    def test_create_node_config_basic(self, mock_home):
        """Test basic node config creation"""
        mock_home.return_value = Path(self.test_dir)

        node_id, config_path = node_config.create_node_config(
            node_name="test-node",
            network_mode="private",
            bootstrap_peers=["tcp://192.168.1.100:5555"],
            dht_enabled=False,
            pub_port=5555,
            dashboard_port=3001
        )

        # Check that node ID was generated
        assert node_id is not None
        assert node_id.startswith("agent-")

        # Check that config file was created
        assert os.path.exists(config_path)

        # Check config content
        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert config['node']['id'] == node_id
        assert config['node']['name'] == "test-node"
        assert config['network']['mode'] == "private"
        assert config['network']['pub_port'] == 5555
        assert config['dashboard']['port'] == 3001
        assert config['network']['bootstrap_peers'] == ["tcp://192.168.1.100:5555"]
        assert config['network']['dht_enabled'] is False

    @patch('pathlib.Path.home')
    def test_create_node_config_public_mode(self, mock_home):
        """Test node config creation with public mode and DHT"""
        mock_home.return_value = Path(self.test_dir)

        node_id, config_path = node_config.create_node_config(
            node_name="public-node",
            network_mode="public",
            bootstrap_peers=[],
            dht_enabled=True,
            pub_port=5555,
            dashboard_port=3001
        )

        # Check config content
        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert config['network']['mode'] == "public"
        assert config['network']['dht_enabled'] is True
        assert config['network']['bootstrap_peers'] == []

    @patch('pathlib.Path.home')
    def test_list_nodes_empty(self, mock_home):
        """Test listing nodes when none exist"""
        mock_home.return_value = Path(self.test_dir)

        nodes = node_config.list_nodes()
        assert nodes == []

    @patch('pathlib.Path.home')
    def test_list_nodes_with_configs(self, mock_home):
        """Test listing nodes after creating some"""
        mock_home.return_value = Path(self.test_dir)

        # Create two nodes
        node_id1, _ = node_config.create_node_config(node_name="node1", network_mode="private", bootstrap_peers=[], dht_enabled=False, pub_port=5555, dashboard_port=3001)
        node_id2, _ = node_config.create_node_config(node_name="node2", network_mode="public", bootstrap_peers=[], dht_enabled=True, pub_port=5556, dashboard_port=3002)

        # List nodes
        nodes = node_config.list_nodes()

        assert len(nodes) == 2
        node_ids = [n['id'] for n in nodes]
        assert node_id1 in node_ids
        assert node_id2 in node_ids

    @patch('pathlib.Path.home')
    def test_get_node_config(self, mock_home):
        """Test retrieving specific node config"""
        mock_home.return_value = Path(self.test_dir)

        # Create a node
        node_id, _ = node_config.create_node_config(node_name="test-node", network_mode="private", bootstrap_peers=[], dht_enabled=False, pub_port=5555, dashboard_port=3001)

        # Get the config
        config = node_config.load_node_config(node_id)

        assert config is not None
        assert config['node']['id'] == node_id
        assert config['node']['name'] == "test-node"

    @patch('pathlib.Path.home')
    def test_get_nonexistent_node_config(self, mock_home):
        """Test retrieving config for nonexistent node"""
        mock_home.return_value = Path(self.test_dir)

        config = node_config.load_node_config("nonexistent-node")
        assert config is None

    @patch('pathlib.Path.home')
    def test_update_node_config(self, mock_home):
        """Test updating node configuration"""
        mock_home.return_value = Path(self.test_dir)

        # Create a node
        node_id, _ = node_config.create_node_config(node_name="test-node", network_mode="private", bootstrap_peers=[], dht_enabled=False, pub_port=5555, dashboard_port=3001)

        # Update the config
        updates = {
            'network': {
                'pub_port': 6666,
                'bootstrap_peers': ["tcp://10.0.0.1:5555"]
            }
        }
        success = node_config.update_node_config(node_id, updates)

        assert success is True

        # Verify the update
        config = node_config.load_node_config(node_id)
        assert config['network']['pub_port'] == 6666
        assert config['network']['bootstrap_peers'] == ["tcp://10.0.0.1:5555"]

    @patch('pathlib.Path.home')
    def test_delete_node_config(self, mock_home):
        """Test deleting node configuration"""
        mock_home.return_value = Path(self.test_dir)

        # Create a node
        node_id, config_path = node_config.create_node_config(node_name="test-node", network_mode="private", bootstrap_peers=[], dht_enabled=False, pub_port=5555, dashboard_port=3001)

        # Delete the node
        success = node_config.delete_node(node_id)

        assert success is True
        # Note: delete_node removes entire directory, not just config
        node_dir = Path(self.test_dir) / ".marlos" / "nodes" / node_id
        assert not node_dir.exists()

        # Verify it's gone from the list
        nodes = node_config.list_nodes()
        node_ids = [n['id'] for n in nodes]
        assert node_id not in node_ids


class TestConfigPrecedence:
    """Test configuration precedence: Environment > Node Config > Defaults"""

    def setup_method(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.orig_env = os.environ.copy()

    def teardown_method(self):
        """Clean up test environment"""
        # Remove temporary directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        # Restore environment
        os.environ.clear()
        os.environ.update(self.orig_env)

    @patch('pathlib.Path.home')
    def test_node_config_overrides_defaults(self, mock_home):
        """Test that node config values override system defaults"""
        mock_home.return_value = Path(self.test_dir)

        # Create a node with specific settings
        node_id, _ = node_config.create_node_config(
            node_name="custom-node",
            network_mode="public",
            bootstrap_peers=["tcp://192.168.1.50:5555"],
            dht_enabled=True,
            pub_port=7777,
            dashboard_port=4001
        )

        # Set NODE_ID env var
        os.environ['NODE_ID'] = node_id

        # Load config
        config = load_config()

        # Check that node config values were used
        assert config.node_id == node_id
        assert config.network.mode == NetworkMode.PUBLIC
        assert config.network.pub_port == 7777
        assert config.dashboard.port == 4001
        assert config.network.dht_enabled is True

    @patch('pathlib.Path.home')
    def test_env_vars_override_node_config(self, mock_home):
        """Test that environment variables override node config"""
        mock_home.return_value = Path(self.test_dir)

        # Create a node
        node_id, _ = node_config.create_node_config(
            node_name="test-node",
            network_mode="private",
            bootstrap_peers=[],
            dht_enabled=False,
            pub_port=5555,
            dashboard_port=3001
        )

        # Set environment variables to override
        os.environ['NODE_ID'] = node_id
        os.environ['PUB_PORT'] = '9999'
        os.environ['DASHBOARD_PORT'] = '5001'
        os.environ['NETWORK_MODE'] = 'public'
        os.environ['DHT_ENABLED'] = 'true'

        # Load config
        config = load_config()

        # Check that env vars took precedence
        assert config.network.pub_port == 9999
        assert config.dashboard.port == 5001
        assert config.network.mode == NetworkMode.PUBLIC
        assert config.network.dht_enabled is True

    def test_system_defaults_when_no_node_config(self):
        """Test that system defaults are used when no node config exists"""
        # Don't set NODE_ID, so no node config will be loaded
        if 'NODE_ID' in os.environ:
            del os.environ['NODE_ID']

        # Load config
        config = load_config()

        # Check that defaults were used
        assert config.network.pub_port == 5555  # Default value
        assert config.dashboard.port == 3001    # Default value
        assert config.network.mode == NetworkMode.PRIVATE  # Default

    @patch('pathlib.Path.home')
    def test_partial_env_overrides(self, mock_home):
        """Test that partial env var overrides work correctly"""
        mock_home.return_value = Path(self.test_dir)

        # Create a node
        node_id, _ = node_config.create_node_config(
            node_name="test-node",
            network_mode="private",
            bootstrap_peers=["tcp://192.168.1.100:5555"],
            dht_enabled=False,
            pub_port=5555,
            dashboard_port=3001
        )

        # Set only some env vars
        os.environ['NODE_ID'] = node_id
        os.environ['PUB_PORT'] = '8888'  # Override only this

        # Load config
        config = load_config()

        # Check precedence
        assert config.network.pub_port == 8888  # From env
        assert config.dashboard.port == 3001   # From node config
        assert config.network.bootstrap_peers == ["tcp://192.168.1.100:5555"]  # From node config


class TestConfigValidation:
    """Test configuration validation and error handling"""

    def setup_method(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('pathlib.Path.home')
    def test_invalid_network_mode(self, mock_home):
        """Test handling of invalid network mode"""
        mock_home.return_value = Path(self.test_dir)

        # Create config with invalid mode - should default to private
        node_id, config_path = node_config.create_node_config(
            node_name="test-node",
            network_mode="invalid_mode",
            bootstrap_peers=[],
            dht_enabled=False,
            pub_port=5555,
            dashboard_port=3001
        )

        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Should store the invalid value, but loader will handle it
        assert config['network']['mode'] == "invalid_mode"

    @patch('pathlib.Path.home')
    def test_missing_node_config_file(self, mock_home):
        """Test handling of missing node config file"""
        mock_home.return_value = Path(self.test_dir)

        # Try to load config for non-existent node
        os.environ['NODE_ID'] = 'non-existent-node'

        # Should fall back to defaults without error
        config = load_config()
        assert config is not None

    @patch('pathlib.Path.home')
    def test_corrupted_json_config(self, mock_home):
        """Test handling of corrupted YAML config file"""
        mock_home.return_value = Path(self.test_dir)

        # Create a node
        node_id, config_path = node_config.create_node_config(
            node_name="test-node",
            network_mode="private",
            bootstrap_peers=[],
            dht_enabled=False,
            pub_port=5555,
            dashboard_port=3001
        )

        # Corrupt the config file
        with open(config_path, 'w') as f:
            f.write("{ invalid yaml: [unclosed")

        os.environ['NODE_ID'] = node_id

        # Should fall back to defaults
        config = load_config()
        assert config is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
