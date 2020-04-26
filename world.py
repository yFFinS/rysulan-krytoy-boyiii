from entities import EntityManager
from systems import BaseSystem
from typing import Set, Generic, TypeVar


class SystemNotExistsError(Exception):
    """Raised when system not found in current world"""
    pass


class SystemExistsError(Exception):
    """Raised when system already exists in current world"""
    pass


class World:
    __current_id = 0
    __slots__ = ("__id", "__entity_manager", "__systems")
    TSystem = TypeVar("TSystem", bound=BaseSystem)

    def __init__(self):
        self.__id = World.__current_id
        World.__current_id += 1

        self.__entity_manager = EntityManager()
        self.__systems: Set[BaseSystem] = set()

    def get_id(self) -> int:
        return self.__id

    def get_manager(self) -> EntityManager:
        return self.__entity_manager

    def get_system(self, system_type: Generic[TSystem]) -> TSystem:
        for existing_system in self.__systems:
            if type(existing_system) == system_type:
                return existing_system
        raise SystemNotExistsError()

    def create_system(self, system_type: Generic[TSystem]) -> TSystem:
        if system_type in map(type, self.__systems):
            raise NotImplementedError()

        system = system_type()
        system.is_enabled = True
        self.__systems.add(system)
        return system

    def get_or_create_system(self, system_type: Generic[TSystem]) -> TSystem:
        try:
            return self.get_system(system_type)
        except SystemNotExistsError:
            return self.create_system(system_type)

    def remove_system(self, system_type: Generic[TSystem]) -> None:
        self.__systems.remove(self.get_system(system_type))

    def set_system_state(self, system_type: Generic[TSystem], enabled: bool) -> None:
        self.get_system(system_type).is_enabled = enabled

    def update_systems(self) -> None:
        for system in self.__systems:
            if system.is_enabled:
                system.on_update(self.__entity_manager)