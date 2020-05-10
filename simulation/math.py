from typing import Tuple
from math import sqrt


class Vector:
    __slots__ = ("x", "y")
    x: float
    y: float

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def to_tuple(self) -> Tuple[float, float]:
        return self.x, self.y

    @staticmethod
    def clone(vector: "Vector") -> "Vector":
        return Vector(vector.x, vector.y)

    def __repr__(self):
        return "Vector" + self.__str__()

    def __str__(self):
        return f"({self.x}, {self.y})"

    def __iadd__(self, other: "Vector"):
        self.x += other.x
        self.y += other.y
        return self

    def __add__(self, other: "Vector"):
        vec = Vector.clone(self)
        vec += other
        return vec

    def __isub__(self, other: "Vector"):
        self.x -= other.x
        self.y -= other.y
        return self

    def __sub__(self, other: "Vector"):
        vec = Vector.clone(self)
        vec -= other
        return vec

    def __imul__(self, other: float):
        self.x *= other
        self.y *= other
        return self

    def __mul__(self, other: float):
        vec = Vector.clone(self)
        vec *= other
        return vec

    def __itruediv__(self, other: float):
        self.x /= other
        self.y /= other
        return self

    def __truediv__(self, other: float):
        vec = Vector.clone(self)
        vec /= other
        return vec

    def __neg__(self):
        return Vector(-self.x, -self.y)

    def normalized(self) -> "Vector":
        self_len = self.len()
        return Vector(self.x / self_len, self.y / self_len) if self_len else Vector(0, 0)

    def __eq__(self, other):
        return abs(self.x - other.x) < 0.0001 and abs(self.y - other.y) < 0.0001

    def __ne__(self, other):
        return not self == other

    def sqr_len(self) -> float:
        return self.x * self.x + self.y * self.y

    def len(self) -> float:
        return sqrt(self.sqr_len())

    def __hash__(self):
        return hash(self.to_tuple())