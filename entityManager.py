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


class EntityManager:

    def __init__(self):
        self.__entities_and_components: Dict[int, Set[BaseComponent]] = {}

    def create_entity(self) -> Entity:
        entity = Entity()
        self.__entities_and_components[entity.get_id()] = set()
        return entity

    def kill_entity(self, entity: Entity) -> None:
        if self.__has_entity(entity):
            self.__entities_and_components.pop(entity.get_id())

    def add_component(self, entity: Entity, component: BaseComponent) -> None:
        if self.__has_entity(entity):
            self.__entities_and_components[entity.get_id()].add(component)

    def remove_component(self, entity: Entity, component: BaseComponent) -> None:
        if self.__has_entity(entity):
            self.__entities_and_components[entity.get_id()].remove(component)

    def __has_entity(self, entity: Entity) -> bool:
        if entity.get_id() in self.__entities_and_components:
            return True
        else:
            raise EntityNotFoundError()



