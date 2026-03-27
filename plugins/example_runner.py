"""
Example MarlOS plugin runner.
This file demonstrates how to create a custom runner.

Drop any .py file in the plugins/ directory and it auto-registers
with the MarlOS agent on startup.
"""

from agent.plugins import runner


@runner.register("ping")
async def ping_runner(job: dict) -> dict:
    """Simple ping runner that echoes back the payload."""
    payload = job.get("payload", {})
    message = payload.get("message", "pong")
    return {
        "status": "success",
        "output": f"ping: {message}",
    }


@runner.register("math")
async def math_runner(job: dict) -> dict:
    """Basic math evaluation runner."""
    payload = job.get("payload", {})
    expression = payload.get("expression", "0")

    # Safe evaluation: only allow basic math
    allowed = set("0123456789+-*/(). ")
    if not all(c in allowed for c in expression):
        return {"status": "error", "error": "Invalid expression"}

    try:
        result = eval(expression)  # Safe because we filtered chars above
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}
