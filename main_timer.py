TARGET_FPS = 60


class Time:
    from time import time
    from pygame import time as pg_time
    __slots__ = ()
    __clock = pg_time.Clock()
    __last_tick_time = 0
    __delta_time = 0
    __update_frequency = 1.0 / TARGET_FPS

    @staticmethod
    def tick() -> None:
        Time.__clock.tick(TARGET_FPS)
        cur_time = Time.time()
        Time.__delta_time = (cur_time - Time.__last_tick_time) * Time.__update_frequency
        Time.__last_tick_time = cur_time

    @staticmethod
    def get_delta_time() -> float:
        return Time.__delta_time
