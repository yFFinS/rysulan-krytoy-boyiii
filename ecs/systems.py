from abc import ABC, abstractmethod
from ecs.entities import EntityManager
from ecs.entities import ComponentDataFilter
from ecs.entities import ComponentDataArray
from typing import Set


class BaseSystem(ABC):
    __slots__ = ("is_enabled", "entity_manager", "filter")
    is_enabled: bool
    filter: ComponentDataFilter
    entity_manager: EntityManager

    def on_create(self) -> None:
        pass

    @abstractmethod
    def on_update(self, delta_time: float) -> None:
        raise NotImplementedError()

    def query(self) -> Set[ComponentDataArray]:
        return self.entity_manager.get_entities().filter(self.filter)