"""
Plugin system for MarlOS runners.
Drop a Python file in the plugins/ directory and it auto-registers.

Usage:
    # plugins/my_runner.py
    from agent.plugins import runner

    @runner.register("my_custom_type")
    async def run(job: dict) -> dict:
        payload = job.get("payload", {})
        # ... do work ...
        return {"status": "success", "result": {"output": "done"}}
"""

import importlib
import importlib.util
import logging
import os
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class _RunnerRegistry:
    """Global registry for plugin runners using decorator pattern."""

    def __init__(self):
        self._runners: dict[str, Callable] = {}

    def register(self, job_type: str):
        """Decorator to register a runner for a job type.

        Usage:
            @runner.register("my_type")
            async def my_runner(job: dict) -> dict:
                ...
        """
        def decorator(func):
            self._runners[job_type] = func
            logger.info(f"[PLUGIN] Registered runner: {job_type}")
            return func
        return decorator

    def get_runners(self) -> dict[str, Callable]:
        return dict(self._runners)

    def clear(self):
        self._runners.clear()


# Singleton registry
runner = _RunnerRegistry()


class PluginLoader:
    """Discovers and loads plugin files from a directory."""

    def __init__(self, plugin_dir: str = None):
        if plugin_dir is None:
            # Default: plugins/ in project root
            plugin_dir = str(Path(__file__).parent.parent.parent / "plugins")
        self.plugin_dir = Path(plugin_dir)
        self.loaded_plugins: list[str] = []

    def discover_and_load(self) -> dict[str, Callable]:
        """Scan plugin directory and load all .py files.
        Returns dict of job_type -> runner_func."""

        if not self.plugin_dir.exists():
            logger.debug(f"[PLUGIN] Plugin directory not found: {self.plugin_dir}")
            return {}

        for py_file in sorted(self.plugin_dir.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            self._load_plugin(py_file)

        loaded = runner.get_runners()
        if loaded:
            print(f"[PLUGIN] Loaded {len(loaded)} plugin runner(s): {', '.join(loaded.keys())}")

        return loaded

    def _load_plugin(self, file_path: Path):
        """Load a single plugin file."""
        module_name = f"marlos_plugin_{file_path.stem}"

        try:
            spec = importlib.util.spec_from_file_location(module_name, str(file_path))
            if spec is None or spec.loader is None:
                logger.warning(f"[PLUGIN] Could not load spec for {file_path}")
                return

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.loaded_plugins.append(file_path.stem)
            logger.info(f"[PLUGIN] Loaded plugin: {file_path.name}")

        except Exception as e:
            logger.error(f"[PLUGIN] Error loading {file_path.name}: {e}")
            print(f"[PLUGIN] Error loading {file_path.name}: {e}")

    def register_with_engine(self, executor_engine):
        """Load plugins and register them with the execution engine."""
        runners = self.discover_and_load()
        count = 0
        for job_type, func in runners.items():
            executor_engine.register_runner(job_type, func)
            count += 1
        return count
