from abc import ABC, abstractmethod


class BaseSystem(ABC):
    __slots__ = ("is_enabled", "entity_manager")

    def on_create(self):
        pass

    @abstractmethod
    def on_update(self, delta_time: float):
        raise NotImplementedError()