"""Tool executor and registry"""
from typing import Any, Dict, List
from .tools.base import BaseTool, BaseToolGroup, BaseStatus
from .tools.execute_command import ShellToolGroup, ShellStatus
from .tools.read_file import ReadFileTool
from .tools.write_file import WriteFileTool
from .tools.list_directory import ListDirectoryTool
from .tools.skills import UseSkillTool
from .tools.skills_status import SkillsStatus


class ToolExecutor:
    """Manages and executes tools"""

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.statuses: Dict[str, BaseStatus] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register all default tools"""
        default_tools = [
            ReadFileTool(),
            WriteFileTool(),
            ListDirectoryTool(),
            UseSkillTool(),
        ]
        for tool in default_tools:
            self.register_tool(tool)

        self.register_tool_group(ShellToolGroup())
        self.register_status(ShellStatus())
        self.register_status(SkillsStatus())
    
    def register_tool(self, tool: BaseTool) -> None:
        """Register a new tool"""
        self.tools[tool.name] = tool

    def register_tool_group(self, group: BaseToolGroup) -> None:
        """Register a group of tools"""
        tools = group.get_tools()
        for tool in tools:
            self.register_tool(tool)

    def register_status(self, status: BaseStatus) -> None:
        """Register a status-only entry"""
        self.statuses[status.name] = status
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a registered tool"""
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found"
            }
        
        try:
            tool = self.tools[tool_name]
            result = tool.execute(**kwargs)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all registered tools in OpenAI format"""
        return [tool.to_dict() for tool in self.tools.values()]

    def get_all_tool_statuses(self) -> List[Dict[str, Any]]:
        """Get status for all registered tools"""
        return [status.get_status() for status in self.statuses.values()]


# Global tool executor instance
tool_executor = ToolExecutor()
