from abc import ABC, abstractmethod
from random import randint
from ecs.world import World


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
        try:
            entity_manager = World.current_world.get_manager()

            def buffered_command():
                from simulation.utils import create_creature
                for i in range(int(count)):
                    create_creature(entity_manager, entity_manager.create_entity())
                methods.send_message(data["peer_id"], f"Создано {count} существ.")

            entity_manager.add_command(buffered_command)
        except TypeError:
            methods.send_message(data["peer_id"], "Неправильный формат ввода.")


class CreateNamedEntitiesCommand(BaseCommand):
    _name = "creature"
    _event_data = ("text", "peer_id")
    _description = ""

    def __init__(self):
        from pygame import font
        self.__font = font.Font(None, 25)
        self.__name_color = (240, 240, 240)

    def on_call(self, data: dict, methods: BotMethods) -> None:
        name = data["text"]
        entity_manager = World.current_world.get_manager()

        def buffered_command():
            from simulation.utils import create_creature
            from simulation.components import EntityName, RenderSprite, Position
            from pygame import sprite, Surface
            from simulation.math import Vector

            name_entity = entity_manager.create_entity()
            follow_entity = entity_manager.create_entity()
            create_creature(entity_manager, follow_entity)
            name_comp = EntityName()
            name_comp.value = name
            name_comp.entity = follow_entity
            name_comp.user_id = data["peer_id"]

            render_comp = RenderSprite()
            text_sprite = sprite.Sprite()
            text = self.__font.render(name, True, self.__name_color)
            text_sprite.image = text
            text_sprite.rect = text.get_rect()
            render_comp.sprite = text_sprite
            position_comp = Position()
            position_comp.value = Vector(0, 0)

            entity_manager.add_component(name_entity, name_comp)
            entity_manager.add_component(name_entity, render_comp)
            entity_manager.add_component(name_entity, position_comp)

            methods.send_message(data["peer_id"], "Существо создано.")

        entity_manager.add_command(buffered_command)
