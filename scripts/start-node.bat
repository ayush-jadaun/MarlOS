@echo off
REM MarlOS Node Launcher for Windows
REM Template script for launching a MarlOS node

REM ============================================
REM CONFIGURATION - EDIT NODE_ID
REM ============================================

REM Node ID (must match a configured node in ~/.marlos/nodes/)
REM Create nodes using: marl start
REM List nodes using: marl nodes list
set NODE_ID=YOUR_NODE_ID_HERE

REM ============================================
REM OPTIONAL OVERRIDES
REM ============================================
REM These override settings from the node config file
REM Uncomment only if you need temporary overrides

REM set PUB_PORT=5555
REM set SUB_PORT=5556
REM set DASHBOARD_PORT=3001
REM set NETWORK_MODE=private
REM set DHT_ENABLED=false
REM set BOOTSTRAP_PEERS=tcp://192.168.1.101:5555
REM set ENABLE_DOCKER=false
REM set ENABLE_HARDWARE_RUNNER=false

REM ============================================
REM STARTUP
REM ============================================

echo.
echo ╔═══════════════════════════════════════╗
echo ║     MarlOS Distributed Agent          ║
echo ║           v1.0.5                      ║
echo ╚═══════════════════════════════════════╝
echo.
echo 🆔 Node ID:      %NODE_ID%
echo 📁 Config:       ~/.marlos/nodes/%NODE_ID%/config.json
echo.
echo Starting agent...
echo.

REM Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Error: Python 3 not found. Please install Python 3.11+
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist venv\Scripts\activate.bat (
    echo 🔧 Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Run the agent
python -m agent.main

REM Capture exit code
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Agent exited with error code: %ERRORLEVEL%
    echo Check logs at: data\%NODE_ID%\agent.log
    pause
)

exit /b %ERRORLEVEL%
