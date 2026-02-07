"""Tests for ToolExecutor."""
from pathlib import Path

from iribot.executor import ToolExecutor
from iribot.tools.base import BaseTool


class DummyTool(BaseTool):
    @property
    def name(self) -> str:
        return "dummy"

    @property
    def description(self) -> str:
        return "Dummy tool"

    @property
    def parameters(self):
        return {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs):
        return {"success": True, "value": kwargs.get("value")}


def test_executor_creates_outputs_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    executor = ToolExecutor()
    outputs_dir = Path.cwd() / "outputs"
    assert outputs_dir.exists()
    assert executor.outputs_dir == outputs_dir


def test_executor_execute_tool_missing():
    executor = ToolExecutor()
    result = executor.execute_tool("does_not_exist")
    assert result["success"] is False


def test_executor_execute_tool_custom():
    executor = ToolExecutor()
    executor.register_tool(DummyTool())
    result = executor.execute_tool("dummy", value=123)
    assert result["success"] is True
    assert result["value"] == 123
