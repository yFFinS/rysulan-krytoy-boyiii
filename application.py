import pygame
from profiling import Profiler
from ecs.world import World
from main_timer import Time
from input import Mouse
import os


WIDTH, HEIGHT = 800, 600
BACKGROUND_COLOR = (0, 0, 0)


class Application:
    __slots__ = ("__screen", "__is_running", "__clock")
    __instance = None

    def __init__(self):

        if Application.__instance is None:
            pygame.init()
            Application.__instance = self
        else:
            raise Exception()

        self.__is_running = False
        self.__screen: pygame.Surface = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF)
        self.__clock = pygame.time.Clock()

        World.default_world = World()

    def run(self, profile=False, clear_log=False) -> None:
        Profiler.begin_profile_session()
        World.default_world.create_all_systems()
        self.__is_running = True
        while self.__is_running:
            self.__screen.fill(BACKGROUND_COLOR)

            for event in pygame.event.get():
                Mouse.handle_event(event)
                if event.type == pygame.QUIT:
                    self.__is_running = False
                    break

            World.update_current()

            pygame.display.flip()
            Time.tick()

            pygame.display.set_caption(str(int(Time.get_fps())))

        if clear_log:
            Profiler.clear_log()
        if profile:
            Profiler.end_profile_session()

        pygame.quit()
        os._exit(0)

    @staticmethod
    def get_render_surface():
        return Application.__instance.__screen
