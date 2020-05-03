from typing import Tuple


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
