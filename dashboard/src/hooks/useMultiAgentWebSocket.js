import { useState, useEffect, useCallback, useRef } from 'react';

// Connect to all 3 agents
const AGENT_PORTS = [8001, 8002, 8003];
const RECONNECT_DELAY = 3000;
const MAX_RECONNECT_ATTEMPTS = 10;
const INITIAL_CONNECT_DELAY = 1000;

export const useMultiAgentWebSocket = () => {
  const [agentsState, setAgentsState] = useState({});
  const [connections, setConnections] = useState({});
  const [error, setError] = useState(null);

  const wsRefs = useRef({});
  const reconnectTimeouts = useRef({});
  const reconnectAttempts = useRef({});
  const isConnecting = useRef({});

  const updateAgentState = useCallback((port, state) => {
    setAgentsState(prev => ({
      ...prev,
      [port]: state
    }));
  }, []);

  const updateConnection = useCallback((port, connected) => {
    setConnections(prev => ({
      ...prev,
      [port]: connected
    }));
  }, []);

  const connectToAgent = useCallback((port) => {
    const wsUrl = `ws://localhost:${port}`;

    if (isConnecting.current[port]) {
      console.log(`Connection to port ${port} already in progress, skipping...`);
      return;
    }

    if (reconnectAttempts.current[port] >= MAX_RECONNECT_ATTEMPTS) {
      console.error(`Max reconnection attempts reached for agent on port ${port}`);
      return;
    }

    try {
      isConnecting.current[port] = true;
      console.log(`Connecting to agent on ${wsUrl} (attempt ${(reconnectAttempts.current[port] || 0) + 1})`);

      // Close existing connection if any
      if (wsRefs.current[port] && wsRefs.current[port].readyState !== WebSocket.CLOSED) {
        wsRefs.current[port].close();
      }

      const ws = new WebSocket(wsUrl);
      wsRefs.current[port] = ws;

      ws.onopen = () => {
        console.log(`WebSocket connected to agent on port ${port}`);
        updateConnection(port, true);
        reconnectAttempts.current[port] = 0;
        isConnecting.current[port] = false;
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'initial_state' || data.type === 'state_update') {
            updateAgentState(port, data.data);
          }
        } catch (err) {
          console.error(`Failed to parse message from port ${port}:`, err);
        }
      };

      ws.onerror = (err) => {
        console.error(`WebSocket error on port ${port}:`, err);
        isConnecting.current[port] = false;
      };

      ws.onclose = (event) => {
        console.log(`WebSocket disconnected from port ${port} (code: ${event.code})`);
        updateConnection(port, false);
        isConnecting.current[port] = false;

        // Clear existing timeout
        if (reconnectTimeouts.current[port]) {
          clearTimeout(reconnectTimeouts.current[port]);
        }

        // Attempt reconnect with exponential backoff
        reconnectAttempts.current[port] = (reconnectAttempts.current[port] || 0) + 1;
        const delay = Math.min(
          RECONNECT_DELAY * Math.pow(1.5, reconnectAttempts.current[port] - 1),
          30000
        );

        console.log(`Reconnecting to port ${port} in ${delay}ms`);
        reconnectTimeouts.current[port] = setTimeout(() => {
          connectToAgent(port);
        }, delay);
      };
    } catch (err) {
      console.error(`Failed to create WebSocket for port ${port}:`, err);
      setError(`Failed to connect to agent on port ${port}`);
      isConnecting.current[port] = false;
    }
  }, [updateAgentState, updateConnection]);

  const sendMessage = useCallback((port, message) => {
    const ws = wsRefs.current[port];
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    } else {
      console.warn(`WebSocket not connected for port ${port}`);
    }
  }, []);

  const sendToAll = useCallback((message) => {
    AGENT_PORTS.forEach(port => {
      sendMessage(port, message);
    });
  }, [sendMessage]);

  useEffect(() => {
    // Initialize reconnect attempts
    AGENT_PORTS.forEach(port => {
      reconnectAttempts.current[port] = 0;
      isConnecting.current[port] = false;
    });

    // Delay initial connections
    const initialTimeout = setTimeout(() => {
      AGENT_PORTS.forEach(port => {
        connectToAgent(port);
      });
    }, INITIAL_CONNECT_DELAY);

    return () => {
      clearTimeout(initialTimeout);

      // Cleanup all connections
      AGENT_PORTS.forEach(port => {
        if (reconnectTimeouts.current[port]) {
          clearTimeout(reconnectTimeouts.current[port]);
        }
        if (wsRefs.current[port] && wsRefs.current[port].readyState !== WebSocket.CLOSED) {
          wsRefs.current[port].close();
        }
      });
    };
  }, [connectToAgent]);

  const connectedCount = Object.values(connections).filter(Boolean).length;
  const totalAgents = AGENT_PORTS.length;

  return {
    agentsState,      // Object with port -> agent state
    connections,      // Object with port -> boolean (connected status)
    connectedCount,   // Number of connected agents
    totalAgents,      // Total number of agents
    error,
    sendMessage,      // Send to specific agent
    sendToAll,        // Send to all agents
  };
};
