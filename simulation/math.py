
class Vector:
    __slots__ = ("x", "y")
    x: float
    y: float

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    from typing import Tuple

    def to_tuple(self) -> Tuple[float, float]:
        return self.x, self.y

    @staticmethod
    def clone(vector: "Vector") -> "Vector":
        return Vector(vector.x, vector.y)

    def __iadd__(self, other: "Vector"):
        self.x += other.x
        self.y += other.y

    def __add__(self, other: "Vector"):
        vec = Vector.clone(self)
        vec += other
        return vec

    def __isub__(self, other: "Vector"):
        self.x -= other.x
        self.y -= other.y

    def __sub__(self, other: "Vector"):
        vec = Vector.clone(self)
        vec -= other
        return vec

    def __imul__(self, other: float):
        self.x *= other
        self.y *= other

    def __mul__(self, other: float):
        vec = Vector.clone(self)
        vec *= other
        return vec
