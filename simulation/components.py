from ecs.component import BaseComponent
from simulation.math import *


class RenderSprite(BaseComponent):
    __slots__ = ("sprite",)


class Position(BaseComponent):
    __slots__ = ("value",)
    value: Vector
