const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn, exec } = require('child_process'); // Import process managers

let mainWindow;
let pythonProcess = null; // Track the python sidecar

const isDev = process.env.NODE_ENV === 'development';

// ========================================================
// 🐍 PYTHON SIDECAR MANAGEMENT
// ========================================================
function startPythonBackend() {
  console.log('🚀 [ELECTRON] Starting Python backend...');

  // Defines where the 'agent' folder is relative to this file
  // Assuming structure:
  // project-root/
  // ├── agent/
  // └── electron/main.js
  const projectRoot = path.join(__dirname, '..');

  // Spawn python as a child process
  // Uses 'python -m agent.main' to start your node
  pythonProcess = spawn('python', ['-m', 'agent.main'], {
    cwd: projectRoot, // Run from project root so imports work
    shell: true,      // Helps path resolution on Windows
    stdio: 'pipe'     // Allows us to capture stdout/stderr
  });

  // 📝 Pipe Python logs to Electron console
  pythonProcess.stdout.on('data', (data) => {
    // Clean up the output a bit
    console.log(`[PYTHON] ${data.toString().trim()}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`[PYTHON ERROR] ${data.toString().trim()}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`[ELECTRON] Python backend exited with code ${code}`);
  });
  
  pythonProcess.on('error', (err) => {
    console.error('[ELECTRON] Failed to start Python process:', err);
  });
}

function killPythonBackend() {
  if (pythonProcess) {
    console.log('🛑 [ELECTRON] Stopping Python backend...');
    // Windows needs forceful taskkill to ensure sub-processes (like ZMQ threads) die
    if (process.platform === 'win32') {
      try {
        exec(`taskkill /pid ${pythonProcess.pid} /T /F`);
      } catch (e) {
        console.error("Error killing process on Windows:", e);
      }
    } else {
      // Unix/Mac standard kill
      pythonProcess.kill('SIGINT');
    }
    pythonProcess = null;
  }
}

// ========================================================
// 🖥️ ELECTRON WINDOW MANAGEMENT
// ========================================================
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    backgroundColor: '#000000',
    title: 'MarlOS Control Center',
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

// ✅ APP LIFECYCLE HOOKS

// When Electron is ready, start Python AND create window
app.whenReady().then(() => {
  startPythonBackend();
  createWindow();
});

// When user quits, kill Python first
app.on('will-quit', () => {
  killPythonBackend();
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