const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn, exec } = require('child_process'); 
const os = require('os'); 

let mainWindow;
const isDev = process.env.NODE_ENV === 'development';

// 🚨 UPDATED PORTS FOR READINESS CHECK 
// Assuming a multi-node setup or multiple services starting.
const BACKEND_PORTS = [8081, 8082, 8083]; 
const MAX_WAIT_SECONDS = 45; // Increased timeout for multi-node Docker startup

// ========================================================
// 🐳 DOCKER COMPOSE MANAGEMENT (The Containerized Agent)
// ========================================================

/**
 * Checks if the backend's required ports are open on localhost.
 * This ensures the Python application inside Docker is fully initialized.
 */
function waitForBackend(callback) {
  let attempts = 0;
  let isReady = false; // <<< NEW LOCK: Prevents repeated success calls
  const net = require('net');
  
  const checkAllPorts = () => {
    if (isReady) return; // Exit if already successful

    attempts++;
    let portsOpenedCount = 0;
    
    // We will track promises for all connection attempts
    const checks = BACKEND_PORTS.map(port => new Promise(resolve => {
        const socket = net.createConnection({ port: port, host: 'localhost' }, () => {
            socket.end();
            resolve(true); // Port is open
        });

        socket.on('error', () => {
            socket.destroy();
            resolve(false); // Port is closed
        });
        
        // Give connection 200ms before timing out
        setTimeout(() => resolve(false), 200); 
    }));

    // Wait for all checks in this attempt round to finish
    Promise.all(checks).then(results => {
        portsOpenedCount = results.filter(r => r).length;

        if (portsOpenedCount === BACKEND_PORTS.length) {
            if (!isReady) { // Final check before execution
                isReady = true; // Set lock
                console.log(`✅ [READINESS] All required ports (${BACKEND_PORTS.join(',')}) are OPEN after ${attempts} attempts.`);
                callback(); // Execute callback (createWindow) ONCE
            }
        } else if (attempts < MAX_WAIT_SECONDS) {
            // Retry after 1 second
            console.log(`⏱️ [READINESS] Status: ${portsOpenedCount}/${BACKEND_PORTS.length} ports open. Retrying in 1s... (Attempt ${attempts}/${MAX_WAIT_SECONDS})`);
            setTimeout(checkAllPorts, 1000);
        } else {
            // Failed permanently
            console.error(`🚨 [READINESS] Backend failed to start within ${MAX_WAIT_SECONDS}s timeout. Only ${portsOpenedCount}/${BACKEND_PORTS.length} ports opened.`);
            callback(new Error('Backend timeout'));
        }
    });
  };

  // Start the check
  checkAllPorts();
}


function startDockerBackend(callback) {
  console.log('🚀 [DOCKER-START] Launching Python backend via Docker Compose...');

  const projectRoot = path.join(__dirname, '..', '..');
  
  // NOTE: Use spawn instead of exec for better long-running process control, 
  // although exec is simpler for quick commands. Sticking to exec for speed.
  exec('docker compose up -d', { cwd: projectRoot, shell: true }, (err, stdout, stderr) => {
    if (err) {
      console.error(`🚨 [DOCKER-ERROR] Failed to start services. Is Docker Desktop running? Command error: ${stderr.trim()}`);
      callback(new Error('Docker startup failed'));
      return;
    }
    console.log(`✅ [DOCKER-STATUS] Compose command succeeded. Containers are starting...`);
    
    // Start waiting for the application ports to open
    waitForBackend(callback);
  });
}

/**
 * Stops and removes the Docker Compose services when the application quits.
 */
function killDockerBackend() {
  console.log('🛑 [DOCKER-STOP] Initiating clean shutdown...');
  const projectRoot = path.join(__dirname, '..', '..');
  
  exec('docker compose down', { cwd: projectRoot, shell: true }, (err, stdout, stderr) => {
    if (err) {
      console.error('[DOCKER-ERROR] Failed to stop containers cleanly:', stderr.trim());
      return;
    }
    console.log('[DOCKER-STATUS] Services shut down successfully.');
  });
}

// ========================================================
// 🖥️ ELECTRON WINDOW MANAGEMENT
// ========================================================

function createWindow() {
  // Only allow one window instance
  if (BrowserWindow.getAllWindows().length > 0) return; 

  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    backgroundColor: '#000000',
    title: 'AetherOS Control Center',
    icon: path.join(__dirname, 'assets/icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    autoHideMenuBar: !isDev,
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ========================================================
// ✅ APP LIFECYCLE HOOKS
// ========================================================

app.whenReady().then(() => {
  // We launch the Docker backend, and only when the readiness probe succeeds,
  // do we then call createWindow().
  startDockerBackend((err) => {
    if (err) {
      console.error('🚨 APPLICATION LAUNCH FAILED: Backend did not start in time. Check Docker/Python logs.');
      app.quit();
      return;
    }
    createWindow();
  });
});

app.on('will-quit', () => {
    killDockerBackend();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

console.log('[ELECTRON] Main process started');