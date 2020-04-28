TARGET_FPS = 60


class Time:
    from pygame import time as pg_time
    __slots__ = ()
    __clock = pg_time.Clock()

    @staticmethod
    def tick() -> None:
        Time.__clock.tick(TARGET_FPS)

    @staticmethod
    def get_delta_time() -> float:
        return 1 / max(1.0, Time.get_fps())

    @staticmethod
    def get_fps() -> float:
        return Time.__clock.get_fps()