from math import ceil
from random import random, randint

import pygame

from core.input import Mouse
from ecs.entities import ComponentNotFoundError
from ecs.entities import EntityNotFoundError
from ecs.systems import BaseSystem
from ecs.world import World
from .__all_components import *
from .settings import *
from .utils import create_food, create_named_creature, TEAM_COLORS


class RenderSystem(BaseSystem):
    __update_order__ = 100

    def __init__(self):
        self.__sprites = pygame.sprite.Group()
        self.__render_surface = None
        from core.application import WIDTH, HEIGHT
        self.camera_position: Vector = Vector(WIDTH / 2, HEIGHT / 2)
        self.filter = None

    def on_create(self):
        from core.application import Application
        self.__render_surface = Application.get_render_surface()
        self.filter = self.entity_manager.create_filter(required=(RenderSprite, Position),
                                                        without=(DeadTag,))

    def on_update(self, delta_time: float):
        cached_positions = []
        for i in self.query(self.filter):

            render_comp = i.get_component(RenderSprite)
            if not self.__sprites.has(render_comp.sprite):
                self.__sprites.add(render_comp.sprite)

            position_comp = i.get_component(Position)
            cached_positions.append((render_comp.sprite, position_comp.value.to_tuple()))
            render_comp.sprite.rect.center = (position_comp.value + self.camera_position).to_tuple()

        self.__sprites.draw(self.__render_surface)

        for i in cached_positions:
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
        self.filter = None

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Position, EntityName),
                                                        without=(DeadTag,))

    def on_update(self, delta_time: float) -> None:
        for i in self.query(self.filter):
            entity = i.get_component(EntityName).entity
            if not self.entity_manager.has_entity(entity):
                self.entity_manager.add_component(i.entity, DeadTag())
                return
            follow_position_comp = self.__cached_positions.get(entity, None)
            if follow_position_comp is None:
                try:
                    follow_position_comp = self.entity_manager.get_component(entity, Position)
                    self.__cached_positions[entity] = follow_position_comp
                except ComponentNotFoundError:
                    self.entity_manager.add_component(i.entity, DeadTag())
                    return
            position_comp = i.get_component(Position)
            position_comp.value = follow_position_comp.value + self.__name_offset


class MoveToTargetSystem(BaseSystem):

    def __init__(self):
        self.filter = None

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(MoveSpeed, Position, TargetPosition),
                                                        without=(DeadTag,))

    def on_update(self, delta_time: float) -> None:
        for i in self.query(self.filter):
            target_pos_comp = i.get_component(TargetPosition)
            pos_comp = i.get_component(Position)
            if target_pos_comp.value is not None:
                target_pos = target_pos_comp.value
                pos = pos_comp.value
                if (target_pos - pos).sqr_len() > 4:
                    speed = i.get_component(MoveSpeed).value
                    pos += (target_pos - pos).normalized() * (speed * delta_time)
                else:
                    pos_comp.value = Vector.clone(target_pos)
                    target_pos_comp.value = None


class CreateFood(BaseSystem):

    def __init__(self):
        self.time = 3
        self.filter = None

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(BushTag,))

    def on_update(self, delta_time: float) -> None:
        self.time += delta_time
        if self.time >= FOOD_CREATE_DELAY:
            if len(self.query(self.filter)) <= MAX_FOOD:
                self.entity_manager.add_command(create_food, self.entity_manager, self.entity_manager.create_entity())
                self.time = 0


class HungerSystem(BaseSystem):

    def __init__(self):
        self.hunger_time = 0
        self.filter = None

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Hunger,), additional=(MoveSpeed, Priority),
                                                        without=(DeadTag,))

    def on_update(self, delta_time: float) -> None:
        self.hunger_time += delta_time
        if self.hunger_time >= HUNGER_TICK_DELAY:
            for i in self.query(self.filter):
                speed_comp = i.get_component(MoveSpeed)
                hunger_comp = i.get_component(Hunger)
                hunger_comp.value -= 1
                if speed_comp is not None:
                    hunger_comp.value -= speed_comp.value * SPEED_HUNGER_MULTIPLIER
                if hunger_comp.value <= 0:
                    self.entity_manager.add_component(i.entity, DeadTag())

            self.hunger_time = 0


class ExtremePrioritySystem(BaseSystem):

    def __init__(self):
        self.extreme_priority_time = 0
        self.filter = None

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Hunger, Health), additional=(Priority,),
                                                        without=(DeadTag,))

    def on_update(self, delta_time: float) -> None:
        self.extreme_priority_time += delta_time
        if self.extreme_priority_time >= 1:
            for i in self.query(self.filter):
                hp_comp = i.get_component(Health)
                hunger_comp = i.get_component(Hunger)
                if hunger_comp.value <= EXTREME_HUNGER_VALUE:
                    priority_comp = i.get_component(Priority)
                    if priority_comp:
                        priority_comp.value = 'gathering'
                if hp_comp.value <= EXTREME_HEALTH_VALUE:
                    priority_comp = i.get_component(Priority)
                    if priority_comp:
                        priority_comp.value = 'safety'
            self.extreme_priority_time = 0


class GatheringSystem(BaseSystem):

    def __init__(self):
        self.gathering_time = 1
        self.filter = None
        self.filter2 = None

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Position, TargetPosition, Hunger),
                                                        additional=(Health, Priority),
                                                        without=(DeadTag,))
        self.filter2 = self.entity_manager.create_filter(required=(Position, BushTag),
                                                         without=(DeadTag,))

    def on_update(self, delta_time: float) -> None:
        self.gathering_time += delta_time
        if self.gathering_time >= 1:
            bush_pos = []
            for i in self.query(self.filter2):
                bush_pos_comp = i.get_component(Position)
                bush_pos.append((i.entity, bush_pos_comp.value))
            if not bush_pos:
                return
            for i in self.query(self.filter):
                priority = i.get_component(Priority)
                if priority is not None and priority.value != "gathering":
                    continue
                creature_pos_comp = i.get_component(Position)
                creature_target_comp = i.get_component(TargetPosition)
                hp_comp = i.get_component(Health)
                closest_bush = bush_pos[0]
                for j in bush_pos:
                    if (creature_pos_comp.value - j[1]).sqr_len() < (
                            creature_pos_comp.value - closest_bush[1]).sqr_len():
                        closest_bush = j
                creature_target_comp.value = closest_bush[1]
                if (creature_target_comp.value - creature_pos_comp.value).sqr_len() <= EAT_DISTANCE:
                    hunger_comp = i.get_component(Hunger)
                    hunger_comp.value += BUSH_FOOD_VALUE
                    if hp_comp is not None:
                        hp_comp.value += BUSH_FOOD_VALUE
                    self.entity_manager.add_component(closest_bush[0], DeadTag())
            self.gathering_time = 0


class HuntingSystem(BaseSystem):

    def __init__(self):
        self.filter = None
        self.hunting_time = 1

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Position, TargetPosition, Hunger, Strength, Health),
                                                        additional=(Priority,),
                                                        without=(DeadTag,))

    def on_update(self, delta_time: float) -> None:
        self.hunting_time += delta_time
        if self.hunting_time >= 1:
            creatures = tuple(self.query(self.filter))
            for i in creatures:
                priority_comp = i.get_component(Priority)
                if priority_comp is not None and priority_comp.value != 'hunting':
                    continue
                hp_comp = i.get_component(Health)
                if hp_comp.value < 100:
                    continue

                pos_comp = i.get_component(Position)
                target_comp = i.get_component(TargetPosition)
                strength = i.get_component(Strength).value

                closest_pos = creatures[0].get_component(Position).value

                for j in creatures:
                    if j == i:
                        continue
                    pos = j.get_component(Position).value

                    if (pos_comp.value - pos).sqr_len() < (pos_comp.value - closest_pos).sqr_len()\
                            and j.get_component(Health).value / strength\
                            >= hp_comp.value / j.get_component(Strength).value:
                        closest_pos = pos
                target_comp.value = closest_pos
            self.hunting_time = 0


class SafetySystem(BaseSystem):

    def __init__(self):
        self.filter = None
        self.safety_time = 1

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Position, TargetPosition),
                                                        additional=(Priority,),
                                                        without=(DeadTag,))

    def on_update(self, delta_time: float) -> None:
        self.safety_time += delta_time
        if self.safety_time >= 1:
            creatures = tuple(self.query(self.filter))
            for i in creatures:
                priority_comp = i.get_component(Priority)
                if priority_comp is not None and priority_comp.value != 'safety':
                    continue

                pos_comp = i.get_component(Position)
                target_comp = i.get_component(TargetPosition)

                closest_pos = creatures[0].get_component(Position).value

                for j in creatures:
                    if j == i:
                        continue
                    pos = j.get_component(Position).value

                    if (pos_comp.value - pos).sqr_len() < (pos_comp.value - closest_pos).sqr_len():
                        closest_pos = pos
                target_comp.value = pos_comp.value * 2 - closest_pos
                if (pos_comp.value - closest_pos).sqr_len() > SAFETY_DISTANCE * SAFETY_DISTANCE:
                    target_comp.value = None

            self.safety_time = 0


class PositionLimitSystem(BaseSystem):
    __update_order__ = 5

    def __init__(self):
        self.filter = None

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Position,), without=(EntityName,))

    def on_update(self, delta_time: float) -> None:
        for i in self.query(self.filter):
            pos_comp = i.get_component(Position)
            pos_comp.value = pos_comp.value.normalized() * min(pos_comp.value.len(), WORLD_SIZE)


class CollisionSystem(BaseSystem):
    __update_order__ = -5

    def __init__(self):
        self.filter = None
        self.simplification_value = 10

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Position, Rigidbody),
                                                        additional=(Strength, Health, Team, Hunger))

    def on_update(self, delta_time: float) -> None:
        colliders = dict()

        for i in self.query(self.filter):
            rigidbody_comp = i.get_component(Rigidbody)
            radius = rigidbody_comp.radius
            vel = rigidbody_comp.velocity
            strength_comp = i.get_component(Strength)
            strength = strength_comp.value if strength_comp is not None else 1
            health_comp = i.get_component(Health)

            team_comp = i.get_component(Team)
            team = team_comp.value if team_comp is not None else 0

            position = i.get_component(Position).value
            simplified_pos = Vector(round(position.x) // self.simplification_value * self.simplification_value,
                                    round(position.y) // self.simplification_value * self.simplification_value)
            simp_offset = ceil(radius / self.simplification_value)
            simp_offsets = tuple(Vector(x, y) * self.simplification_value for x in range(-simp_offset, simp_offset + 1)
                                 for y in range(-simp_offset, simp_offset + 1))
            for key in map(lambda x: x + simplified_pos, simp_offsets):
                res = colliders.get(key, None)
                if res is None:
                    continue
                for ent, other_position, other_vel, other_strength, other_hp, other_team in res:
                    diff = other_position - position
                    direction = diff.normalized()
                    vel -= direction * (PUSH_MULTIPLIER * other_strength) \
                           + Vector(0.5 - random(), 0.5 - random()) * 0.1
                    other_vel += direction * (PUSH_MULTIPLIER * strength) \
                                 + Vector(0.5 - random(), 0.5 - random()) * 0.1

                    if team != other_team:
                        if health_comp is not None:
                            health_comp.value -= other_strength
                            if health_comp.value <= 0:
                                self.entity_manager.add_component(i.entity, DeadTag())

                        if other_hp is not None:
                            other_hp.value -= strength
                            if other_hp.value <= 0:
                                hunger_comp = i.get_component(Hunger)
                                hunger_comp.value += MEAT_FOOD_VALUE
                                health_comp.value += KILL_TREATMENT
                                self.entity_manager.add_component(ent, DeadTag())

            colliders[simplified_pos] = colliders.get(simplified_pos, [])
            colliders[simplified_pos].append((i.entity, position, vel, strength, health_comp, team))

        for arr in colliders.values():
            for pos, vel in map(lambda x: (x[1], x[2]), arr):
                pos += vel
                vel *= 1 - DAMPENING
                if vel.sqr_len() < 0.1:
                    vel *= 0


class EvolveSystem(BaseSystem):

    def __init__(self):
        self.filter = None

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

    def __init__(self):
        self.__locked_entity = None
        self.filter = None
        self.__render_system = None
        self.__render_surface = None
        self.__font = None

    def on_create(self) -> None:
        from core.application import Application
        self.filter = self.entity_manager.create_filter(required=(Position,),
                                                        additional=(MoveSpeed, Hunger, Strength, Health))
        self.__render_system = World.current_world.get_or_create_system(RenderSystem)
        self.__font = pygame.font.Font(None, 30)
        self.__render_surface = Application.get_render_surface()
        self.__locked_entity = None

    def on_update(self, delta_time: float) -> None:
        mouse_pos = Mouse.get_position()
        if Mouse.is_mouse_down():
            self.__locked_entity = None
        for i in self.query(self.filter):
            entity_pos = i.get_component(Position).value + self.__render_system.camera_position
            if (entity_pos - mouse_pos).sqr_len() <= 65 or self.__locked_entity is not None:
                if Mouse.is_mouse_down():
                    self.__locked_entity = i.entity
                if self.__locked_entity is not None and i.entity != self.__locked_entity:
                    continue
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


class DrawWorldBordersSystem(BaseSystem):
    __update_order__ = 150

    def __init__(self):
        from simulation.utils import create_circle
        from core.application import Application
        self.__sprite = create_circle(round(WORLD_SIZE + 5), (0, 0, 0), (200, 10, 10), 10)
        self.__sprite.image.set_colorkey((0, 0, 0))
        self.__group = pygame.sprite.GroupSingle()
        self.__group.add(self.__sprite)

        self.__render_surface = Application.get_render_surface()
        self.__render_system = World.current_world.get_or_create_system(RenderSystem)

    def on_update(self, delta_time: float) -> None:
        self.__sprite.rect.center = self.__render_system.camera_position.to_tuple()
        self.__group.draw(self.__render_surface)


class KillSystem(BaseSystem):
    __update_order__ = 200

    def __init__(self):
        self.filter = None

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(DeadTag,))

    def on_update(self, delta_time: float) -> None:
        to_kill = set()
        for i in self.query(self.filter):
            to_kill.add(i.entity)
        self.entity_manager.add_command(self.__kill, to_kill)

    def __kill(self, entities) -> None:
        try:
            for entity in entities:
                self.entity_manager.kill_entity(entity)
        except EntityNotFoundError:
            pass


class BotCreationSystem(BaseSystem):

    def __init__(self):
        self.time = 0

    def on_update(self, delta_time: float) -> None:
        self.time += delta_time
        if self.time >= BOT_CREATE_DELAY:
            self.entity_manager.add_command(self.__create_command)
            self.time = 0

    def __create_command(self) -> None:
        entity = self.entity_manager.create_entity()
        create_named_creature(self.entity_manager, entity,
                              "Bot" + str(entity.get_id()), randint(0, len(TEAM_COLORS) - 1))
