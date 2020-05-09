from abc import ABC, abstractmethod
from ecs.entities import EntityManager
from ecs.entities import ComponentDataFilter
from ecs.entities import ComponentDataArray
from typing import Set


class BaseSystem(ABC):
    __slots__ = ("is_enabled", "entity_manager")
    is_enabled: bool
    entity_manager: EntityManager
    __update_order__: int = 0

    def on_create(self) -> None:
        pass

    @abstractmethod
    def on_update(self, delta_time: float) -> None:
        raise NotImplementedError()

    def query(self, data_filter: ComponentDataFilter) -> Set[ComponentDataArray]:
        return self.entity_manager.get_entities().filter(data_filter)

    def __lt__(self, other: "BaseSystem"):
        return self.__update_order__ < other.__update_order__
