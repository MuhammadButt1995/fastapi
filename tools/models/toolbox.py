from tools.models.tool import Tool
from typing import Dict, Type
from fastapi import HTTPException

class Toolbox:
    def __init__(self):
        self.tools: Dict[str, Type[Tool]] = {}

    def register_tool(self, tool_id, tool: Type[Tool]):
        self.tools[tool_id] = tool
        
    def get_tool(self, tool_name: str) -> Type[Tool]:
        """Gets the tool class by its name."""
        if tool_name not in self.tools:
            raise KeyError(f"Tool '{tool_name}' not found")

        return self.tools[tool_name]

    def list_tools(self):
        """Lists all the current tools as objects with their name, description, and icon."""
        tools_list = []

        for tool_name in self.tools:
            tool_instance = self.get_tool(tool_name)
        
            tool_data = {
                "name": tool_instance.name,
                "description": tool_instance.description,
                "tool_type": tool_instance.type,
                "tags": tool_instance.tags,
                "icon": tool_instance.icon
            }
            tools_list.append(tool_data)

        return tools_list