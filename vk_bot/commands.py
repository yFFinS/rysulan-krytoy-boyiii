from abc import ABC, abstractmethod
from random import randint
from typing import Tuple
import requests
import json

from ecs.world import World


class BotMethods:
    from vk_api import VkApi
    __slots__ = ("__api", "__group_id")
    __instance: "BotMethods" = None
    __group_id: str

    def __init__(self, session: VkApi, group_id: str):
        if BotMethods.__instance is None:
            BotMethods.__instance = self
            self.__api = session.get_api()
            self.__group_id = group_id

    @staticmethod
    def send_message(peer_id: str, message: str) -> None:
        BotMethods.__instance.__api.messages.send(peer_id=peer_id, message=message, random_id=BotMethods.random_id())

    @staticmethod
    def random_id() -> str:
        return str(randint(-10000000, 10000000))

    @staticmethod
    def send_photo(peer_id: str, file_path: str) -> None:
        try:
            api = BotMethods.__instance.__api
            data = api.photos.getMessagesUploadServer(user_id=peer_id)

            upload_url = data["upload_url"]
            files = {'photo': open(file_path, 'rb')}

            response = requests.post(upload_url, files=files)
            result = json.loads(response.text)

            upload_result = api.photos.saveMessagesPhoto(server=result["server"],
                                                         photo=result["photo"],
                                                         hash=result["hash"])

            api.messages.send(user_id=peer_id,
                              attachment=f'photo{upload_result[0]["owner_id"]}_{upload_result[0]["id"]}',
                              random_id=BotMethods.random_id())
        except BaseException as e:
            print(e)

    @staticmethod
    def set_online(value: bool) -> None:
        # blocked by vk api XD.
        return

    @staticmethod
    def broadcast_message(message: str, exclude: tuple = ()) -> None:
        from main import BROADCAST_MESSAGES
        if not BROADCAST_MESSAGES:
            return
        inst = BotMethods.__instance
        user_ids = inst.__api.groups.getMembers(group_id=inst.__group_id)
        for user in user_ids["items"]:
            user_id = str(user)
            if user_id not in exclude:
                inst.send_message(user_id, message)


class BaseCommand(ABC):
    __slots__ = ()
    _name: str = None
    _description: str = None
    _event_data: tuple = ()
    _args: Tuple[Tuple[str, type]] = None
    _owner_only: bool = False

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
            elif len(cls._args) > len(text_data):
                raise IndexError("Недостаточно аргументов.")
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
        return f"{cls._name} {args} — {cls._description}."

    @classmethod
    def is_owner_only(cls) -> bool:
        return cls._owner_only


class CreateEntitiesCommand(BaseCommand):
    _name = "create"
    _event_data = ("peer_id",)
    _args = (("число", int),)
    _description = "создает {число} существ"
    _owner_only = True

    def on_call(self, data: dict, args: dict, methods: BotMethods) -> None:
        from simulation.components import Rigidbody
        from simulation.settings import MAX_CREATURES
        from simulation.utils import TEAM_COLORS

        count = args["число"]
        entity_manager = World.current_world.get_manager()
        data_filter = entity_manager.create_filter(required=(Rigidbody,))

        def buffered_command():
            c = max(0, min(count, MAX_CREATURES - len(entity_manager.get_entities().filter(data_filter))))
            for i in range(c):
                from simulation.utils import create_named_creature

                entity = entity_manager.create_entity()
                create_named_creature(entity_manager, entity, "Bot" + str(entity.get_id()),
                                      randint(0, len(TEAM_COLORS) - 1))
            methods.send_message(data["peer_id"], f"Создано {c} существ.")

        entity_manager.add_command(buffered_command)


class CreateUserEntityCommand(BaseCommand):
    _name = "creature"
    _event_data = ("peer_id",)
    _args = (("имя", str),)
    _description = "создает существо с именем {имя}"

    def on_call(self, data: dict, args: dict, methods: BotMethods) -> None:
        name = args["имя"]
        entity_manager = World.current_world.get_manager()

        def buffered_command():
            from simulation.utils import create_named_creature, TEAM_COLORS
            from simulation.components import UserId

            entity = entity_manager.create_entity()
            create_named_creature(entity_manager, entity, name, randint(0, len(TEAM_COLORS)))
            id_comp = UserId()
            id_comp.value = str(data["peer_id"])
            entity_manager.add_component(entity, id_comp)

            methods.send_message(data["peer_id"], f"Существо создано. Его номер — {entity.get_id()}.")

        entity_manager.add_command(buffered_command)


class ListCommand(BaseCommand):
    _name = "list"
    _description = "выводит список всех ваших существ"
    _event_data = ("peer_id",)

    def on_call(self, data: dict, args: dict, methods: BotMethods) -> None:
        user_id = data["peer_id"]
        entity_manager = World.current_world.get_manager()
        message = []
        try:
            from simulation.components import UserId, EntityName

            data_filter = entity_manager.create_filter(required=(EntityName, UserId))
            for i in entity_manager.get_entities().filter(data_filter):
                try:
                    if i.get_component(UserId).value == str(user_id):
                        message.append(f"{i.get_component(EntityName).value}, номер — {i.entity.get_id()}.")
                except:
                    continue
            if not message:
                message.append("У вас нет существ, создайте одно с помощью команды creature.")
            methods.send_message(user_id, "\n".join(message))
        except:
            methods.send_message(user_id, "Что-то пошло не так.")


class StatsCommand(BaseCommand):
    _name = "stats"
    _description = "показывает характеристики вашего существа"
    _args = (("номер существа", int),)
    _event_data = ("peer_id",)

    def on_call(self, data: dict, args: dict, methods: BotMethods) -> None:
        user_id = data["peer_id"]
        entity_manager = World.default_world.get_manager()
        message = []

        num = args["номер существа"]
        try:
            from simulation.components import UserId, MoveSpeed, Strength, Health, Hunger
            from simulation.systems import RenderSystem
            from simulation.math import Vector
            from ecs.entities import EntityNotFoundError

            try:
                entity = entity_manager.get_entity(num)
                id_comp = entity_manager.get_component(entity, UserId)

                if id_comp.value != str(user_id):
                    raise EntityNotFoundError()

                stat_comp = entity_manager.get_component(entity, Health)

                if stat_comp is not None:
                    message.append(f"Здоровье: {stat_comp.value}")
                stat_comp = entity_manager.get_component(entity, Strength)
                if stat_comp is not None:
                    message.append(f"Сила: {stat_comp.value}")
                stat_comp = entity_manager.get_component(entity, MoveSpeed)
                if stat_comp is not None:
                    message.append(f"Скорость: {stat_comp.value}")
                stat_comp = entity_manager.get_component(entity, Hunger)
                if stat_comp is not None:
                    message.append(f"Сытость: {stat_comp.value}")

                methods.send_message(user_id, "\n".join(message))
            except:
                methods.send_message(user_id, "Существо не найдено.")
        except:
            methods.send_message(user_id, "Что-то пошло не так.")


class PhotoCommand(BaseCommand):
    _name = "photo"
    _description = "отправляет фото вашего существа"
    _args = (("номер существа", int),)
    _event_data = ("peer_id",)

    def on_call(self, data: dict, args: dict, methods: BotMethods) -> None:
        num = args["номер существа"]
        user_id = data["peer_id"]
        entity_manager = World.current_world.get_manager()
        try:
            from simulation.components import UserId, Position
            from simulation.systems import RenderSystem
            from simulation.math import Vector
            from ecs.entities import EntityNotFoundError
            from core.application import Application, WIDTH, HEIGHT
            from pygame.image import save

            try:
                entity = entity_manager.get_entity(num)
                pos = entity_manager.get_component(entity, Position).value
                if entity_manager.get_component(entity, UserId).value != str(user_id):
                    raise EntityNotFoundError()
                render_system = World.current_world.get_system(RenderSystem)
                render_system.camera_position = pos - Vector(WIDTH / 2, HEIGHT / 2)
                render_surface = Application.get_render_surface()

                def command():
                    save(render_surface, "temp.jpg")
                    methods.send_photo(user_id, "temp.jpg")

                Application.add_post_render_command(lambda: entity_manager.add_command(command))
            except:
                methods.send_message(user_id, "Существо не найдено.")
        except:
            methods.send_message(user_id, "Что-то пошло не так.")


class PauseCommand(BaseCommand):
    _name = "pause"
    _description = "приостанавливает симуляцию"
    _owner_only = True

    def on_call(self, data: dict, args: dict, methods: BotMethods) -> None:
        from core.application import Application
        if Application.set_paused(True):
            methods.broadcast_message("Симуляция приостановлена.")


class UnpauseCommand(BaseCommand):
    _name = "unpause"
    _description = "возобновляет симуляцию"
    _owner_only = True

    def on_call(self, data: dict, args: dict, methods: BotMethods) -> None:
        from core.application import Application
        if Application.set_paused(False):
            methods.broadcast_message("Симуляция возобновлена.")


class BroadcastCommand(BaseCommand):
    _name = "broadcast"
    _description = "отправляет {сообщение} всем участникам сообщества"
    _owner_only = True
    _event_data = ("peer_id",)
    _args = (("сообщение", str),)

    def on_call(self, data: dict, args: dict, methods: BotMethods) -> None:
        bc_id = str(data["peer_id"])
        message = args["сообщение"]
        try:
            methods.broadcast_message(message, (bc_id,))
            methods.send_message(bc_id, "Сообщения отправлены.")
        except:
            methods.send_message(bc_id, "Что-то пошло не так.")


class SetPriorityCommand(BaseCommand):
    _name = "priority"
    _description = "устанавливает приоритет {0: еда, 1: охота} существа {номер существа}"
    _args = (("номер существа", int), ("приоритет", int))
    _event_data = ("peer_id",)

    def on_call(self, data: dict, args: dict, methods: BotMethods) -> None:
        user_id = data["peer_id"]
        entity_manager = World.default_world.get_manager()

        num = args["номер существа"]
        try:
            from simulation.components import UserId, Priority
            from simulation.math import Vector
            from ecs.entities import EntityNotFoundError

            try:
                entity = entity_manager.get_entity(num)
                id_comp = entity_manager.get_component(entity, UserId)

                if id_comp.value != str(user_id):
                    raise EntityNotFoundError()

                p_comp = entity_manager.get_component(entity, Priority)
                if args["приоритет"] == 0:
                    p_comp.target = "gathering"
                elif args["приоритет"] == 1:
                    p_comp.target = "hunting"
                else:
                    methods.send_message(user_id, "Ошибка ввода.")
                    return

                methods.send_message(user_id, "Сделано.")
            except:
                methods.send_message(user_id, "Существо не найдено.")
        except:
            methods.send_message(user_id, "Что-то пошло не так.")