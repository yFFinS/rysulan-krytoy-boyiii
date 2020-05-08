from random import randint
from pygame import sprite, Surface, draw
from .math import Vector
from .settings import *
from ecs.entities import Entity, EntityManager


def create_rect(width: int, height: int, fill_color, border_color=None, border_width=1):
    rect_sprite = sprite.Sprite()
    rect_sprite.image = Surface((width, height))
    rect_sprite.image.fill(fill_color)
    rect_sprite.rect = rect_sprite.image.get_rect()
    if border_color is not None:
        draw.rect(rect_sprite.image, border_color, (0, 0, width, height), border_width)
    return rect_sprite


def create_circle(radius: int, fill_color, border_color=None, border_width=1):
    circle_sprite = sprite.Sprite()
    circle_sprite.image = Surface((2 * radius, 2 * radius))
    circle_sprite.rect = circle_sprite.image.get_rect()
    draw.circle(circle_sprite.image, fill_color, (radius, radius), radius, 0)
    if border_color is not None:
        draw.circle(circle_sprite.image, border_color,
                    (radius, radius), radius + border_width, border_width)
    circle_sprite.image.set_colorkey((0, 0, 0))
    return circle_sprite


def create_creature(entity_manager: EntityManager, entity: Entity) -> None:
    from .components import Position, RenderSprite, TargetPosition, MoveSpeed
    pos_comp = Position()
    pos_comp.value = Vector(randint(-WORLD_SIZE, WORLD_SIZE), randint(-WORLD_SIZE, WORLD_SIZE))
    target_pos_comp = TargetPosition()
    target_pos_comp.value = Vector(randint(-WORLD_SIZE, WORLD_SIZE), randint(-WORLD_SIZE, WORLD_SIZE))
    render_comp = RenderSprite()
    render_comp.sprite = create_circle(START_CREATURE_SIZE, START_CREATURE_COLOR,
                                       CREATURE_BORDER_COLOR, CREATURE_BORDER_WIDTH)
    move_speed_comp = MoveSpeed()
    move_speed_comp.value = randint(10, 100) / 15
    entity_manager.add_component(entity, pos_comp)
    entity_manager.add_component(entity, render_comp)
    entity_manager.add_component(entity, target_pos_comp)
    entity_manager.add_component(entity, move_speed_comp)