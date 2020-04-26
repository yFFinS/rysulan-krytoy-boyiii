from typing import Dict, Set
from component import BaseComponent


class Entity:
    __current_id = 0

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


class EntityContainer:

    def __init__(self):
        self.__data: Dict[int, Set[BaseComponent]] = {}

    def __getitem__(self, item):
        return self.__data[item]

    def __has_entity(self, entity: Entity) -> bool:
        return entity.get_id() in self.__data

    def add_entity(self, entity: Entity) -> None:
        if not self.__has_entity(entity):
            self.__data[entity.get_id()] = set()
        else:
            raise

    def remove_entity(self, entity: Entity) -> None:
        if self.__has_entity(entity):
            self.__data.pop(entity.get_id())
        else:
            raise EntityNotFoundError()

    def add_entity_data(self, entity: Entity, data: BaseComponent) -> None:
        if self.__has_entity(entity):
            self.__data[entity.get_id()].add(data)
        else:
            raise EntityNotFoundError()

    def remove_entity_data(self, entity: Entity, data: BaseComponent) -> None:
        if self.__has_entity(entity):
            self.__data[entity.get_id()].discard(data)
        else:
            raise EntityNotFoundError()


class EntityManager:

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

