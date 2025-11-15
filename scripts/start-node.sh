#!/bin/bash
# MarlOS Node Launcher
# Template script for launching a MarlOS node

# ============================================
# CONFIGURATION - EDIT NODE_ID
# ============================================

# Node ID (must match a configured node in ~/.marlos/nodes/)
# Create nodes using: marl start
# List nodes using: marl nodes list
export NODE_ID="YOUR_NODE_ID_HERE"

# ============================================
# OPTIONAL OVERRIDES
# ============================================
# These override settings from the node config file
# Uncomment only if you need temporary overrides

# export PUB_PORT=5555
# export SUB_PORT=5556
# export DASHBOARD_PORT=3001
# export NETWORK_MODE="private"
# export DHT_ENABLED="false"
# export BOOTSTRAP_PEERS="tcp://192.168.1.101:5555"
# export ENABLE_DOCKER=false
# export ENABLE_HARDWARE_RUNNER=false

# ============================================
# STARTUP
# ============================================

echo "╔═══════════════════════════════════════╗"
echo "║     MarlOS Distributed Agent          ║"
echo "║           v1.0.5                      ║"
echo "╚═══════════════════════════════════════╝"
echo ""
echo "🆔 Node ID:      $NODE_ID"
echo "📁 Config:       ~/.marlos/nodes/$NODE_ID/config.json"
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
