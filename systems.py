from abc import ABC, abstractmethod


class BaseSystem(ABC):
    from entities import EntityManager
    __slots__ = ("is_enabled",)

    @abstractmethod
    def on_update(self, entity_manager: EntityManager):
        raise NotImplementedError()