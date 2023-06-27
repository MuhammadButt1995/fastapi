from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ToolExecutionStrategy(ABC):
    @abstractmethod
    def execute(self, method: Optional[str]) -> Optional[Dict[str, Any]]:
        pass