#!/usr/bin/env python3
"""
Simple test script to submit a job via WebSocket
"""
import asyncio
import json
import websockets
import time
import uuid

async def submit_job():
    # Load test job
    with open('test_job.json', 'r') as f:
        job = json.load(f)

    # Add required fields
    job['job_id'] = job.get('job_id', f"job-{str(uuid.uuid4())[:8]}")
    job['priority'] = job.get('priority', 0.5)
    job['payment'] = job.get('payment', 50.0)
    job['deadline'] = job.get('deadline', time.time() + 300)

    print(f"Submitting job: {job['job_id']}")
    print(f"  Type: {job['job_type']}")
    print(f"  Payment: {job['payment']} AC")
    print(f"  Command: {job['payload']['command']}")
    print()

    # Connect to agent-1 dashboard (port 8081 as per docker-compose.yml)
    uri = "ws://localhost:8081"

    try:
        async with websockets.connect(uri, open_timeout=5) as websocket:
            # Submit job
            request = {
                'type': 'submit_job',
                'job': job
            }

            await websocket.send(json.dumps(request))
            print("Job sent to agent-1!")
            print("Waiting for responses...")

            # Wait for multiple responses
            response_count = 0
            try:
                while response_count < 3:  # Get first 3 responses
                    response = await asyncio.wait_for(websocket.recv(), timeout=3)
                    response_data = json.loads(response)
                    response_count += 1

                    print(f"\nResponse {response_count}: {response_data.get('type')}")

                    if response_data.get('type') == 'job_submitted':
                        if response_data.get('status') == 'success':
                            print(f"  SUCCESS! Job {response_data.get('job_id')} submitted to swarm")
                        else:
                            print(f"  ERROR: {response_data.get('error')}")
                        break
                    elif response_data.get('type') == 'initial_state':
                        print(f"  Received initial state (connected to {response_data['data'].get('node_name')})")
                    elif response_data.get('type') == 'state_update':
                        print(f"  Received state update")
            except asyncio.TimeoutError:
                print("Timeout waiting for more responses")

    except Exception as e:
        print(f"ERROR: {e}")
        print("Make sure agent-1 is running (dashboard on port 8081)")
        print("Run: docker-compose up")

if __name__ == '__main__':
    asyncio.run(submit_job())
