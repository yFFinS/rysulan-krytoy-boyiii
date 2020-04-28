from abc import ABC, abstractmethod


class BaseSystem(ABC):
    from ecs.entities import EntityManager
    __slots__ = ("is_enabled", "entity_manager")
    is_enabled: bool
    entity_manager: EntityManager

    def on_create(self) -> None:
        pass

    @abstractmethod
    def on_update(self, delta_time: float) -> None:
        raise NotImplementedError()