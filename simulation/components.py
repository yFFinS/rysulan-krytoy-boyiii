from ecs.component import BaseComponent
import sqlalchemy as sa
from ecs.entities import EntityManager
from simulation.math import Vector
from pygame import image, sprite


class RenderSprite(BaseComponent):
    __slots__ = ("sprite",)
    sql_image = sa.Column(sa.String, name="image")
    sql_width = sa.Column(sa.Integer, name="width")
    sql_height = sa.Column(sa.Integer, name="height")

    def __init__(self):
        self.sprite = None

    def to_database(self) -> None:
        bin_data = image.tostring(self.sprite.image, "RGBA")
        self.sql_image = bin_data
        rect = self.sprite.image.get_rect()
        self.sql_width = rect.w
        self.sql_height = rect.h

    def from_database(self, entity_manager) -> None:
        self.sprite = sprite.Sprite()
        self.sprite.image = image.fromstring(self.sql_image, (self.sql_width, self.sql_height), "RGBA")
        self.sprite.rect = self.sprite.image.get_rect()


class Position(BaseComponent):
    sql_x = sa.Column(sa.Float, name="x")
    sql_y = sa.Column(sa.Float, name="y")
    __slots__ = ("value",)

    def __init__(self):
        self.value = None

    def from_database(self, entity_manager: EntityManager) -> None:
        self.value = Vector(self.sql_x, self.sql_y)

    def to_database(self) -> None:
        self.sql_x = self.value.x
        self.sql_y = self.value.y


class TargetPosition(BaseComponent):
    __slots__ = ("value",)
    sql_x = sa.Column(sa.Float, name="x")
    sql_y = sa.Column(sa.Float, name="y")

    def __init__(self):
        self.value = None

    def from_database(self, entity_manager) -> None:
        self.value = Vector(self.sql_x, self.sql_y)

    def to_database(self) -> None:
        self.sql_x = self.value.x
        self.sql_y = self.value.y
 

class EntityName(BaseComponent):
    __slots__ = ("value", "entity")
    sql_name = sa.Column(sa.String, name="name")
    sql_linked_entity_id = sa.Column(sa.Integer, name="linked_entity_id")

    def __init__(self):
        self.value = None
        self.entity = None

    def from_database(self, entity_manager: EntityManager) -> None:
        self.value = self.sql_name
        self.entity = entity_manager.get_entity(self.sql_linked_entity_id)

    def to_database(self) -> None:
        self.sql_name = self.value
        self.sql_linked_entity_id = self.entity.get_id()


class MoveSpeed(BaseComponent):
    __slots__ = ("value",)
    sql_speed = sa.Column(sa.Float, name="speed")

    def __init__(self):
        self.value = None

    def from_database(self, entity_manager) -> None:
        self.value = self.sql_speed

    def to_database(self) -> None:
        self.sql_speed = self.value


class Priority(BaseComponent):
    __slots__ = ("value",)
    sql_priority = sa.Column(sa.String, name="priority")

    def __init__(self):
        self.value = None

    def from_database(self, entity_manager: EntityManager) -> None:
        self.value = self.sql_priority

    def to_database(self) -> None:
        self.sql_priority = self.value


class Strength(BaseComponent):
    __slots__ = ("value",)
    sql_strength = sa.Column(sa.Integer, name="strength")

    def __init__(self):
        self.value = None

    def from_database(self, entity_manager: EntityManager) -> None:
        self.value = self.sql_strength

    def to_database(self) -> None:
        self.sql_strength = self.value
        

class Hunger(BaseComponent):
    __slots__ = ("value",)
    sql_hunger = sa.Column(sa.Integer, name="hunger")

    def __init__(self):
        self.value = None

    def from_database(self, entity_manager: EntityManager) -> None:
        self.value = self.sql_hunger

    def to_database(self) -> None:
        self.sql_hunger = self.value


class BushTag(BaseComponent):
    pass
