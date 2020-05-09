from pygame.time import Clock
from time import time


TARGET_FPS = 100


class Time:
    __slots__ = ()
    __clock = Clock()
    __last_tick_time = 0
    __delta_time = 0

    @staticmethod
    def tick() -> None:
        cur_time = time()
        Time.__delta_time = cur_time - Time.__last_tick_time
        Time.__last_tick_time = cur_time
        Time.__clock.tick(TARGET_FPS)

    @staticmethod
    def get_delta_time() -> float:
        return Time.__delta_time

    @staticmethod
    def get_fps() -> float:
        return 1 / Time.__delta_time if Time.__delta_time != 0 else 1 / TARGET_FPS
