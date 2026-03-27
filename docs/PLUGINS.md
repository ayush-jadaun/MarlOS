# MarlOS Plugin Development Guide

This guide covers everything you need to build custom job runners for MarlOS. Plugins let you extend the network with new capabilities -- from simple utilities to GPU inference pipelines -- without touching core agent code.

---

## Table of Contents

1. [How the Plugin System Works](#how-the-plugin-system-works)
2. [Your First Runner in 5 Minutes](#your-first-runner-in-5-minutes)
3. [The @runner.register Decorator](#the-runnerregister-decorator)
4. [Input/Output Format](#inputoutput-format)
5. [Available Job Payload Fields](#available-job-payload-fields)
6. [Error Handling](#error-handling)
7. [Testing Your Plugin](#testing-your-plugin)
8. [Advanced Topics](#advanced-topics)
9. [Example Runners](#example-runners)

---

## How the Plugin System Works

MarlOS uses **auto-discovery** to load plugins at startup. Here is the full lifecycle:

1. You drop a `.py` file into the `plugins/` directory at the project root.
2. When a MarlOS agent starts, `PluginLoader` scans that directory for all `.py` files (sorted alphabetically).
3. Files whose names start with `_` (e.g., `_helpers.py`) are skipped -- use them for private utilities.
4. Each file is imported as a module. Any `@runner.register("job_type")` decorators inside the file add runners to a global registry.
5. The registered runners are handed to the `ExecutionEngine`, which treats them identically to built-in runners (shell, docker, etc.).
6. When a job arrives with a matching `job_type`, the engine calls your runner function.

```
plugins/
  example_runner.py    <-- auto-loaded (registers "ping" and "math")
  my_scraper.py        <-- auto-loaded (registers "web_scrape")
  _utils.py            <-- skipped (starts with underscore)
```

Key source files:
- `agent/plugins/loader.py` -- `PluginLoader` class and `runner` singleton
- `agent/plugins/__init__.py` -- exports `PluginLoader` and `runner`
- `agent/executor/engine.py` -- `ExecutionEngine` that calls your runner
- `agent/main.py` -- where plugins are loaded during agent startup (`_register_job_runners`)

### What happens if a plugin fails to load?

The loader catches all exceptions. A broken plugin logs an error but does not crash the agent or block other plugins from loading.

---

## Your First Runner in 5 Minutes

### Step 1: Create the file

Create a new file in the `plugins/` directory. The filename does not matter (as long as it does not start with `_`), but a descriptive name helps.

```bash
touch plugins/hello_runner.py
```

### Step 2: Write the runner

```python
"""My first MarlOS plugin."""

from agent.plugins import runner


@runner.register("hello")
async def hello_runner(job: dict) -> dict:
    payload = job.get("payload", {})
    name = payload.get("name", "World")
    return {
        "status": "success",
        "output": f"Hello, {name}!",
    }
```

That is it. Three things to remember:
- Import `runner` from `agent.plugins`
- Decorate with `@runner.register("your_job_type")`
- Make the function `async` and accept a `dict`, return a `dict`

### Step 3: Start the agent

```bash
NODE_ID=dev-node python -m agent.main
```

You should see in the startup logs:

```
[PLUGIN] Registered runner: hello
[PLUGIN] Loaded 1 plugin runner(s): hello
```

### Step 4: Submit a job

```bash
marl execute --job-type hello --payload '{"name": "MarlOS"}'
```

Or via Python:

```python
from cli.marlOS import submit_job

submit_job({
    "job_type": "hello",
    "payload": {"name": "MarlOS"},
    "payment": 10.0,
})
```

---

## The @runner.register Decorator

```python
from agent.plugins import runner

@runner.register("my_job_type")
async def my_function(job: dict) -> dict:
    ...
```

### How it works

`runner` is a singleton instance of `_RunnerRegistry`. When you call `@runner.register("my_job_type")`, it stores a mapping from the string `"my_job_type"` to your function. Later, the `ExecutionEngine` looks up runners by job type string.

### Rules

| Rule | Details |
|------|---------|
| Job type must be unique | If two plugins register the same job type, the last one loaded wins (alphabetical file order). |
| Function must be `async` | The execution engine calls your function with `await`. A synchronous function will raise a runtime error. |
| Function signature | Must accept a single `dict` argument and return a `dict`. |
| One file, multiple runners | You can register as many job types as you want in a single file. |

### Registering multiple runners in one file

```python
from agent.plugins import runner

@runner.register("compress")
async def compress_runner(job: dict) -> dict:
    ...

@runner.register("decompress")
async def decompress_runner(job: dict) -> dict:
    ...
```

---

## Input/Output Format

### Input: the job dict

Your runner receives the full job dictionary. Here is a typical example:

```python
{
    "job_id": "job-a1b2c3d4",
    "job_type": "hello",            # matches your @runner.register string
    "payload": {                     # your custom data -- any structure you want
        "name": "MarlOS",
    },
    "payment": 100.0,               # AC tokens offered for this job
    "priority": 0.5,                # 0.0 (low) to 1.0 (urgent)
    "deadline": 1711555200.0,        # Unix timestamp -- job must finish before this
    "timestamp": 1711554900.0,       # when the job was created
}
```

Your runner should read from `job["payload"]` for task-specific input. The other fields are metadata managed by the framework.

### Output: the result dict

Return a dictionary. The engine wraps it into a `JobResult` dataclass, but your runner only needs to return a plain dict.

**Success:**

```python
return {
    "status": "success",
    "output": "the result data",    # can be a string, number, dict, list -- anything serializable
}
```

**Partial result with extra metadata:**

```python
return {
    "status": "success",
    "result": 42,
    "details": {"iterations": 1000, "converged": True},
}
```

**Failure (handled by your code, not an exception):**

```python
return {
    "status": "error",
    "error": "File not found: /data/input.csv",
}
```

The engine does not enforce a strict schema on your return dict. However, including a `"status"` field (`"success"` or `"error"`) is the established convention.

---

## Available Job Payload Fields

The `payload` dict is entirely defined by you -- the plugin author. There is no enforced schema. However, these are the **top-level job fields** that the framework sets before your runner sees the job:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `job_id` | `str` | Auto-generated (e.g., `"job-a1b2c3d4"`) | Unique identifier for this job. |
| `job_type` | `str` | **Required** | Must match your `@runner.register` string. |
| `payload` | `dict` | **Required** | Your custom input data. Define whatever fields you need. |
| `payment` | `float` | `100.0` | Token payment in AC (MarlCredits). |
| `priority` | `float` | `0.5` | Priority from 0.0 (low) to 1.0 (critical). |
| `deadline` | `float` | `time.time() + 300` | Unix timestamp. The engine enforces a timeout based on this. |
| `timestamp` | `float` | `time.time()` | When the job was originally created. |
| `requirements` | `list[str]` | `[]` | Optional list of capabilities the runner needs (used by the bidding/routing layer). |

### Designing your payload

Document what your plugin expects. For example, a web scraper might expect:

```python
"payload": {
    "url": "https://example.com",
    "selector": "h1.title",
    "timeout": 10
}
```

---

## Error Handling

There are two ways errors surface from a plugin:

### 1. Return an error dict (preferred for expected failures)

```python
@runner.register("divide")
async def divide_runner(job: dict) -> dict:
    payload = job.get("payload", {})
    a = payload.get("a", 0)
    b = payload.get("b", 1)

    if b == 0:
        return {"status": "error", "error": "Division by zero"}

    return {"status": "success", "result": a / b}
```

This gives the caller a clean error message. The job is marked as `FAILURE` by the engine.

### 2. Raise an exception (for unexpected failures)

If your runner raises an unhandled exception, the execution engine catches it and marks the job as `FAILURE` with the exception message as the error string. The agent does not crash.

```python
@runner.register("risky")
async def risky_runner(job: dict) -> dict:
    data = job["payload"]["data"]  # KeyError if missing -- engine catches it
    result = expensive_computation(data)
    return {"status": "success", "result": result}
```

### 3. Timeouts

The engine enforces a timeout derived from `job["deadline"]`. If your runner does not finish in time, it is cancelled via `asyncio.TimeoutError` and the job is marked as `TIMEOUT`. You do not need to handle this yourself, but you can use it to do cleanup:

```python
@runner.register("long_task")
async def long_task_runner(job: dict) -> dict:
    try:
        result = await some_long_operation()
        return {"status": "success", "result": result}
    except asyncio.CancelledError:
        # Optional: cleanup resources
        await cleanup_temp_files()
        raise  # Re-raise so the engine marks it as timeout
```

### Best practices

- Validate `payload` fields early and return clear error messages.
- Do not silently swallow exceptions -- either handle them with a meaningful error dict or let them propagate.
- Set reasonable defaults with `.get("field", default)` so callers can omit optional fields.

---

## Testing Your Plugin

### Unit test without running an agent

Plugins are just async functions. Test them directly with pytest:

```python
# test/plugins/test_my_plugin.py

import pytest
from agent.plugins.loader import PluginLoader, runner


class TestMyPlugin:
    def setup_method(self):
        """Clear the global registry before each test."""
        runner.clear()

    @pytest.mark.asyncio
    async def test_hello_success(self):
        # Load plugins from the project plugins/ directory
        from pathlib import Path
        plugins_dir = Path(__file__).parent.parent.parent / "plugins"
        loader = PluginLoader(str(plugins_dir))
        runners = loader.discover_and_load()

        result = await runners["hello"]({"payload": {"name": "Test"}})
        assert result["status"] == "success"
        assert "Test" in result["output"]

    @pytest.mark.asyncio
    async def test_hello_default_name(self):
        from pathlib import Path
        plugins_dir = Path(__file__).parent.parent.parent / "plugins"
        loader = PluginLoader(str(plugins_dir))
        runners = loader.discover_and_load()

        result = await runners["hello"]({"payload": {}})
        assert result["status"] == "success"
        assert "World" in result["output"]
```

### Isolated test (no file loading)

You can also test the function directly without the loader:

```python
import pytest
from agent.plugins import runner


class TestDivideRunner:
    def setup_method(self):
        runner.clear()

    @pytest.mark.asyncio
    async def test_divide(self):
        @runner.register("divide")
        async def divide_runner(job: dict) -> dict:
            a = job["payload"]["a"]
            b = job["payload"]["b"]
            if b == 0:
                return {"status": "error", "error": "Division by zero"}
            return {"status": "success", "result": a / b}

        runners = runner.get_runners()
        result = await runners["divide"]({"payload": {"a": 10, "b": 2}})
        assert result["result"] == 5.0

    @pytest.mark.asyncio
    async def test_divide_by_zero(self):
        @runner.register("divide")
        async def divide_runner(job: dict) -> dict:
            a = job["payload"]["a"]
            b = job["payload"]["b"]
            if b == 0:
                return {"status": "error", "error": "Division by zero"}
            return {"status": "success", "result": a / b}

        runners = runner.get_runners()
        result = await runners["divide"]({"payload": {"a": 10, "b": 0}})
        assert result["status"] == "error"
```

### Run the tests

```bash
# Run all plugin tests
python -m pytest test/plugins/ -v

# Run with timeout guard
python -m pytest test/plugins/ -v --timeout=30
```

---

## Advanced Topics

### Async operations

Your runner is an async function, so you can use `await` freely. This is the recommended way to do I/O:

```python
import aiohttp
from agent.plugins import runner


@runner.register("fetch_url")
async def fetch_url_runner(job: dict) -> dict:
    url = job["payload"]["url"]

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            text = await resp.text()
            return {
                "status": "success",
                "result": {
                    "status_code": resp.status,
                    "body_length": len(text),
                    "body": text[:5000],  # Truncate large responses
                },
            }
```

### Running blocking/synchronous code

If you must call a blocking library (e.g., a CPU-bound computation, a synchronous SDK), use `asyncio.to_thread` to avoid blocking the event loop:

```python
import asyncio
from agent.plugins import runner


def heavy_computation(data):
    """This is a blocking function."""
    import time
    time.sleep(5)  # Simulates CPU work
    return sum(data)


@runner.register("compute")
async def compute_runner(job: dict) -> dict:
    data = job["payload"]["data"]
    result = await asyncio.to_thread(heavy_computation, data)
    return {"status": "success", "result": result}
```

### External dependencies

Plugins can import any Python package installed in the agent's environment. If your plugin needs a third-party library:

1. Add it to your environment: `pip install aiohttp beautifulsoup4`
2. Import it at the top of your plugin file.
3. If the dependency is optional, handle the import gracefully:

```python
from agent.plugins import runner

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


@runner.register("csv_analysis")
async def csv_runner(job: dict) -> dict:
    if not HAS_PANDAS:
        return {"status": "error", "error": "pandas is not installed"}

    # ... use pandas ...
```

### Accessing the filesystem

Plugins run in the same process as the agent, so they have access to the local filesystem. Use `pathlib` or standard file I/O:

```python
import asyncio
from pathlib import Path
from agent.plugins import runner


@runner.register("read_file")
async def read_file_runner(job: dict) -> dict:
    file_path = Path(job["payload"]["path"])

    if not file_path.exists():
        return {"status": "error", "error": f"File not found: {file_path}"}

    # Read in a thread to avoid blocking
    content = await asyncio.to_thread(file_path.read_text)
    return {
        "status": "success",
        "result": {
            "path": str(file_path),
            "size": file_path.stat().st_size,
            "content": content[:10000],
        },
    }
```

### Subprocess execution

For running external commands from a plugin:

```python
import asyncio
from agent.plugins import runner


@runner.register("run_script")
async def run_script_runner(job: dict) -> dict:
    script = job["payload"]["script"]

    proc = await asyncio.create_subprocess_shell(
        script,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        return {
            "status": "error",
            "error": stderr.decode().strip(),
            "returncode": proc.returncode,
        }

    return {
        "status": "success",
        "output": stdout.decode().strip(),
    }
```

### Accessing job metadata

Your runner receives the full job dict, so you can read framework fields for decision-making:

```python
import time
from agent.plugins import runner


@runner.register("priority_aware")
async def priority_runner(job: dict) -> dict:
    priority = job.get("priority", 0.5)
    deadline = job.get("deadline", time.time() + 300)
    time_left = deadline - time.time()

    if time_left < 10:
        # Rush mode -- use a faster but less accurate algorithm
        result = fast_algorithm(job["payload"])
    else:
        result = thorough_algorithm(job["payload"])

    return {"status": "success", "result": result}
```

---

## Example Runners

### Ping runner

The simplest possible plugin. Echoes back a message.

```python
# plugins/ping_runner.py

from agent.plugins import runner


@runner.register("ping")
async def ping_runner(job: dict) -> dict:
    payload = job.get("payload", {})
    message = payload.get("message", "pong")
    return {
        "status": "success",
        "output": f"ping: {message}",
    }
```

**Submit:**
```python
submit_job({"job_type": "ping", "payload": {"message": "hello"}, "payment": 5.0})
```

---

### Math runner

Safe arithmetic evaluation with input sanitization.

```python
# plugins/math_runner.py

from agent.plugins import runner


@runner.register("math")
async def math_runner(job: dict) -> dict:
    payload = job.get("payload", {})
    expression = payload.get("expression", "0")

    # Only allow digits and basic math operators
    allowed = set("0123456789+-*/(). ")
    if not all(c in allowed for c in expression):
        return {"status": "error", "error": "Invalid characters in expression"}

    try:
        result = eval(expression)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

**Submit:**
```python
submit_job({"job_type": "math", "payload": {"expression": "2 + 3 * 4"}, "payment": 5.0})
# Returns: {"status": "success", "result": 14}
```

---

### Web scraper

Fetches a URL and optionally extracts text matching a CSS selector.

```python
# plugins/web_scraper.py

import asyncio
from agent.plugins import runner

try:
    import aiohttp
    from bs4 import BeautifulSoup
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False


@runner.register("web_scrape")
async def web_scrape_runner(job: dict) -> dict:
    if not HAS_DEPS:
        return {"status": "error", "error": "Install aiohttp and beautifulsoup4"}

    payload = job.get("payload", {})
    url = payload.get("url")
    selector = payload.get("selector")  # Optional CSS selector
    timeout = payload.get("timeout", 15)

    if not url:
        return {"status": "error", "error": "Missing 'url' in payload"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                html = await resp.text()

                result = {
                    "url": url,
                    "status_code": resp.status,
                    "content_length": len(html),
                }

                if selector:
                    soup = BeautifulSoup(html, "html.parser")
                    elements = soup.select(selector)
                    result["matches"] = [el.get_text(strip=True) for el in elements[:50]]
                    result["match_count"] = len(elements)
                else:
                    result["body"] = html[:10000]

                return {"status": "success", "result": result}

    except asyncio.TimeoutError:
        return {"status": "error", "error": f"Request timed out after {timeout}s"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

**Submit:**
```python
submit_job({
    "job_type": "web_scrape",
    "payload": {
        "url": "https://example.com",
        "selector": "h1",
        "timeout": 10,
    },
    "payment": 25.0,
})
```

---

### File processor

Reads a file, applies a transformation, and writes the output.

```python
# plugins/file_processor.py

import asyncio
import hashlib
from pathlib import Path
from agent.plugins import runner


@runner.register("file_process")
async def file_process_runner(job: dict) -> dict:
    payload = job.get("payload", {})
    input_path = payload.get("input_path")
    operation = payload.get("operation", "checksum")  # checksum, linecount, wordcount, head

    if not input_path:
        return {"status": "error", "error": "Missing 'input_path' in payload"}

    path = Path(input_path)
    if not path.exists():
        return {"status": "error", "error": f"File not found: {input_path}"}

    content = await asyncio.to_thread(path.read_text, encoding="utf-8", errors="replace")

    if operation == "checksum":
        sha256 = hashlib.sha256(content.encode()).hexdigest()
        return {"status": "success", "result": {"sha256": sha256, "size": len(content)}}

    elif operation == "linecount":
        lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
        return {"status": "success", "result": {"lines": lines}}

    elif operation == "wordcount":
        words = len(content.split())
        return {"status": "success", "result": {"words": words}}

    elif operation == "head":
        n = payload.get("lines", 10)
        head_lines = content.split("\n")[:n]
        return {"status": "success", "result": {"head": "\n".join(head_lines)}}

    else:
        return {"status": "error", "error": f"Unknown operation: {operation}"}
```

**Submit:**
```python
submit_job({
    "job_type": "file_process",
    "payload": {
        "input_path": "/var/log/syslog",
        "operation": "linecount",
    },
    "payment": 15.0,
})
```

---

### GPU inference

Run a machine learning model for inference. Demonstrates handling heavy dependencies, running blocking code in a thread, and structured output.

```python
# plugins/gpu_inference.py

import asyncio
from agent.plugins import runner

try:
    import torch
    HAS_TORCH = True
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
except ImportError:
    HAS_TORCH = False
    DEVICE = "cpu"


# Cache the model across invocations to avoid reloading
_model_cache = {}


def _load_model(model_name: str):
    """Load model (blocking -- call via asyncio.to_thread)."""
    if model_name in _model_cache:
        return _model_cache[model_name]

    # Example: load a torchvision model
    import torchvision.models as models
    model_fn = getattr(models, model_name, None)
    if model_fn is None:
        raise ValueError(f"Unknown model: {model_name}")

    model = model_fn(pretrained=True).eval().to(DEVICE)
    _model_cache[model_name] = model
    return model


def _run_inference(model, input_data):
    """Run forward pass (blocking)."""
    import torch
    with torch.no_grad():
        tensor = torch.tensor(input_data, dtype=torch.float32).to(DEVICE)
        output = model(tensor.unsqueeze(0))
        return output.cpu().numpy().tolist()


@runner.register("gpu_inference")
async def gpu_inference_runner(job: dict) -> dict:
    if not HAS_TORCH:
        return {"status": "error", "error": "PyTorch is not installed"}

    payload = job.get("payload", {})
    model_name = payload.get("model", "resnet18")
    input_data = payload.get("input")

    if input_data is None:
        return {"status": "error", "error": "Missing 'input' in payload"}

    try:
        model = await asyncio.to_thread(_load_model, model_name)
        predictions = await asyncio.to_thread(_run_inference, model, input_data)

        return {
            "status": "success",
            "result": {
                "model": model_name,
                "device": DEVICE,
                "predictions": predictions,
            },
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

**Submit:**
```python
submit_job({
    "job_type": "gpu_inference",
    "payload": {
        "model": "resnet18",
        "input": [[[0.5] * 224] * 224] * 3,  # 3x224x224 dummy image
    },
    "payment": 200.0,
    "priority": 0.8,
})
```

---

## Quick Reference

```python
# Minimal plugin template -- copy and modify

from agent.plugins import runner


@runner.register("my_type")
async def my_runner(job: dict) -> dict:
    payload = job.get("payload", {})

    # Your logic here

    return {"status": "success", "result": "done"}
```

### Checklist before shipping a plugin

- [ ] File is in the `plugins/` directory
- [ ] Filename does not start with `_`
- [ ] Runner function is `async def`
- [ ] `@runner.register("unique_job_type")` decorator is present
- [ ] Payload fields are documented (even if just in a docstring)
- [ ] Error cases return `{"status": "error", "error": "..."}` instead of crashing
- [ ] Blocking I/O is wrapped in `asyncio.to_thread()`
- [ ] Optional dependencies are guarded with try/except ImportError
- [ ] At least one unit test exists in `test/plugins/`
