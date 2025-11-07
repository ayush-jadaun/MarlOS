"""
Dashboard WebSocket Server
Provides real-time updates to the dashboard frontend
"""
import asyncio
import json
import logging
from typing import Set
import websockets
from websockets.server import WebSocketServerProtocol

# Configure logging for websockets
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DashboardServer:
    """
    WebSocket server for dashboard communication
    """
    
    def __init__(self, node_id: str, config, agent):
        self.node_id = node_id
        self.config = config
        self.agent = agent
        
        # Connected clients
        self.clients: Set[WebSocketServerProtocol] = set()
        
        # Server
        self.server = None
        self.running = False
    
    async def process_request(self, path, request_headers):
        """
        Process HTTP request before WebSocket upgrade.
        Return None to accept, or (status, headers, body) to reject.
        """
        # Accept all WebSocket upgrade requests
        # request_headers is a websockets Request object
        return None  # Accept the connection

    async def start(self):
        """Start WebSocket server"""
        self.running = True

        try:
            # Start WebSocket server with additional options
            self.server = await websockets.serve(
                self.handle_client,
                self.config.host,
                self.config.port,
                # Add connection parameters for better stability
                ping_interval=20,  # Send ping every 20 seconds
                ping_timeout=30,   # Wait 30 seconds for pong
                close_timeout=5,   # Wait 5 seconds for close handshake
                max_size=10 * 1024 * 1024,  # 10MB max message size
                compression=None,  # Disable compression for lower latency
                process_request=self.process_request  # Handle pre-upgrade requests
            )

            # Start broadcast loop
            asyncio.create_task(self._broadcast_loop())

            print(f"📊 Dashboard server started on ws://{self.config.host}:{self.config.port}")
            print(f"   Accepting connections from: {', '.join(self.config.cors_origins)}")

        except Exception as e:
            print(f"❌ Failed to start dashboard server: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def stop(self):
        """Stop WebSocket server"""
        self.running = False
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
    
    async def handle_client(self, websocket: WebSocketServerProtocol):
        """Handle new client connection"""
        print(f"📡 Dashboard client connecting from {websocket.remote_address}...")

        try:
            # Add client to set
            self.clients.add(websocket)
            print(f"📡 Dashboard client connected ({len(self.clients)} total)")

            # Send initial state (with error handling)
            try:
                initial_data = self.agent.get_state() if self.agent else {}
                await self.send_to_client(websocket, {
                    'type': 'initial_state',
                    'data': initial_data
                })
            except Exception as e:
                print(f"⚠️  Error sending initial state: {e}")
                # Send empty state as fallback
                await self.send_to_client(websocket, {
                    'type': 'initial_state',
                    'data': {'error': 'Failed to load initial state'}
                })

            # Handle messages
            async for message in websocket:
                await self.handle_message(websocket, message)

        except websockets.exceptions.ConnectionClosedError as e:
            print(f"⚠️  WebSocket connection closed unexpectedly: {e}")
        except websockets.exceptions.ConnectionClosedOK:
            print(f"📡 Dashboard client disconnected gracefully")
        except Exception as e:
            print(f"❌ Error in dashboard client handler: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # Ensure client is removed from set
            if websocket in self.clients:
                self.clients.remove(websocket)
                print(f"📡 Dashboard client removed ({len(self.clients)} remaining)")
    
    async def handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """Handle message from client"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'get_state':
                await self.send_to_client(websocket, {
                    'type': 'state_update',
                    'data': self.agent.get_state()
                })
            
            elif msg_type == 'chaos_mode':
                # Kill this node (for demo)
                print("💥 CHAOS MODE ACTIVATED - Shutting down node!")
                asyncio.create_task(self.agent.stop())
            
            elif msg_type == 'submit_job':
                # Submit job from dashboard
                job_data = data.get('job')
                print(f"📤 Job submitted from dashboard: {job_data}")

                # Import at function level to avoid circular imports
                from ..p2p.protocol import MessageType
                import uuid
                import time

                # Ensure required fields have defaults
                job_id = job_data.get('job_id') or f"job-{str(uuid.uuid4())[:8]}"
                deadline = job_data.get('deadline') or time.time() + 300  # 5 min default

                try:
                    # Broadcast job to P2P network
                    # This agent will receive its own broadcast like all other agents
                    # ensuring synchronized auction timing for everyone
                    await self.agent.p2p.broadcast_message(
                        MessageType.JOB_BROADCAST,
                        job_id=job_id,
                        job_type=job_data.get('job_type'),
                        priority=job_data.get('priority', 0.5),
                        payment=job_data.get('payment', 100.0),
                        deadline=deadline,
                        payload=job_data.get('payload', {}),
                        requirements=job_data.get('requirements'),
                        verify=job_data.get('verify', False),
                        verifiers=job_data.get('verifiers', 1)
                    )

                    print(f"✅ Job {job_id} broadcast to swarm")
                    print(f"📥 This agent will receive and process the broadcast like all peers")

                    # Send confirmation back to client
                    await self.send_to_client(websocket, {
                        'type': 'job_submitted',
                        'job_id': job_id,
                        'status': 'success'
                    })

                except Exception as e:
                    print(f"❌ Error broadcasting job: {e}")
                    import traceback
                    traceback.print_exc()

                    # Send error back to client
                    await self.send_to_client(websocket, {
                        'type': 'job_submitted',
                        'job_id': job_id,
                        'status': 'error',
                        'error': str(e)
                    })
        
        except Exception as e:
            print(f"[DASHBOARD] Error handling message: {e}")
    
    async def send_to_client(self, websocket: WebSocketServerProtocol, message: dict):
        """Send message to specific client"""
        try:
            await websocket.send(json.dumps(message))
        except:
            pass
    
    async def broadcast(self, message: dict):
        """Broadcast message to all clients"""
        if self.clients:
            message_json = json.dumps(message)
            await asyncio.gather(
                *[client.send(message_json) for client in self.clients],
                return_exceptions=True
            )
    
    async def _broadcast_loop(self):
        """Periodically broadcast state updates"""
        while self.running:
            await asyncio.sleep(1)  # Update every second
            
            if self.clients:
                await self.broadcast({
                    'type': 'state_update',
                    'data': self.agent.get_state()
                })