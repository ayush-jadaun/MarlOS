#!/bin/bash
# MarlOS Node Launcher
# Customize this script for your device

# ============================================
# CONFIGURATION - EDIT THESE VALUES
# ============================================

# Node Identity (make it unique for each device)
export NODE_ID="laptop-1"
export NODE_NAME="My-Device"

# Network Ports (default values, change if needed)
export PUB_PORT=5555
export SUB_PORT=5556
export DASHBOARD_PORT=3001

# Bootstrap Peers - REPLACE WITH YOUR ACTUAL DEVICE IPs
# Format: tcp://<IP>:<PORT>,tcp://<IP>:<PORT>
# Example for local network:
#   export BOOTSTRAP_PEERS="tcp://192.168.1.101:5555,tcp://192.168.1.102:5555"
# Example for public IPs:
#   export BOOTSTRAP_PEERS="tcp://203.0.113.45:5555,tcp://198.51.100.89:5555"
export BOOTSTRAP_PEERS="tcp://192.168.1.101:5555,tcp://192.168.1.102:5555"

# Optional: Disable Docker for direct job execution
export ENABLE_DOCKER=false

# Optional: Enable hardware control via MQTT
export ENABLE_HARDWARE_RUNNER=false
export MQTT_BROKER_HOST="localhost"

# Optional: Data directory (default: ./data)
# export DATA_DIR="/var/marlos/data"

# ============================================
# STARTUP
# ============================================

echo "╔═══════════════════════════════════════╗"
echo "║     MarlOS Distributed Agent          ║"
echo "╚═══════════════════════════════════════╝"
echo ""
echo "🆔 Node ID:      $NODE_ID"
echo "📛 Node Name:    $NODE_NAME"
echo "📡 Bootstrap:    $BOOTSTRAP_PEERS"
echo "🌐 Dashboard:    http://0.0.0.0:$DASHBOARD_PORT"
echo "⚙️  PUB Port:     $PUB_PORT"
echo "⚙️  SUB Port:     $SUB_PORT"
echo ""
echo "Starting agent..."
echo ""

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Error: Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

# Run the agent
python -m agent.main

# Capture exit code
exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo ""
    echo "❌ Agent exited with error code: $exit_code"
    echo "Check logs at: data/$NODE_ID/agent.log"
fi

exit $exit_code
