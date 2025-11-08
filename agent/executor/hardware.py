"""
marlos/executor/hardware.py
"""
import paho.mqtt.client as mqtt
from .engine import JobResult, JobStatus
import time

class HardwareRunner:
    
    def __init__(self, mqtt_client: mqtt.Client, command_topic: str):
        self.mqtt_client = mqtt_client
        self.command_topic = command_topic
        print(f"🛰️  HardwareRunner initialized. Will send commands to: {command_topic}")

    # --- THIS IS THE CORRECTED METHOD ---
    async def run(self, job: dict) -> JobResult:
        """
        Executes the hardware job by publishing to MQTT.
        """
        start_time = time.time()
        job_id = job.get('job_id', 'unknown-job')
        output = None
        error = None
        status = JobStatus.FAILURE # Assume failure until success
        
        try:
            command = job.get('payload', {}).get('command')
            
            if command not in ["ON", "OFF"]:
                error = f"Unknown hardware command: '{command}'"
                print(f"[EXECUTOR] Error: {error}")
            else:
                # This is the success path
                print(f"[MQTT-OUT] Sending command '{command}' to {self.command_topic}")
                self.mqtt_client.publish(self.command_topic, command)
                output = {"message": f"Command '{command}' sent to hardware."}
                status = JobStatus.SUCCESS
        
        except Exception as e:
            # This catches errors during publish
            error = f"Failed to publish MQTT command: {e}"
            print(f"[EXECUTOR] Error: {error}")
        
        # Finally, create a complete JobResult object
        end_time = time.time()
        duration = end_time - start_time
        
        return JobResult(
            job_id=job_id,
            status=status,
            output=output,
            error=error,
            start_time=start_time,
            end_time=end_time,
            duration=duration
        )