@echo off
REM MarlOS Node Launcher for Windows
REM Customize this script for your device

REM ============================================
REM CONFIGURATION - EDIT THESE VALUES
REM ============================================

REM Node Identity (make it unique for each device)
set NODE_ID=laptop-1
set NODE_NAME=My-Device

REM Network Ports (default values, change if needed)
set PUB_PORT=5555
set SUB_PORT=5556
set DASHBOARD_PORT=3001

REM Bootstrap Peers - REPLACE WITH YOUR ACTUAL DEVICE IPs
REM Format: tcp://<IP>:<PORT>,tcp://<IP>:<PORT>
REM Example: set BOOTSTRAP_PEERS=tcp://192.168.1.101:5555,tcp://192.168.1.102:5555
set BOOTSTRAP_PEERS=tcp://192.168.1.101:5555,tcp://192.168.1.102:5555

REM Optional: Disable Docker for direct job execution
set ENABLE_DOCKER=false

REM Optional: Enable hardware control via MQTT
set ENABLE_HARDWARE_RUNNER=false
set MQTT_BROKER_HOST=localhost

REM ============================================
REM STARTUP
REM ============================================

echo.
echo ╔═══════════════════════════════════════╗
echo ║     MarlOS Distributed Agent          ║
echo ╚═══════════════════════════════════════╝
echo.
echo 🆔 Node ID:      %NODE_ID%
echo 📛 Node Name:    %NODE_NAME%
echo 📡 Bootstrap:    %BOOTSTRAP_PEERS%
echo 🌐 Dashboard:    http://0.0.0.0:%DASHBOARD_PORT%
echo ⚙️  PUB Port:     %PUB_PORT%
echo ⚙️  SUB Port:     %SUB_PORT%
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
