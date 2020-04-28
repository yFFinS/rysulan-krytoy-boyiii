import pygame
from profiling import Profiler


WIDTH, HEIGHT = 800, 600
BACKGROUND_COLOR = (0, 0, 0)


class Application:
    __slots__ = ("__screen", "__is_running", "__clock")
    __instance: "Application" = None

    def __init__(self):

        from ecs.world import World

        if Application.__instance is None:
            pygame.init()
            Application.__instance = self
        else:
            raise Exception()

        self.__is_running = False
        self.__screen: pygame.Surface = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF)
        self.__clock = pygame.time.Clock()

        World.default_world = World()

    def run(self, profile: bool = False, clear_log: bool = False) -> None:

        from ecs.world import World
        from main_timer import Time

        if profile:
            Profiler.begin_profile_session()

        World.default_world.create_all_systems()

        self.__is_running = True
        while self.__is_running:
            self.__screen.fill(BACKGROUND_COLOR)

            World.update_current()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.__is_running = False
                    break
            pygame.display.flip()
            Time.tick()
            pygame.display.set_caption(str(int(Time.get_fps())))

        if clear_log:
            Profiler.clear_log()
        if profile:
            Profiler.end_profile_session()

        pygame.quit()

    @staticmethod
    def get_render_surface() -> pygame.Surface:
        return Application.__instance.__screen
