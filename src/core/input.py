from pygame.locals import MOUSEBUTTONUP, MOUSEBUTTONDOWN, BUTTON_LEFT, BUTTON_RIGHT
from pygame import mouse
from enum import Enum
from src.simulation.math import Vector


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
    def handle_event(event) -> None:
        pos = mouse.get_pos()
        Mouse.__position = Vector(pos[0], pos[1])
        if event is None or event.type not in (MOUSEBUTTONDOWN, MOUSEBUTTONUP):
            if Mouse.__state == MouseState.PRESSED or Mouse.__state == MouseState.HOLD:
                Mouse.__state = MouseState.HOLD
            else:
                Mouse.__state = MouseState.NONE
        else:
            if event.type == MOUSEBUTTONDOWN and event.button in (BUTTON_LEFT, BUTTON_RIGHT):
                Mouse.__state = MouseState.PRESSED
            if event.type == MOUSEBUTTONUP:
                Mouse.__state = MouseState.RELEASED

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
