from abc import ABC, abstractmethod
from random import randint


class BotMethods:
    from vk_api import VkApi
    __slots__ = ("__api", "__uploads")

    def __init__(self, session: VkApi):
        from vk_api.upload import VkUpload
        self.__api = session.get_api()
        self.__uploads = VkUpload(session)

    def send_message(self, peer_id: int, message: str) -> None:
        self.__api.messages.send(peer_id=str(peer_id), message=message, random_id=self.random_id())

    @staticmethod
    def random_id() -> str:
        return str(randint(-10000000, 10000000))


class BaseCommand(ABC):
    __slots__ = ()
    _name: str = None
    _description: str = None
    _event_data: tuple = None

    @abstractmethod
    def on_call(self, data: dict, methods: BotMethods) -> None:
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


class HelloCommand(BaseCommand):
    _name = "hello"
    _description = "says hello"
    _event_data = ("text", "peer_id")

    def on_call(self, data: dict, methods: BotMethods) -> None:
        methods.send_message(data["peer_id"], "hello " + data["text"])


class CreateEntitiesCommand(BaseCommand):
    _name = "create"
    _event_data = ("text", "peer_id")
    _description = ""

    def on_call(self, data: dict, methods: BotMethods) -> None:
        count = data["text"]
        from simulation.utils import create_creature
        try:
            for i in range(int(count)):
                create_creature()
            methods.send_message(data["peer_id"], f"Создано {count} существ.")
        except TypeError as e:
            print(e)
            methods.send_message(data["peer_id"], "Неправильный формат ввода.")
