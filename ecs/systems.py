from abc import ABC, abstractmethod


class BaseSystem(ABC):
    from ecs.entities import EntityManager
    __slots__ = ("is_enabled",)

    @abstractmethod
    def on_update(self, entity_manager: EntityManager, delta_time: float):
        raise NotImplementedError()