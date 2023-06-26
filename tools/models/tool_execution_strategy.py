from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ToolExecutionStrategy(ABC):
    @abstractmethod
    def execute(self, method: Optional[str] = None) -> Optional[Dict[str, Any]]:
        pass