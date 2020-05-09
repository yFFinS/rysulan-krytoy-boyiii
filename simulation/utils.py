from random import randint
from pygame import Surface, draw
from .settings import *
from ecs.entities import Entity
from .components import *


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
    pos_comp = Position()
    pos_comp.value = Vector(randint(-WORLD_SIZE, WORLD_SIZE), randint(-WORLD_SIZE, WORLD_SIZE))

    target_pos_comp = TargetPosition()
    target_pos_comp.value = None

    render_comp = RenderSprite()
    render_comp.sprite = create_circle(START_CREATURE_SIZE, START_CREATURE_COLOR,
                                       CREATURE_BORDER_COLOR, CREATURE_BORDER_WIDTH)

    move_speed_comp = MoveSpeed()
    move_speed_comp.value = randint(3, 13)

    hunger_comp = Hunger()
    hunger_comp.value = randint(10, 25)

    rb_comp = Rigidbody()
    rb_comp.radius = START_CREATURE_SIZE
    rb_comp.velocity = Vector(0, 0)

    str_comp = Strength()
    str_comp.value = randint(1, 7)

    hp_comp = Health()
    hp_comp.value = randint(50, 151)

    entity_manager.add_component(entity, pos_comp)
    entity_manager.add_component(entity, render_comp)
    entity_manager.add_component(entity, target_pos_comp)
    entity_manager.add_component(entity, move_speed_comp)
    entity_manager.add_component(entity, hunger_comp)
    entity_manager.add_component(entity, rb_comp)
    entity_manager.add_component(entity, str_comp)
    entity_manager.add_component(entity, hp_comp)


def create_food(entity_manager: EntityManager, entity: Entity) -> None:
    pos_comp = Position()
    pos_comp.value = Vector(randint(-WORLD_SIZE, WORLD_SIZE), randint(-WORLD_SIZE, WORLD_SIZE))
    render_comp = RenderSprite()
    render_comp.sprite = create_rect(START_FOOD_SIZE, START_FOOD_SIZE, START_FOOD_COLOR,
                                     FOOD_BORDER_COLOR, FOOD_BORDER_WIDTH)
    entity_manager.add_component(entity, pos_comp)
    entity_manager.add_component(entity, render_comp)
    entity_manager.add_component(entity, BushTag())
