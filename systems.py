from entities import EntityManager
from abc import ABC, abstractmethod


class BaseSystem(ABC):
    __slots__ = ("is_enabled",)

    @abstractmethod
    def on_update(self, entity_manager: EntityManager):
        raise NotImplementedError()