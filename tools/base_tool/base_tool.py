from abc import ABC, abstractmethod

class BaseTool(ABC):
    def __init__(self, name, description, icon):
        self.name = name
        self.description = description
        self.icon = icon

    @abstractmethod
    def execute(self, *args, **kwargs):
        pass