from pygame.locals import MOUSEBUTTONUP, MOUSEBUTTONDOWN
from pygame.event import EventType
from pygame import mouse
from enum import Enum
from simulation.math import Vector


class MouseState(Enum):
    NONE = 0
    PRESSED = 1
    HOLD = 2
    RELEASED = 3


class Mouse:
    __slots__ = ()
    __state: MouseState = MouseState.NONE
    __position: Vector = Vector(0, 0)

    @staticmethod
    def handle_event(event: EventType) -> None:
        pos = mouse.get_pos()
        Mouse.__position = Vector(pos[0], pos[1])

        if event.type == MOUSEBUTTONDOWN:
            Mouse.__state = MouseState.PRESSED
        elif event.type == MOUSEBUTTONUP:
            Mouse.__state = MouseState.RELEASED
        elif Mouse.__state != MouseState.HOLD:
            if Mouse.__state == MouseState.PRESSED:
                Mouse.__state = MouseState.HOLD
            else:
                Mouse.__state = MouseState.NONE

    @staticmethod
    def is_mouse_down() -> bool:
        return Mouse.__state == MouseState.PRESSED

    @staticmethod
    def is_mouse_up() -> bool:
        return Mouse.__state == MouseState.RELEASED

    @staticmethod
    def is_mouse() -> bool:
        return Mouse.__state == MouseState.HOLD

    @staticmethod
    def get_position() -> Vector:
        return Mouse.__position
