from abc import ABC, abstractmethod
from typing import Optional

class BaseTool(ABC):
    def __init__(self, name, description, tool_type, icon, tags=None, ):
        self.name = name
        self.description = description
        self.tool_type = tool_type
        self.icon = icon
        self.tags = tags
        

    @abstractmethod
    def execute(self, *args, **kwargs):
        pass
