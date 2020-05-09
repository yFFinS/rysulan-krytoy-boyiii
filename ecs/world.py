from ecs.entities import EntityManager
from ecs.systems import BaseSystem
from typing import List, Type, TypeVar
from core.profiling import profiled
from core.main_timer import Time


class SystemNotExistsError(Exception):
    """Raised when system not found in current world"""
    pass


class SystemExistsError(Exception):
    """Raised when system already exists in current world"""
    pass


class World:
    default_world: "World" = None
    current_world: "World" = None
    __current_id = 0
    __slots__ = ("__id", "__entity_manager", "__systems")
    TSystem = TypeVar("TSystem", bound=BaseSystem)

    def __init__(self):
        self.__id = World.__current_id
        World.__current_id += 1

        self.__entity_manager = EntityManager()
        self.__systems: List[BaseSystem] = []

        if World.current_world is None:
            World.current_world = self

    def get_id(self) -> int:
        return self.__id

    def get_manager(self) -> EntityManager:
        return self.__entity_manager

    @profiled
    def get_system(self, system_type: Type[TSystem]) -> TSystem:
        for existing_system in self.__systems:
            if type(existing_system) == system_type:
                return existing_system
        raise SystemNotExistsError()

    @profiled
    def create_system(self, system_type: type) -> TSystem:
        if system_type in map(type, self.__systems):
            raise SystemExistsError()

        system = system_type()
        system.is_enabled = True
        system.entity_manager = self.__entity_manager
        self.__systems.append(system)
        system.on_create()
        return system

    @profiled
    def get_or_create_system(self, system_type: Type[TSystem]) -> TSystem:
        try:
            return self.get_system(system_type)
        except SystemNotExistsError:
            return self.create_system(system_type)

    @profiled
    def remove_system(self, system_type: Type[TSystem]) -> None:
        self.__systems.remove(self.get_system(system_type))

    def set_system_state(self, system_type: Type[TSystem], enabled: bool) -> None:
        self.get_system(system_type).is_enabled = enabled

    def update(self) -> None:
        delta_time = Time.get_delta_time()
        for system in self.__systems:
            if system.is_enabled:
                profiled(system.on_update)(delta_time)
        self.__entity_manager.release_buffer()

    @staticmethod
    def update_current() -> None:
        World.current_world.update()

    def create_all_systems(self) -> None:
        import simulation.__all_systems
        count = 0
        for system_type in BaseSystem.__subclasses__():
            try:
                self.create_system(system_type)
                count += 1
                self.__systems.sort()
            except SystemExistsError:
                pass
        print(f"Created {count} systems.")