from vk_api import vk_api, VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType, VkBotEvent
from vk_bot.commands import *
from typing import Dict, TypeVar


PROPERTIES_FILE_PATH = "vk_bot/bot.properties"


class Client:
    from vk_bot.commands import BaseCommand
    __slots__ = ("__session", "__methods", "__long_poll", "__group_id", "__commands")
    __session: VkApi
    __api: vk_api.VkApiMethod
    __long_poll: VkBotLongPoll
    __group_id: int
    __methods: BotMethods

    TCommand = TypeVar("TCommand", bound=BaseCommand)
    __commands: Dict[str, TCommand]

    def __init__(self):
        with open(PROPERTIES_FILE_PATH, "r") as file:
            for line in file.readlines():
                line_data = line.strip().split("=")
                if "group_id" in line:
                    self.__group_id = int(line_data[-1])
                if "token" in line:
                    self.__session = VkApi(token=line_data[-1])
            self.__long_poll = VkBotLongPoll(self.__session, self.__group_id)
        self.__methods = BotMethods(self.__session)
        self.__commands = {}
        for command_type in BaseCommand.__subclasses__():
            command = command_type()
            self.__commands[command.get_name()] = command

    def listen(self) -> None:
        for event in self.__long_poll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                self.__process_command(event)

    @staticmethod
    def __get_command(event: VkBotEvent) -> str:
        return event.obj["text"].strip().split()[0]

    def __process_command(self, event: VkBotEvent) -> None:
        name = self.__get_command(event)
        command = self.__commands.get(name, None)
        if command is not None:
            command.on_call(command.filter_data(event.obj), self.__methods)


def init():
    from threading import Thread
    client = Client()
    bot_thread = Thread(target=client.listen)
    bot_thread.start()
    print("Bot is running.")
