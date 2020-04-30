from vk_api import vk_api, VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEvent


PROPERTIES_FILE_PATH = "vk_bot/bot.properties"


class Client:
    __slots__ = ("__session", "__api", "__long_poll", "__group_id")
    __session: VkApi
    __api: vk_api.VkApiMethod
    __long_poll: VkBotLongPoll
    __group_id: int

    def __init__(self):
        with open(PROPERTIES_FILE_PATH, "r") as file:
            for line in file.readlines():
                line_data = line.strip().split()
                if "group_id" in line:
                    self.__group_id = int(line_data[-1])
                if "token" in line:
                    self.__session = VkApi(token=line_data[-1])
            self.__api = self.__session.get_api()
            self.__long_poll = VkBotLongPoll(self.__session, self.__group_id)

    def send_message(self, chat_id: int, message: str) -> None:
        self.__api.messages.send(chat_id=chat_id, message=message)

    def listen(self) -> None:
        for event in self.__long_poll.listen():
            pass


def init():
    from threading import Thread
    client = Client()
    bot_thread = Thread(target=client.listen)
    bot_thread.start()
    print("Bot is running.")
