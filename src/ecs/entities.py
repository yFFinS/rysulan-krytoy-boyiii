from typing import Dict, List, Type, TypeVar, Callable, Set, Generic
from src.ecs.component import BaseComponent
from src.core.profiling import profiled


class Entity:
    __current_id = 0
    __free_ids: Set[int] = set()
    __slots__ = ("__id",)

    def __init__(self):
        if not Entity.__free_ids:
            self.__id = Entity.__current_id
            Entity.__current_id += 1
        else:
            self.__id = Entity.__free_ids.pop()

    def get_id(self) -> int:
        return self.__id

    def __eq__(self, other):
        return self.__id == other.__id

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.__id)


class EntityNotFoundError(Exception):
    """Raised when entity does not exists in current manager"""
    pass


class EntityExistsError(Exception):
    """Raised when entity already exists in current manager"""
    pass


TComponent = TypeVar("TComponent", bound=BaseComponent)


class ComponentDataArray:
    __slots__ = ("entity", "components", "__cache")

    def __init__(self, entity: Entity, components: List[BaseComponent]):
        self.entity = entity
        self.components = {type(comp): comp for comp in components}

    @profiled
    def get_component(self, component_type: Type[TComponent]) -> TComponent:
        return self.components.get(component_type, None)


class ComponentDataFilter:
    __slots__ = ("required", "without", "additional")

    def __init__(self, required, without=(), additional=()):
        self.required = required
        self.without = without
        self.additional = additional

    def filter(self, data: Dict[Entity, Set[BaseComponent]],
               cache: Dict[Type[TComponent], Set[Entity]] = None) -> Set[ComponentDataArray]:
        output = set()
        if cache is None:
            for entity, components in data.items():
                temp = []
                required_count = 0
                for component in components:
                    comp_type = type(component)
                    if comp_type in self.without:
                        temp.clear()
                        break
                    elif comp_type in self.required:
                        required_count += 1
                        temp.append(component)
                    elif comp_type in self.additional:
                        temp.append(component)
                if required_count == len(self.required) and temp:
                    output.add(ComponentDataArray(entity, temp))
        else:
            entities = set(data.keys())
            for req in self.required:
                entities &= cache[req]
            for wout in self.without:
                entities -= cache[wout]
            output = set(
                ComponentDataArray(
                    entity,
                    [component for component in data[entity]
                     if type(component) in self.required or type(component) in self.additional])
                for entity in entities)
        return output


class EntityContainer:
    __slots__ = ("__data", "__cache")

    def __init__(self):
        self.__data: Dict[Entity, Set[BaseComponent]] = dict()
        self.__cache: Dict[Type[TComponent], Set[Entity]]\
            = {comp_type: set() for comp_type in BaseComponent.__subclasses__()}

    def __getitem__(self, item):
        return self.__data[item]

    def __len__(self):
        return len(self.__data)

    def has_entity(self, entity: Entity) -> bool:
        return entity in self.__data.keys()

    def add_entity(self, entity: Entity) -> None:
        if not self.has_entity(entity):
            self.__data[entity] = set()
        else:
            raise EntityExistsError()

    @profiled
    def remove_entity(self, entity: Entity) -> None:
        if self.has_entity(entity):
            to_remove = []
            for data in self.__data[entity]:
                to_remove.append(type(data))
            for i in to_remove:
                self.remove_entity_data(entity, i)
            self.__data.pop(entity)
        else:
            raise EntityNotFoundError()

    def add_entity_data(self, entity: Entity, data: BaseComponent) -> None:
        if self.has_entity(entity):
            self.__data[entity].add(data)
            self.__cache[type(data)].add(entity)
        else:
            raise EntityNotFoundError()

    def remove_entity_data(self, entity: Entity, data_type: Type[BaseComponent]) -> None:
        if self.has_entity(entity):
            to_remove = None
            for data in self.__data[entity]:
                if type(data) == data_type:
                    to_remove = data
                    break
            if to_remove is not None:
                self.__data[entity].discard(to_remove)
                self.__cache[type(to_remove)].discard(entity)
                from src.sql.data import EntryDeletionStack
                EntryDeletionStack.add(to_remove)
                to_remove.on_remove()

        else:
            raise EntityNotFoundError()

    @profiled
    def filter(self, data_filter: ComponentDataFilter) -> Set[ComponentDataArray]:
        return data_filter.filter(self.__data, self.__cache)

    @profiled
    def get_component(self, entity: Entity, component_type: Type[TComponent]) -> TComponent:
        if self.has_entity(entity):
            for comp in self.__data[entity]:
                if type(comp) == component_type:
                    return comp

    @profiled
    def get_entity(self, entity_id: int) -> Entity:
        for entity in self.__data.keys():
            if entity.get_id() == entity_id:
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
    __commands: List[BufferedCommand]

    def __init__(self):
        self.__commands = []

    def add_command(self, command: Callable, *args, **kwargs) -> None:
        self.__commands.append(BufferedCommand(command, *args, **kwargs))

    def execute_commands(self) -> None:
        for command in self.__commands:
            try:
                command.execute()
            except:
                print(f"Error in {command.command.__name__}.")
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

    def get_component(self, entity: Entity, component_type: Generic[TComponent]) -> TComponent:
        return self.__container.get_component(entity, component_type)

    def remove_component(self, entity: Entity, component: Type[BaseComponent]) -> None:
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

    def get_entity(self, entity_id: int) -> Entity:
        return self.__container.get_entity(entity_id)

    def has_entity(self, entity: Entity) -> bool:
        return self.__container.has_entity(entity)