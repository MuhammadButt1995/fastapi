from typing import List, Any


class Observable:
    def __init__(self):
        self._observers: List[Observer] = []

    def attach(self, observer: "Observer"):
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: "Observer"):
        if observer in self._observers:
            self._observers.remove(observer)

    async def notify(self, data: Any):
        for observer in self._observers:
            await observer.update(data)


class Observer:
    def update(self, data: Any):
        raise NotImplementedError