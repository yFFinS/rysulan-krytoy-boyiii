import vk_api
import vk_api.longpoll


TOKEN_FILE_PATH = "vk_bot/token.txt"


class Client:
    __slots__ = ("__session", "__api", "__longpoll")
    __session: vk_api.VkApi
    __api: vk_api.vk_api.VkApiMethod
    __longpoll: vk_api.longpoll.VkLongPoll

    def __init__(self):
        with open(TOKEN_FILE_PATH, "r") as file:
            for line in file.readlines():
                line = line.strip()
                if " " in line or not line:
                    continue
                print(line)
                self.__session = vk_api.VkApi(token=line)
                self.__api = self.__session.get_api()
                self.__longpoll = vk_api.longpoll.VkLongPoll(self.__session)
                return
            print("Token not found.")

    def send_message(self, chat_id: int, message: str) -> None:
        self.__api.messages.send(chat_id=chat_id, message=message)

    def listen(self) -> None:
        for event in self.__longpoll.listen():
            pass


def init():
    from threading import Thread
    client = Client()
    bot_thread = Thread(target=client.listen)
    bot_thread.start()
    print("Bot is running.")
