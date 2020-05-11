import pygame
from src.core.profiling import Profiler
from src.ecs.world import World
from src.core.main_timer import Time
from src.core.input import Mouse


WIDTH, HEIGHT = 800, 600
BACKGROUND_COLOR = (102, 102, 51)


class Application:
    __slots__ = ("__screen", "__is_running", "__clock", "__pr_commands", "__is_paused")
    __instance: "Application" = None

    def __init__(self):

        if Application.__instance is None:
            pygame.init()
            Application.__instance = self
        else:
            raise Exception()

        self.__is_running = False
        self.__screen: pygame.Surface = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF)
        self.__clock = pygame.time.Clock()
        self.__pr_commands = []
        self.__is_paused = False

        World.default_world = World()

    def run(self, profile=False, clear_log=False) -> None:
        from src.vk_bot.commands import BotMethods
        BotMethods.broadcast_message("Мы онлайн.")

        Profiler.begin_profile_session()
        World.default_world.create_all_systems()
        self.__is_running = True

        Time.tick()
        Time.tick()

        while self.__is_running:
            events_found = False
            for event in pygame.event.get():
                events_found = True
                Mouse.handle_event(event)
                if event.type == pygame.QUIT:
                    self.__is_running = False
                    break
            if not events_found:
                Mouse.handle_event(None)

            if self.__is_paused:
                continue

            self.__screen.fill(BACKGROUND_COLOR)
            World.update_current()

            Time.tick()

            pygame.display.flip()

            for com in self.__pr_commands:
                try:
                    com()
                except:
                    continue
            self.__pr_commands.clear()

            pygame.display.set_caption(str(int(Time.get_fps())))

        if clear_log:
            Profiler.clear_log()
        if profile:
            Profiler.end_profile_session()

        pygame.quit()

    @staticmethod
    def get_render_surface():
        return Application.__instance.__screen

    @staticmethod
    def add_post_render_command(command) -> None:
        Application.__instance.__pr_commands.append(command)

    @staticmethod
    def terminate() -> None:
        from src.vk_bot.commands import BotMethods
        from time import sleep
        import os
        BotMethods.broadcast_message("Мы оффлайн.")
        sleep(0.2)
        os._exit(0)

    @staticmethod
    def set_paused(value: bool) -> bool:
        result = Application.__instance.__is_paused != value
        Application.__instance.__is_paused = value
        return result
