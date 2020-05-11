from vk_api import VkApi, VkApiError
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType, VkBotEvent
from src.vk_bot.commands import *
from typing import Dict, TypeVar
from os.path import exists


PROPERTIES_FILE_PATH = "bot.properties"


class Client:
    from src.vk_bot.commands import BaseCommand
    __slots__ = ("__session", "__methods", "__long_poll", "__group_id", "__commands", "__owners")
    __session: VkApi
    __long_poll: VkBotLongPoll
    __group_id: str
    __methods: BotMethods
    __owners: Tuple[str]

    TCommand = TypeVar("TCommand", bound=BaseCommand)
    __commands: Dict[str, TCommand]

    def __init__(self):
        if not exists(PROPERTIES_FILE_PATH):
            with open(PROPERTIES_FILE_PATH, "w") as file:
                file.write("token=\ngroup_id=\n# AAAAAAA; BBBBBBBBB; CCCCCCCC\nowner_ids=")
            print("You need to set bot properties.")
            input("Press enter to close...")
            exit(0)
        try:
            with open(PROPERTIES_FILE_PATH, "r") as file:
                for line in file.readlines():
                    line_data = line.strip().split("=")
                    if "group_id" in line:
                        self.__group_id = line_data[-1]
                    if "token" in line:
                        self.__session = VkApi(token=line_data[-1])
                    if "owner_ids" in line:
                        self.__owners = tuple(map(str.strip, line_data[-1].split(";")))
                self.__long_poll = VkBotLongPoll(self.__session, self.__group_id)
            self.__methods = BotMethods(self.__session, self.__group_id)
            self.__commands = dict()
        except VkApiError:
            print("Wrong token or group id.")
            input("Press enter to close...")
            exit(0)
        for command_type in BaseCommand.__subclasses__():
            command = command_type()
            self.__commands[command.get_name()] = command

        self.__methods.set_online(True)

    def listen(self) -> None:
        for event in self.__long_poll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                self.__process_command(event)

    @staticmethod
    def __get_command(event: VkBotEvent) -> str:
        text = event.obj["text"].strip().split()
        return text[0] if text else ""

    def __process_command(self, event: VkBotEvent) -> None:
        name = self.__get_command(event)
        if name == "help":
            self.__help_command(event)
            return
        command = self.__commands.get(name, None)
        if command is not None:
            if command.is_owner_only() and str(event.obj["from_id"]) not in self.__owners:
                return
            try:
                command.on_call(command.filter_data(event.obj), command.parse_args(event.obj["text"]), self.__methods)
            except BaseException as e:
                self.__methods.send_message(str(event.obj["peer_id"]), str(e))

    def __help_command(self, event) -> None:
        message_data = []
        for command in self.__commands.values():
            if command.is_owner_only() and str(event.obj["from_id"]) not in self.__owners:
                continue
            message_data.append(command.help_data())
        self.__methods.send_message(event.obj["peer_id"], "\n".join(message_data))


def init():
    from threading import Thread
    client = Client()
    bot_thread = Thread(target=client.listen)
    bot_thread.start()
    print("Bot is running.")
