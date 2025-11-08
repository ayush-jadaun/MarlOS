import { useState, useEffect, useCallback, useRef } from 'react';

const WEBSOCKET_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:3002';
const RECONNECT_DELAY = 3000;
const MAX_RECONNECT_ATTEMPTS = 10;
const INITIAL_CONNECT_DELAY = 1000; // Wait 1 second before first connection

export const useWebSocket = () => {
  const [agentState, setAgentState] = useState(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);
  const ws = useRef(null);
  const reconnectTimeout = useRef(null);
  const reconnectAttempts = useRef(0);
  const isConnecting = useRef(false);

  const connect = useCallback(() => {
    // Prevent multiple simultaneous connection attempts
    if (isConnecting.current) {
      console.log('Connection attempt already in progress, skipping...');
      return;
    }

    // Stop reconnecting after max attempts
    if (reconnectAttempts.current >= MAX_RECONNECT_ATTEMPTS) {
      console.error('Max reconnection attempts reached');
      setError('Failed to connect after multiple attempts. Please refresh the page.');
      return;
    }

    try {
      isConnecting.current = true;
      console.log(`Connecting to WebSocket: ${WEBSOCKET_URL} (attempt ${reconnectAttempts.current + 1})`);

      // Close existing connection if any
      if (ws.current && ws.current.readyState !== WebSocket.CLOSED) {
        ws.current.close();
      }

      ws.current = new WebSocket(WEBSOCKET_URL);

      ws.current.onopen = () => {
        console.log('WebSocket connected successfully');
        setConnected(true);
        setError(null);
        reconnectAttempts.current = 0; // Reset counter on successful connection
        isConnecting.current = false;
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'initial_state' || data.type === 'state_update') {
            setAgentState(data.data);
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.current.onerror = (err) => {
        console.error('WebSocket error:', err);
        setError('Connection error');
        isConnecting.current = false;
      };

      ws.current.onclose = (event) => {
        console.log(`WebSocket disconnected (code: ${event.code}, reason: ${event.reason || 'unknown'})`);
        setConnected(false);
        isConnecting.current = false;

        // Clear any existing reconnect timeout
        if (reconnectTimeout.current) {
          clearTimeout(reconnectTimeout.current);
        }

        // Attempt to reconnect with exponential backoff
        reconnectAttempts.current += 1;
        const delay = Math.min(RECONNECT_DELAY * Math.pow(1.5, reconnectAttempts.current - 1), 30000);

        console.log(`Attempting to reconnect in ${delay}ms (attempt ${reconnectAttempts.current}/${MAX_RECONNECT_ATTEMPTS})`);

        reconnectTimeout.current = setTimeout(() => {
          connect();
        }, delay);
      };
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError('Failed to connect');
      isConnecting.current = false;
    }
  }, []);

  const sendMessage = useCallback((message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected');
    }
  }, []);

  const submitJob = useCallback((job) => {
    sendMessage({ type: 'submit_job', job });
  }, [sendMessage]);

  const requestState = useCallback(() => {
    sendMessage({ type: 'get_state' });
  }, [sendMessage]);

  useEffect(() => {
    // Delay initial connection to allow server to fully start
    const initialTimeout = setTimeout(() => {
      connect();
    }, INITIAL_CONNECT_DELAY);

    return () => {
      clearTimeout(initialTimeout);
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current && ws.current.readyState !== WebSocket.CLOSED) {
        ws.current.close();
      }
    };
  }, [connect]);

  return {
    agentState,
    connected,
    error,
    submitJob,
    requestState,
  };
};
