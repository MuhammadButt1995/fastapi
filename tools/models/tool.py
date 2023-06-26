from pydantic import BaseModel
from typing import Dict, Any, List, Optional, Type
from fastapi import HTTPException

from tools.models.tool_type import ToolType
from tools.models.tag import Tag
from .tool_execution_strategy import ToolExecutionStrategy
import logging

class Tool(BaseModel):
    name: str
    description: str
    icon: str
    type: ToolType
    tags: List[Tag]
    strategy: Type[ToolExecutionStrategy]

    def execute_strategy(self, method: Optional[str] = None) -> Optional[Dict[str, Any]]:
        try:
            strategy_instance = self.strategy()
            return strategy_instance.execute(method)
        except Exception as e:
            logging.error(f"Error executing tool {self.name}: {e}")
            raise HTTPException(status_code=500, detail="Error executing tool")