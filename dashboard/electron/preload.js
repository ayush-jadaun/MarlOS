// electron/preload.js
// Preload script - runs before renderer, has access to both Node and browser APIs

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods to renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  // Get backend WebSocket URL
  getBackendUrl: () => ipcRenderer.invoke('get-backend-url'),
  
  // Get app version
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  
  // Get platform
  getPlatform: () => ipcRenderer.invoke('get-platform'),
  
  // Check if running in Electron
  isElectron: true,
});

console.log('✅ Preload script loaded');