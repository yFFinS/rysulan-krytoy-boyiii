from typing import Dict, Set, List, Type, Generic, TypeVar
from component import BaseComponent
from profiling import profiled


class Entity:
    __current_id = 0
    __slots__ = ("__id",)

    def __init__(self):
        self.__id = Entity.__current_id
        Entity.__current_id += 1

    def get_id(self) -> int:
        return self.__id


class EntityNotFoundError(Exception):
    """Raised when entity does not exists in current manager"""
    pass


class EntityExistsError(Exception):
    """Raised when entity already exists in current manager"""
    pass


class DataFilter:
    __slots__ = ("entity", "components")
    TComponent = TypeVar("TComponent", bound=BaseComponent)

    def __init__(self, entity: Entity, component: List[BaseComponent]):
        self.entity = entity
        self.components = component

    @profiled
    def get_component(self, component_type: Generic[TComponent]) -> TComponent:
        for existing_component in self.components:
            if type(existing_component) == component_type:
                return existing_component


class EntityContainer:
    __slots__ = ("__data",)

    def __init__(self):
        self.__data: Dict[Entity, Set[BaseComponent]] = {}

    def __getitem__(self, item):
        return self.__data[item]

    def has_entity(self, entity: Entity) -> bool:
        return entity in self.__data

    @profiled
    def add_entity(self, entity: Entity) -> None:
        if not self.has_entity(entity):
            self.__data[entity] = set()
        else:
            raise EntityExistsError()

    @profiled
    def remove_entity(self, entity: Entity) -> None:
        if self.has_entity(entity):
            self.__data.pop(entity)
        else:
            raise EntityNotFoundError()

    @profiled
    def add_entity_data(self, entity: Entity, data: BaseComponent) -> None:
        if self.has_entity(entity):
            self.__data[entity].add(data)
        else:
            raise EntityNotFoundError()

    @profiled
    def remove_entity_data(self, entity: Entity, data: BaseComponent) -> None:
        if self.has_entity(entity):
            self.__data[entity].discard(data)
        else:
            raise EntityNotFoundError()

    @profiled
    def filter(self, *filter_by: Type[BaseComponent]) -> Set[DataFilter]:
        output = set()
        for entity, data in self.__data.items():
            temp = []
            for component in data:
                if type(component) in filter_by:
                    temp.append(component)
            if len(temp) == len(filter_by):
                data_filter = DataFilter(entity, temp)
                output.add(data_filter)

        return output


class EntityManager:
    __slots__ = ("__container",)

    def __init__(self):
        self.__container = EntityContainer()

    def create_entity(self) -> Entity:
        entity = Entity()
        self.__container.add_entity(entity)
        return entity

    def kill_entity(self, entity: Entity) -> None:
        self.__container.remove_entity(entity)

    def add_component(self, entity: Entity, component: BaseComponent) -> None:
        self.__container.add_entity_data(entity, component)

    def remove_component(self, entity: Entity, component: BaseComponent) -> None:
        self.__container.remove_entity_data(entity, component)

    def get_entities(self) -> EntityContainer:
        return self.__container

