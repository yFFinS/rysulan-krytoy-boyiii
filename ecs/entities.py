from typing import Dict, List, Type, TypeVar, Callable, Set
from ecs.component import BaseComponent
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


class ComponentNotFoundError(Exception):
    """Raised when component does not exists within entity"""
    pass


TComponent = TypeVar("TComponent", bound=BaseComponent)


class ComponentDataArray:
    __slots__ = ("entity", "components")

    def __init__(self, entity: Entity, component: List[BaseComponent]):
        self.entity = entity
        self.components = component

    @profiled
    def get_component(self, component_type: Type[TComponent]) -> TComponent:
        for existing_component in self.components:
            if type(existing_component) == component_type:
                return existing_component


class ComponentDataFilter:
    __slots__ = ("required", "without", "additional")

    def __init__(self, required, without=(), additional=()):
        self.required = required
        self.without = without
        self.additional = additional

    def filter(self, data: Dict[Entity, Set[BaseComponent]]) -> Set[ComponentDataArray]:
        output = set()
        for entity, components in data.items():
            temp = []
            required_count = 0
            for component in components:
                if type(component) in self.without:
                    temp.clear()
                    break
                elif type(component) in self.required:
                    required_count += 1
                    temp.append(component)
                elif type(component) in self.additional:
                    temp.append(component)
            if required_count == len(self.required) and temp:
                output.add(ComponentDataArray(entity, temp))
        return output


class EntityContainer:
    __slots__ = ("__data",)

    def __init__(self):
        self.__data: Dict[Entity, Set[BaseComponent]] = {}

    def __getitem__(self, item):
        return self.__data[item]

    def has_entity(self, entity: Entity) -> bool:
        return entity in self.__data

    def add_entity(self, entity: Entity) -> None:
        if not self.has_entity(entity):
            self.__data[entity] = set()
        else:
            raise EntityExistsError()

    def remove_entity(self, entity: Entity) -> None:
        if self.has_entity(entity):
            self.__data.pop(entity)
        else:
            raise EntityNotFoundError()

    def add_entity_data(self, entity: Entity, data: BaseComponent) -> None:
        if self.has_entity(entity):
            self.__data[entity].add(data)
        else:
            raise EntityNotFoundError()

    def remove_entity_data(self, entity: Entity, data: BaseComponent) -> None:
        if self.has_entity(entity):
            self.__data[entity].discard(data)
        else:
            raise EntityNotFoundError()

    @profiled
    def filter(self, data_filter: ComponentDataFilter) -> Set[ComponentDataArray]:
        return data_filter.filter(self.__data)

    @profiled
    def get_component(self, entity: Entity, component_type: Type[TComponent]) -> TComponent:
        if self.has_entity(entity):
            for comp in self.__data[entity]:
                if type(comp) == component_type:
                    return comp
            raise ComponentNotFoundError()

    @profiled
    def get_entity(self, id: int) -> Entity:
        for entity in self.__data.keys():
            if entity.get_id() == id:
                return entity
        raise EntityNotFoundError()


class BufferedCommand:
    __slots__ = ("command", "args", "kwargs")

    def __init__(self, command: Callable, *args, **kwargs):
        self.command = command
        self.args = args
        self.kwargs = kwargs

    def execute(self) -> None:
        self.command(*self.args, **self.kwargs)


class CommandBuffer:
    __slots__ = ("__commands",)
    __commands: Set[BufferedCommand]

    def __init__(self):
        self.__commands = set()

    def add_command(self, command: Callable, *args, **kwargs) -> None:
        self.__commands.add(BufferedCommand(command, *args, **kwargs))

    def execute_commands(self) -> None:
        for command in self.__commands:
            command.execute()
        self.__commands.clear()


class EntityManager:
    __slots__ = ("__container", "__command_buffer")
    __container: EntityContainer
    __command_buffer: CommandBuffer

    def __init__(self):
        self.__container = EntityContainer()
        self.__command_buffer = CommandBuffer()

    def create_entity(self) -> Entity:
        entity = Entity()
        self.__container.add_entity(entity)
        return entity

    def kill_entity(self, entity: Entity) -> None:
        self.__container.remove_entity(entity)

    def add_component(self, entity: Entity, component: BaseComponent) -> None:
        self.__container.add_entity_data(entity, component)

    def get_component(self, entity: Entity, component_type: Type[TComponent]) -> TComponent:
        return self.__container.get_component(entity, component_type)

    def remove_component(self, entity: Entity, component: BaseComponent) -> None:
        self.__container.remove_entity_data(entity, component)

    def get_entities(self) -> EntityContainer:
        return self.__container

    def add_command(self, command: Callable, *args, **kwargs) -> None:
        self.__command_buffer.add_command(command, *args, **kwargs)

    def release_buffer(self) -> None:
        self.__command_buffer.execute_commands()

    @staticmethod
    def create_filter(required=(), without=(), additional=()) -> ComponentDataFilter:
        return ComponentDataFilter(required, without, additional)

    def get_entity(self, id: int) -> Entity:
        return self.__container.get_entity(id)