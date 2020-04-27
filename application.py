import pygame
from profiling import Profiler


WIDTH, HEIGHT = 800, 600
BACKGROUND_COLOR = (0, 0, 0)


class Application:
    from ecs.world import World
    from main_timer import Time
    __slots__ = ("__screen", "__is_running", "__clock")

    def __init__(self):
        if not pygame.get_init():
            pygame.init()

        self.__is_running = False
        self.__screen: pygame.Surface = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF)
        self.__clock = pygame.time.Clock()

        Application.World.default_world = Application.World()

    def run(self) -> None:
        Profiler.begin_profile_session()

        self.__is_running = True
        while self.__is_running:
            self.__screen.fill(BACKGROUND_COLOR)

            Application.World.update_current()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.__is_running = False
                    break

            Application.Time.tick()

        Profiler.end_profile_session()
        pygame.quit()

