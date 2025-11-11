#!/bin/bash
# MarlOS Deployment Test Script
# Tests job execution on real devices

echo "╔════════════════════════════════════════╗"
echo "║   MarlOS Deployment Test Suite        ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Configuration
DASHBOARD_PORT=${DASHBOARD_PORT:-8081}
CLI="python cli/marlOS.py"

echo "📋 Test Configuration:"
echo "   Dashboard Port: $DASHBOARD_PORT"
echo ""

# Test 1: Check if agent is running
echo "🧪 Test 1: Agent Connectivity"
echo -n "   Checking if agent is reachable... "
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$((DASHBOARD_PORT - 5080)) 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ Agent responding"
else
    echo "⚠️  Warning: Cannot reach agent (this is normal if dashboard is WebSocket-only)"
fi
echo ""

# Test 2: Check CLI availability
echo "🧪 Test 2: CLI Availability"
echo -n "   Checking if CLI is available... "
if $CLI --version &>/dev/null; then
    echo "✅ CLI working"
else
    echo "❌ CLI not working"
    exit 1
fi
echo ""

# Test 3: Submit simple echo job
echo "🧪 Test 3: Simple Echo Job"
echo "   Submitting: echo 'Test from deployment script'"
$CLI execute "echo 'Test from deployment script'" --port $DASHBOARD_PORT
echo ""
sleep 2

# Test 4: System info job
echo "🧪 Test 4: System Info Job"
echo "   Submitting: uname -a"
$CLI execute "uname -a" --port $DASHBOARD_PORT
echo ""
sleep 2

# Test 5: Python version job
echo "🧪 Test 5: Python Version Check"
echo "   Submitting: python --version"
$CLI execute "python --version" --port $DASHBOARD_PORT
echo ""
sleep 2

# Test 6: Check swarm status
echo "🧪 Test 6: Swarm Status"
$CLI status --port $DASHBOARD_PORT
echo ""

# Summary
echo "╔════════════════════════════════════════╗"
echo "║   Test Suite Completed                 ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "📊 Next Steps:"
echo "   1. Check dashboard at http://localhost:$((DASHBOARD_PORT - 5080))"
echo "   2. View logs: tail -f data/agent.log"
echo "   3. Watch real-time: $CLI watch --port $DASHBOARD_PORT"
echo ""
echo "💡 Tips:"
echo "   - Jobs are distributed via RL-based auction"
echo "   - Check wallet balance: $CLI wallet --port $DASHBOARD_PORT"
echo "   - List peers: $CLI peers --port $DASHBOARD_PORT"
echo ""
