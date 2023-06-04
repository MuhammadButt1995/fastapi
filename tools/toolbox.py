from typing import Dict, Type

from .base_tool.base_tool import BaseTool

class Toolbox:
    def __init__(self):
        self.tools: Dict[str, Type[BaseTool]] = {}

    def register_tool(self, tool: Type[BaseTool]):
        """Registers a tool in the toolbox."""
        if not issubclass(tool, BaseTool):
            raise ValueError(f"Tool '{tool.__name__}' must inherit from BaseTool")

        if tool.__name__ in self.tools:
            raise ValueError(f"Tool '{tool.__name__}' is already registered")

        self.tools[tool.__name__] = tool

    def unregister_tool(self, tool_name: str):
        """Unregister's a tool from the toolbox."""
        if tool_name not in self.tools:
            raise KeyError(f"Tool '{tool_name}' not found")

        del self.tools[tool_name]

    def get_tool(self, tool_name: str) -> Type[BaseTool]:
        """Gets the tool class by its name."""
        if tool_name not in self.tools:
            raise KeyError(f"Tool '{tool_name}' not found")

        return self.tools[tool_name]

    def execute_tool(self, tool_name: str, *args, **kwargs):
        """Executes a tool by its name with the given arguments."""
        tool_class = self.get_tool(tool_name)
        tool_instance = tool_class()
        return tool_instance.execute(*args, **kwargs)

    def list_tools(self):
        """Lists all the current tools as objects with their name, description, and icon."""
        tools_list = []

        for tool_name in self.tools:
            tool_class = self.get_tool(tool_name)
            tool_instance = tool_class()
        
            tool_data = {
                "name": tool_instance.name,
                "description": tool_instance.description,
                "tool_type": tool_instance.tool_type,
                "tags": tool_instance.tags,
                "icon": tool_instance.icon
            }
            tools_list.append(tool_data)

        return tools_list