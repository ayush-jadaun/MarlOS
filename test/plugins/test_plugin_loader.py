"""Unit tests for the plugin system."""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from agent.plugins.loader import PluginLoader, runner, _RunnerRegistry


class TestRunnerRegistry:
    def setup_method(self):
        """Clear global registry before each test."""
        runner.clear()

    def test_register_decorator(self):
        @runner.register("test_type")
        async def my_runner(job):
            return {"status": "success"}

        runners = runner.get_runners()
        assert "test_type" in runners
        assert runners["test_type"] is my_runner

    def test_register_multiple(self):
        @runner.register("type_a")
        async def runner_a(job):
            return {}

        @runner.register("type_b")
        async def runner_b(job):
            return {}

        runners = runner.get_runners()
        assert len(runners) == 2
        assert "type_a" in runners
        assert "type_b" in runners

    def test_clear(self):
        @runner.register("temp")
        async def temp_runner(job):
            return {}

        assert len(runner.get_runners()) == 1
        runner.clear()
        assert len(runner.get_runners()) == 0


class TestPluginLoader:
    def setup_method(self):
        runner.clear()

    def test_load_nonexistent_dir(self):
        loader = PluginLoader("/nonexistent/path")
        result = loader.discover_and_load()
        assert result == {}

    def test_load_plugin_file(self, tmp_path):
        # Write a plugin file
        plugin_file = tmp_path / "my_plugin.py"
        plugin_file.write_text("""
from agent.plugins import runner

@runner.register("custom_test")
async def custom_runner(job):
    return {"status": "success", "output": "custom"}
""")

        loader = PluginLoader(str(tmp_path))
        runners = loader.discover_and_load()
        assert "custom_test" in runners

    def test_skip_underscore_files(self, tmp_path):
        # _private.py should be skipped
        (tmp_path / "_private.py").write_text("print('should not load')")
        (tmp_path / "good.py").write_text("""
from agent.plugins import runner

@runner.register("good_type")
async def good_runner(job):
    return {}
""")

        loader = PluginLoader(str(tmp_path))
        runners = loader.discover_and_load()
        assert "good_type" in runners
        assert "_private" not in loader.loaded_plugins

    def test_bad_plugin_doesnt_crash(self, tmp_path):
        # Plugin with syntax error
        (tmp_path / "broken.py").write_text("def this is broken syntax!!!")

        loader = PluginLoader(str(tmp_path))
        # Should not raise
        runners = loader.discover_and_load()
        assert runners == {} or "broken" not in loader.loaded_plugins

    def test_register_with_engine(self, tmp_path):
        (tmp_path / "eng_plugin.py").write_text("""
from agent.plugins import runner

@runner.register("engine_test")
async def eng_runner(job):
    return {"status": "success"}
""")

        mock_engine = MagicMock()
        loader = PluginLoader(str(tmp_path))
        count = loader.register_with_engine(mock_engine)
        assert count >= 1
        mock_engine.register_runner.assert_called()


class TestExamplePlugin:
    """Test the example plugin ships with the project."""

    def setup_method(self):
        runner.clear()

    def test_example_plugin_loads(self):
        project_plugins = Path(__file__).parent.parent.parent / "plugins"
        if not project_plugins.exists():
            pytest.skip("No plugins/ directory")

        loader = PluginLoader(str(project_plugins))
        runners = loader.discover_and_load()
        assert "ping" in runners
        assert "math" in runners

    @pytest.mark.asyncio
    async def test_ping_runner(self):
        project_plugins = Path(__file__).parent.parent.parent / "plugins"
        loader = PluginLoader(str(project_plugins))
        runners = loader.discover_and_load()

        if "ping" not in runners:
            pytest.skip("ping runner not found")

        result = await runners["ping"]({"payload": {"message": "hello"}})
        assert result["status"] == "success"
        assert "hello" in result["output"]

    @pytest.mark.asyncio
    async def test_math_runner(self):
        project_plugins = Path(__file__).parent.parent.parent / "plugins"
        loader = PluginLoader(str(project_plugins))
        runners = loader.discover_and_load()

        if "math" not in runners:
            pytest.skip("math runner not found")

        result = await runners["math"]({"payload": {"expression": "2 + 3 * 4"}})
        assert result["status"] == "success"
        assert result["result"] == 14

    @pytest.mark.asyncio
    async def test_math_runner_rejects_unsafe(self):
        project_plugins = Path(__file__).parent.parent.parent / "plugins"
        loader = PluginLoader(str(project_plugins))
        runners = loader.discover_and_load()

        if "math" not in runners:
            pytest.skip("math runner not found")

        result = await runners["math"]({"payload": {"expression": "import os"}})
        assert result["status"] == "error"
