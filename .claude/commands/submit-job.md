Submit a test job to a running MarlOS node.

$ARGUMENTS should be the job type and optional command, e.g.:
  "shell echo hello"
  "malware_scan"
  "port_scan 192.168.1.1"

Parse $ARGUMENTS: first word is job_type, rest is the command/target.

Run:
```bash
python -c "
import asyncio, json, zmq, time, uuid

job_type = '$ARGUMENTS'.split()[0] if '$ARGUMENTS' else 'shell'
rest = ' '.join('$ARGUMENTS'.split()[1:]) if len('$ARGUMENTS'.split()) > 1 else 'echo hello'

job = {
    'job_id': str(uuid.uuid4())[:8],
    'job_type': job_type,
    'payload': {'command': rest} if job_type == 'shell' else {'target': rest},
    'payment': 100.0,
    'priority': 0.7,
    'deadline': time.time() + 300
}
print('Submitting job:', json.dumps(job, indent=2))

ctx = zmq.Context()
sock = ctx.socket(zmq.PUB)
sock.connect('tcp://localhost:5555')
import time; time.sleep(1)
sock.send_string(json.dumps({'type': 'job_broadcast', **job}))
print('Job submitted!')
sock.close()
ctx.term()
"
```

Then watch the agent logs for the bid/execute/result flow.
