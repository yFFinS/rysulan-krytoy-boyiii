from ecs.component import BaseComponent
from simulation.math import *
import sqlalchemy as sa


class RenderSprite(BaseComponent):
    __slots__ = ("sprite",)


class Position(BaseComponent):
    __slots__ = ("value",)