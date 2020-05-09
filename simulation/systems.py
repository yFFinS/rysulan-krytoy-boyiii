from ecs.systems import BaseSystem
from .__all_components import *
from core.input import Mouse
from ecs.world import World
from simulation.math import Vector
import pygame
from .utils import create_food
from .settings import *
from ecs.entities import EntityNotFoundError
from random import random
from ecs.entities import ComponentNotFoundError


class RenderSystem(BaseSystem):

    __update_order__ = 100

    def __init__(self):
        self.__sprites = pygame.sprite.Group()
        self.__render_surface = None
        self.camera_position: Vector = Vector(WORLD_SIZE / 2, WORLD_SIZE / 2)

    def on_create(self):
        from core.application import Application
        self.__render_surface = Application.get_render_surface()
        self.filter = self.entity_manager.create_filter(required=(RenderSprite, Position))

    def on_update(self, delta_time: float):
        __cached_positions = []
        for i in self.query(self.filter):

            render_comp = i.get_component(RenderSprite)
            if not self.__sprites.has(render_comp.sprite):
                self.__sprites.add(render_comp.sprite)

            position_comp = i.get_component(Position)
            __cached_positions.append((render_comp.sprite, position_comp.value.to_tuple()))
            render_comp.sprite.rect.center = (position_comp.value + self.camera_position).to_tuple()

        self.__sprites.draw(self.__render_surface)

        for i in __cached_positions:
            i[0].rect.center = i[1]


class MouseDragSystem(BaseSystem):

    def __init__(self):
        self.__drag_position = None
        self.__render_system = None
        self.__prev_camera_position = None
        self.__dragging = False

    def on_create(self) -> None:
        self.__render_system = World.current_world.get_or_create_system(RenderSystem)
        self.__prev_camera_position = self.__render_system.camera_position

    def on_update(self, delta_time: float) -> None:
        if Mouse.is_mouse_down():
            self.__drag_position = Mouse.get_position()
        if self.__drag_position is not None and Mouse.is_mouse():
            offset = Mouse.get_position() - self.__drag_position
            self.__render_system.camera_position = self.__prev_camera_position + offset
        elif Mouse.is_mouse_up():
            self.__drag_position = None
            self.__prev_camera_position = self.__render_system.camera_position


class EntityNameFollowSystem(BaseSystem):

    def __init__(self):
        self.__cached_positions = dict()
        self.__name_offset = Vector(0, -18)

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Position, EntityName))

    def on_update(self, delta_time: float) -> None:
        for i in self.query(self.filter):
            entity = i.get_component(EntityName).entity
            follow_position_comp = self.__cached_positions.get(entity, None)
            if follow_position_comp is None:
                follow_position_comp = self.entity_manager.get_component(entity, Position)
                self.__cached_positions[entity] = follow_position_comp

            position_comp = i.get_component(Position)
            position_comp.value = follow_position_comp.value + self.__name_offset


class MoveToTargetSystem(BaseSystem):

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(MoveSpeed, Position, TargetPosition))

    def on_update(self, delta_time: float) -> None:
        for i in self.query(self.filter):
            target_pos_comp = i.get_component(TargetPosition)
            pos_comp = i.get_component(Position)
            if target_pos_comp.value is not None:
                if (target_pos_comp.value - pos_comp.value).sqr_len() > 1.5:
                    speed = i.get_component(MoveSpeed).value
                    pos_comp.value += (target_pos_comp.value - pos_comp.value).normalized() * (speed * delta_time)
                else:
                    pos_comp.value = Vector.clone(target_pos_comp.value)
                    target_pos_comp.value = None


class CreateFood(BaseSystem):

    def __init__(self):
        self.time = 3

    def on_update(self, delta_time: float) -> None:
        self.time += delta_time
        if self.time >= FOOD_CREATE_DELAY:
            self.entity_manager.add_command(create_food, self.entity_manager, self.entity_manager.create_entity())
            self.time = 0

            
class HungerSystem(BaseSystem):

    def __init__(self):
        self.hunger_time = 0

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Hunger,), additional=(MoveSpeed,))

    def on_update(self, delta_time: float) -> None:
        self.hunger_time += delta_time
        if self.hunger_time >= HUNGER_TICK_DELAY:
            for i in self.query(self.filter):
                speed_comp = i.get_component(MoveSpeed)
                hunger_comp = i.get_component(Hunger)
                hunger_comp.value -= 1
                if speed_comp is not None:
                    hunger_comp.value -= speed_comp.value * SPEED_HUNGER_MULTIPLIER
                # if hunger_comp.value <= EXTREME_HUNGER_VALUE:
                #     priority_comp = i.get_component(Priority)
                #     priority_comp.value = 'gathering'
                if hunger_comp.value <= 0:
                    self.entity_manager.add_command(self.__kill_creature, i.entity)

            self.hunger_time = 0

    def __kill_creature(self, entity) -> None:
        try:
            self.entity_manager.kill_entity(entity)
        except EntityNotFoundError:
            pass


class GatheringSystem(BaseSystem):

    def __init__(self):
        self.gathering_time = 1

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Position, TargetPosition, Hunger),
                                                        additional=(Health,))
        self.filter2 = self.entity_manager.create_filter(required=(Position, BushTag))

    def on_update(self, delta_time: float) -> None:
        self.gathering_time += delta_time
        bush_pos = []
        if self.gathering_time >= 1:
            for i in self.query(self.filter2):
                bush_pos_comp = i.get_component(Position)
                bush_pos.append((i.entity, bush_pos_comp.value))
            if not bush_pos:
                return
            for i in self.query(self.filter):
                creature_pos_comp = i.get_component(Position)
                creature_target_comp = i.get_component(TargetPosition)
                hp_comp = i.get_component(Health)
                closest_bush = bush_pos[0]
                for j in bush_pos:
                    if (creature_pos_comp.value - j[1]).sqr_len() < (creature_pos_comp.value - closest_bush[1]).sqr_len():
                        closest_bush = j
                creature_target_comp.value = closest_bush[1]
                if (creature_target_comp.value - creature_pos_comp.value).sqr_len() <= EAT_DISTANCE:
                    hunger_comp = i.get_component(Hunger)
                    hunger_comp.value += BUSH_FOOD_VALUE
                    if hp_comp is not None:
                        hp_comp.value += BUSH_FOOD_VALUE
                    self.entity_manager.add_command(self.kill_bush, closest_bush[0])
            self.gathering_time = 0

    def kill_bush(self, bush):
        try:
            self.entity_manager.kill_entity(bush)
        except EntityNotFoundError:
            pass


class PositionLimitSystem(BaseSystem):

    __update_order__ = 5

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Position,))

    def on_update(self, delta_time: float) -> None:
        for i in self.query(self.filter):
            pos_comp = i.get_component(Position)
            pos_comp.value.x = self.__clamp(pos_comp.value.x)
            pos_comp.value.y = self.__clamp(pos_comp.value.y)

    @staticmethod
    def __clamp(value: float) -> float:
        return min(max(-WORLD_SIZE, value), WORLD_SIZE)


class CollisionSystem(BaseSystem):

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Position, Rigidbody), additional=(Strength, Health))

    def on_update(self, delta_time: float) -> None:
        colliders = []
        for i in self.query(self.filter):
            rigidbody_comp = i.get_component(Rigidbody)
            radius = rigidbody_comp.radius
            vel = rigidbody_comp.velocity
            strength_comp = i.get_component(Strength)
            strength = strength_comp.value if strength_comp is not None else 1
            health_comp = i.get_component(Health)
            hp = health_comp.value if health_comp is not None else None

            position = i.get_component(Position).value
            for ent, other_radius, other_position, other_vel, other_strength, other_hp in colliders:
                direction = (other_position - position).normalized()
                sqr_dist = (other_position - position).sqr_len()
                if sqr_dist < (radius + other_radius) * (radius + other_radius):
                    vel -= direction * (delta_time * PUSH_MULTIPLIER * sqr_dist * strength)
                    other_vel += direction * (delta_time * PUSH_MULTIPLIER * sqr_dist * other_strength)
                    if hp is not None:
                        hp -= other_strength
                        if hp <= 0:
                            self.entity_manager.add_command(self.__kill_creature, i.entity)
                    if other_hp is not None:
                        hp -= strength
                        if other_hp <= 0:
                            self.entity_manager.add_command(self.__kill_creature, ent)

            colliders.append((i.entity, radius, position, vel, strength, hp))

        for ent, rad, pos, vel, strength, hp in colliders:
            pos += (vel + Vector(0.5 - random(), 0.5 - random()) * 0.1) * delta_time
            vel *= 1 - DAMPENING

    def __kill_creature(self, entity) -> None:
        try:
            self.entity_manager.kill_entity(entity)
        except EntityNotFoundError:
            pass


class EvolveSystem(BaseSystem):

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Hunger,), additional=(MoveSpeed, Strength, Health))

    def on_update(self, delta_time: float) -> None:
        for i in self.query(self.filter):
            hunger_comp = i.get_component(Hunger)
            if hunger_comp.value >= EVOLVE_HUNGER_VALUE:
                hunger_comp.value -= EVOLVE_HUNGER_COST
                stat_comp = i.get_component(MoveSpeed)
                if stat_comp is not None:
                    stat_comp.value += (0.75 - random()) * 5

                stat_comp = i.get_component(Strength)
                if stat_comp is not None:
                    stat_comp.value += (0.9 - random()) * 6.5

                stat_comp = i.get_component(Health)
                if stat_comp is not None:
                    stat_comp.value += (0.65 - random()) * 14


class MouseHoverInfoSystem(BaseSystem):

    def on_create(self) -> None:
        from core.application import Application
        self.filter = self.entity_manager.create_filter(required=(Position,),
                                                        additional=(MoveSpeed, Hunger, Strength, Health))
        self.__render_system = World.current_world.get_or_create_system(RenderSystem)
        self.__font = pygame.font.Font(None, 30)
        self.__render_surface = Application.get_render_surface()

    def on_update(self, delta_time: float) -> None:
        mouse_pos = Mouse.get_position()
        for i in self.query(self.filter):
            entity_pos = i.get_component(Position).value + self.__render_system.camera_position
            if (entity_pos - mouse_pos).sqr_len() <= 65:
                text = []
                comp = i.get_component(MoveSpeed)
                text.append(f"Entity id: {i.entity.get_id()}")
                if comp is not None:
                    text.append(f"Speed: {'%.2f' % comp.value}")
                comp = i.get_component(Hunger)
                if comp is not None:
                    text.append(f"Hunger: {'%.2f' % comp.value}")
                comp = i.get_component(Strength)
                if comp is not None:
                    text.append(f"Strength: {'%.2f' % comp.value}")
                comp = i.get_component(Health)
                if comp is not None:
                    text.append(f"Health: {'%.2f' % comp.value}")
                line_wrap_dist = 20
                pos = (entity_pos - Vector(50, line_wrap_dist * len(text) + 10)).to_tuple()
                for line in text:
                    render_line = self.__font.render(line, False, (255, 255, 255), (20, 20, 20))
                    self.entity_manager.add_command(self.__render_line, render_line, pos)
                    pos = (pos[0], pos[1] + line_wrap_dist)
                break

    def __render_line(self, line, pos) -> None:
        self.__render_surface.blit(line, pos)