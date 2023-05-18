from abc import ABC, abstractmethod

class Observable:
    def __init__(self):
        self._observers = set()

    def add_observer(self, observer):
        self._observers.add(observer)

    def remove_observer(self, observer):
        self._observers.discard(observer)

    async def notify_all(self, data):
        for observer in self._observers:
            await observer.update(data)

    async def monitor_status(self):
        # Default implementation, can be overridden by subclasses that need real-time updates
        pass


class Observer(ABC):
    
    @abstractmethod
    def update(self, data, *args, **kwargs):
        pass