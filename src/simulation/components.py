from src.ecs.component import BaseComponent
import sqlalchemy as sa
from src.ecs.entities import EntityManager
from src.simulation.math import Vector
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

    def on_remove(self) -> None:
        self.sprite.kill()


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
    sql_x = sa.Column(sa.Float, name="x", nullable=True)
    sql_y = sa.Column(sa.Float, name="y", nullable=True)

    def __init__(self):
        self.value = None

    def from_database(self, entity_manager) -> None:
        if self.sql_x is not None and self.sql_y is not None:
            self.value = Vector(self.sql_x, self.sql_y)
        else:
            self.value = None

    def to_database(self) -> None:
        if self.value is not None:
            self.sql_x = self.value.x
            self.sql_y = self.value.y
        else:
            self.sql_x = None
            self.sql_y = None
 

class EntityName(BaseComponent):
    __slots__ = ("value",)
    sql_name = sa.Column(sa.String, name="name")

    def __init__(self):
        self.value = None

    def from_database(self, entity_manager: EntityManager) -> None:
        self.value = self.sql_name

    def to_database(self) -> None:
        self.sql_name = self.value


class UserId(BaseComponent):
    __slots__ = ("value", "peer_id")
    sql_user_id = sa.Column(sa.String, name="user_id")
    sql_peer_id = sa.Column(sa.String, name="peer_id")

    def __init__(self):
        self.value = None
        self.peer_id = None

    def from_database(self, entity_manager) -> None:
        self.value = self.sql_user_id
        self.peer_id = self.sql_peer_id

    def to_database(self) -> None:
        self.sql_user_id = self.value
        self.sql_peer_id = self.peer_id


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
    __slots__ = ("current", "target")
    sql_current = sa.Column(sa.String, name="current", nullable=True)
    sql_target = sa.Column(sa.String, name="target", nullable=True)

    def __init__(self):
        self.current = None
        self.target = None

    def from_database(self, entity_manager: EntityManager) -> None:
        self.current = self.sql_current
        self.target = self.sql_target

    def to_database(self) -> None:
        self.sql_current = self.current
        self.sql_target = self.target


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


class Rigidbody(BaseComponent):
    __slots__ = ("radius", "velocity")
    sql_radius = sa.Column(sa.Float, name="radius")
    sql_velocity_x = sa.Column(sa.Float, name="velocity_x")
    sql_velocity_y = sa.Column(sa.Float, name="velocity_y")

    def __init__(self):
        self.radius = 0
        self.velocity = Vector(0, 0)

    def from_database(self, entity_manager) -> None:
        self.radius = self.sql_radius
        self.velocity = Vector(self.sql_velocity_x, self.sql_velocity_y)

    def to_database(self) -> None:
        self.sql_radius = self.radius
        self.sql_velocity_x = self.velocity.x
        self.sql_velocity_y = self.velocity.y


class Health(BaseComponent):
    __slots__ = ("value",)
    sql_health = sa.Column(sa.Float, name="health")

    def __init__(self):
        self.value = 0

    def from_database(self, entity_manager) -> None:
        self.value = self.sql_health

    def to_database(self) -> None:
        self.sql_health = self.value


class Team(BaseComponent):
    __slots__ = ("value",)
    sql_team = sa.Column(sa.Integer, name="team")

    def __init__(self):
        self.value = 0

    def from_database(self, entity_manager) -> None:
        self.value = self.sql_team

    def to_database(self) -> None:
        self.sql_team = self.value


class DeadTag(BaseComponent):
    __slots__ = ("reason",)
    sql_reason = sa.Column(sa.String, name="reason", nullable=True)

    def __init__(self, reason: str = None):
        self.reason = reason

    def to_database(self) -> None:
        self.sql_reason = self.reason

    def from_database(self, entity_manager) -> None:
        self.reason = self.sql_reason


class LifeTime(BaseComponent):
    __slots__ = ("value",)
    sql_time = sa.Column(sa.Float, name="time")

    def __init__(self):
        self.value = 0

    def to_database(self) -> None:
        self.sql_time = self.value

    def from_database(self, entity_manager) -> None:
        self.value = self.sql_time
