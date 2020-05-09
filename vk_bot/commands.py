from abc import ABC, abstractmethod
from random import randint
from ecs.world import World
from typing import Tuple


class BotMethods:
    from vk_api import VkApi
    __slots__ = ("__api", "__uploads")

    def __init__(self, session: VkApi):
        from vk_api.upload import VkUpload
        self.__api = session.get_api()
        self.__uploads = VkUpload(session)

    def send_message(self, peer_id: str, message: str) -> None:
        self.__api.messages.send(peer_id=peer_id, message=message, random_id=self.random_id())

    @staticmethod
    def random_id() -> str:
        return str(randint(-10000000, 10000000))


class BaseCommand(ABC):
    __slots__ = ()
    _name: str = None
    _description: str = None
    _event_data: tuple = None
    _args: Tuple[Tuple[str, type]] = None

    @abstractmethod
    def on_call(self, data: dict, args: dict, methods: BotMethods) -> None:
        raise NotImplementedError()

    @classmethod
    def get_name(cls) -> str:
        return cls._name

    @classmethod
    def get_description(cls) -> str:
        return cls._description

    @classmethod
    def filter_data(cls, data: dict) -> dict:
        filtered_data = {}
        for key in cls._event_data:
            if key == "text":
                text = data[key].split(maxsplit=1)
                filtered_data[key] = text[1] if len(text) > 1 else ""
            else:
                filtered_data[key] = data[key]
        return filtered_data

    @classmethod
    def parse_args(cls, text) -> dict:
        args = dict()
        if cls._args:
            text_data = text.strip().split(maxsplit=len(cls._args))[1:]
            if len(cls._args) < len(text_data):
                raise IndexError("Слишком много аргументов.")
            for num, inp in enumerate(text_data):
                arg = cls._args[num]
                try:
                    inp = arg[1](inp)
                    args[arg[0]] = inp
                except ValueError:
                    arg_mes = "{" + arg[0] + "}"
                    raise ValueError(f"Ошибка ввода. Аргумент {arg_mes} должен быть типа {arg[1].__name__}")
        return args

    @classmethod
    def help_data(cls):
        args = " ".join("{" + i[0] + "}" for i in cls._args) + " " if cls._args is not None else ""
        return f"{cls._name} {args}— {cls._description}."


class HelloCommand(BaseCommand):
    _name = "hello"
    _description = "пишет \"привет\""
    _event_data = ("peer_id",)

    def on_call(self, data: dict, args: dict, methods: BotMethods) -> None:
        methods.send_message(data["peer_id"], "привет")


class CreateEntitiesCommand(BaseCommand):
    _name = "create"
    _event_data = ("peer_id",)
    _args = (("число", int),)
    _description = "создает {число} существ"

    def __init__(self):
        from pygame import font
        self.__font = font.Font(None, 25)
        self.__name_color = (240, 240, 240)

    def on_call(self, data: dict, args: dict, methods: BotMethods) -> None:
        count = args["число"]
        entity_manager = World.current_world.get_manager()

        def buffered_command():
            from simulation.utils import create_creature
            from simulation.components import EntityName
            for i in range(count):
                from simulation.utils import create_named_creature
                entity = entity_manager.create_entity()
                create_named_creature(entity_manager, entity, "Bot" + str(entity.get_id()), "0", self.__font,
                                      self.__name_color)
            methods.send_message(data["peer_id"], f"Создано {count} существ.")

        entity_manager.add_command(buffered_command)


class CreateNamedEntitiesCommand(BaseCommand):
    _name = "creature"
    _event_data = ("peer_id",)
    _args = (("имя", str),)
    _description = "создает существо с именем {имя}"

    def __init__(self):
        from pygame import font
        self.__font = font.Font(None, 25)
        self.__name_color = (240, 240, 240)

    def on_call(self, data: dict, args: dict, methods: BotMethods) -> None:
        name = args["имя"]
        entity_manager = World.current_world.get_manager()

        def buffered_command():
            from simulation.utils import create_named_creature
            create_named_creature(entity_manager, entity_manager.create_entity(), name, data["peer_id"],
                                  self.__font, self.__name_color)

            methods.send_message(data["peer_id"], "Существо создано.")

        entity_manager.add_command(buffered_command)
