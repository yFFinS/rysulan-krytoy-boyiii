from math import ceil
from random import random, randint, choice

import pygame

from src.core.input import Mouse
from src.ecs.systems import BaseSystem
from src.ecs.world import World
from .__all_components import *
from .settings import *
from .utils import create_food, create_named_creature, TEAM_COLORS
from src.ecs.entities import EntityNotFoundError


class RenderSystem(BaseSystem):
    __update_order__ = 100

    def __init__(self):
        self.__sprites = pygame.sprite.Group()
        self.__render_surface = None
        from src.core.application import WIDTH, HEIGHT
        self.camera_position: Vector = -Vector(WIDTH / 2, HEIGHT / 2)
        self.filter = None

    def on_create(self):
        from src.core.application import Application
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
            render_comp.sprite.rect.center = (position_comp.value - self.camera_position).to_tuple()

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
            self.__render_system.camera_position = self.__prev_camera_position - offset
        elif Mouse.is_mouse_up():
            self.__drag_position = None
            self.__prev_camera_position = self.__render_system.camera_position


class EntityNameFollowSystem(BaseSystem):
    __update_order__ = 102

    def __init__(self):
        self.__cached_positions = dict()
        self.__name_offset = Vector(0, -18)
        self.filter = None
        self.__sprites = None
        self.__cache = dict()
        self.__font = None
        self.__render_surface = None
        self.__render_system = None

    def on_create(self) -> None:
        from src.core.application import Application
        self.__render_surface = Application.get_render_surface()
        self.__render_system = World.current_world.get_or_create_system(RenderSystem)
        self.__sprites = pygame.sprite.Group()
        self.__font = pygame.font.Font(None, NAME_FONT_SIZE)
        self.filter = self.entity_manager.create_filter(required=(Position, EntityName), additional=(DeadTag,))

    def on_update(self, delta_time: float) -> None:
        for i in self.query(self.filter):
            name = i.get_component(EntityName).value
            if i.get_component(DeadTag) is not None:
                try:
                    self.__cache[name].kill()
                    self.__cache.pop(name)
                except KeyError:
                    pass
                continue
            name_sprite = self.__cache.get(name, None)
            if name_sprite is None:
                try:
                    text = self.__font.render(name, True, NAME_COLOR)
                    name_sprite = sprite.Sprite(self.__sprites)
                    name_sprite.image = text
                    name_sprite.rect = text.get_rect()
                    self.__cache[name] = name_sprite
                except:
                    continue
            pos = i.get_component(Position).value
            name_sprite.rect.center = (pos + self.__name_offset - self.__render_system.camera_position).to_tuple()
        self.__sprites.draw(self.__render_surface)


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
                speed = i.get_component(MoveSpeed).value
                if (target_pos - pos).sqr_len() > speed * 0.5:
                    pos += (target_pos - pos).normalized() * (speed * delta_time)
                else:
                    pos_comp.value = Vector.clone(target_pos)
                    target_pos_comp.value = None


class CreateFood(BaseSystem):

    def __init__(self):
        self.time = 0
        self.filter = None

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(BushTag,))

    def on_update(self, delta_time: float) -> None:
        self.time += delta_time
        if self.time >= FOOD_CREATE_DELAY:
            if len(self.query(self.filter)) <= MAX_FOOD - 4:
                for i in range(4):
                    self.entity_manager.add_command(create_food, self.entity_manager,
                                                    self.entity_manager.create_entity())
            self.time = 0


class HungerSystem(BaseSystem):

    def __init__(self):
        self.hunger_time = 0
        self.filter = None

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Hunger, Health), additional=(MoveSpeed,),
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
                    hp_comp = i.get_component(Health)
                    hp_comp.value *= 0.9
                    hp_comp.value -= 10
                    hunger_comp.value = 0

            self.hunger_time = 0


class GatheringSystem(BaseSystem):

    def __init__(self):
        self.filter = None
        self.filter2 = None
        self.time = 0

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Position, TargetPosition, Hunger),
                                                        additional=(Health, Priority),
                                                        without=(DeadTag,))
        self.filter2 = self.entity_manager.create_filter(required=(Position, BushTag),
                                                         without=(DeadTag,))

    def on_update(self, delta_time: float) -> None:
        self.time += delta_time
        if self.time < 1.2:
            return
        self.time = 0
        bush_pos = []
        for i in self.query(self.filter2):
            bush_pos_comp = i.get_component(Position)
            bush_pos.append((i.entity, bush_pos_comp.value))
        if not bush_pos:
            return
        for i in self.query(self.filter):
            priority = i.get_component(Priority)
            if priority is not None and priority.current != "gathering":
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
            if (creature_target_comp.value - creature_pos_comp.value).sqr_len() <= EAT_DISTANCE * EAT_DISTANCE:
                hunger_comp = i.get_component(Hunger)
                hunger_comp.value += BUSH_FOOD_VALUE
                if hp_comp is not None:
                    hp_comp.value += BUSH_HP_VALUE
                self.entity_manager.add_component(closest_bush[0], DeadTag("съедения"))


class HuntingSystem(BaseSystem):

    def __init__(self):
        self.filter = None
        self.time = 0

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Position, TargetPosition,
                                                                  Strength, Health, Team),
                                                        additional=(Priority,),
                                                        without=(DeadTag,))

    def on_update(self, delta_time: float) -> None:
        self.time += delta_time
        if self.time < 1.5:
            return
        self.time = 0
        creatures = tuple(self.query(self.filter))
        for i in creatures:
            priority_comp = i.get_component(Priority)
            if priority_comp is not None and priority_comp.current != 'hunting':
                continue
            hp_comp = i.get_component(Health)

            team = i.get_component(Team).value
            pos_comp = i.get_component(Position)
            target_comp = i.get_component(TargetPosition)
            strength = i.get_component(Strength).value

            closest_pos = creatures[0].get_component(Position).value

            for j in creatures:
                if j == i or team == j.get_component(Team).value:
                    continue
                pos = j.get_component(Position).value

                if (pos_comp.value - pos).sqr_len() < (pos_comp.value - closest_pos).sqr_len() \
                        and j.get_component(Health).value / strength * strength * DAMAGE_MULTIPLIER \
                        >= hp_comp.value / j.get_component(Strength).value * DAMAGE_MULTIPLIER:
                    closest_pos = pos
            target_comp.value = closest_pos


class PriorityControlSystem(BaseSystem):

    def __init__(self):
        self.filter = None

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Priority, Hunger, Health, MoveSpeed),
                                                        without=(DeadTag,))

    def on_update(self, delta_time: float) -> None:
        for i in self.query(self.filter):
            hunger = i.get_component(Hunger).value
            hp = i.get_component(Health).value
            priority_comp = i.get_component(Priority)
            speed_comp = i.get_component(MoveSpeed)
            if priority_comp.target == "hunting":
                if priority_comp.current == "hunting":
                    speed_comp.value += delta_time * 0.02
                else:
                    speed_comp.value = max(1.5, speed_comp.value - delta_time * 0.002)

            if hunger < EXTREME_HUNGER_VALUE:
                priority_comp.current = "gathering"
            elif hp < EXTREME_HP_VALUE:
                priority_comp.current = "safety"
            else:
                if priority_comp.target == "hunting" and priority_comp.current != "hunting" and \
                        hunger < EVOLVE_HUNGER_VALUE - EVOLVE_HUNGER_COST:
                    priority_comp.current = "gathering"
                else:
                    priority_comp.current = priority_comp.target


class PositionLimitSystem(BaseSystem):
    __update_order__ = 100

    def __init__(self):
        self.filter = None

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Position,))

    def on_update(self, delta_time: float) -> None:
        for i in self.query(self.filter):
            pos_comp = i.get_component(Position)
            pos_comp.value = pos_comp.value.normalized() * min(pos_comp.value.len(), WORLD_SIZE)


class CollisionSystem(BaseSystem):
    __update_order__ = -5

    def __init__(self):
        self.filter = None
        self.simplification_value = 10
        self.simp_offset = ceil(START_CREATURE_SIZE / self.simplification_value)
        self.simp_offsets = tuple(Vector(x, y) * self.simplification_value
                                  for x in range(-self.simp_offset, self.simp_offset + 1)
                                  for y in range(-self.simp_offset, self.simp_offset + 1))

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Position, Rigidbody),
                                                        additional=(Strength,))

    def on_update(self, delta_time: float) -> None:
        colliders = dict()
        creatures = []
        for i in self.query(self.filter):
            rigidbody_comp = i.get_component(Rigidbody)
            vel = rigidbody_comp.velocity
            strength_comp = i.get_component(Strength)
            strength = strength_comp.value if strength_comp is not None else 0

            position = i.get_component(Position).value
            simplified_pos = Vector(round(position.x) // self.simplification_value * self.simplification_value,
                                    round(position.y) // self.simplification_value * self.simplification_value)
            colliders[simplified_pos] = colliders.get(simplified_pos, [])
            colliders[simplified_pos].append((i.entity, position, vel, strength))
            creatures.append(i)

        for i in creatures:
            rigidbody_comp = i.get_component(Rigidbody)
            radius = rigidbody_comp.radius
            vel = rigidbody_comp.velocity

            position = i.get_component(Position).value
            for key in map(lambda x: x + simplified_pos, self.simp_offsets):
                res = colliders.get(key, None)
                if res is None:
                    continue
                for ent, other_position, other_vel, other_strength in res:
                    if ent == i.entity:
                        continue
                    diff = other_position - position
                    if diff.sqr_len() > 4 * radius * radius:
                        continue
                    vel -= diff.normalized() * (PUSH_MULTIPLIER * other_strength)

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
        from src.core.application import Application
        self.filter = self.entity_manager.create_filter(required=(Position,),
                                                        additional=(MoveSpeed, Hunger, Strength, Health, Priority))
        self.__render_system = World.current_world.get_or_create_system(RenderSystem)
        self.__font = pygame.font.Font(None, 30)
        self.__render_surface = Application.get_render_surface()
        self.__locked_entity = None

    def on_update(self, delta_time: float) -> None:
        mouse_pos = Mouse.get_position()
        if Mouse.is_mouse_down():
            self.__locked_entity = None
        for i in self.query(self.filter):
            pos = i.get_component(Position).value
            entity_pos = pos - self.__render_system.camera_position
            if (entity_pos - mouse_pos).sqr_len() <= 65 or self.__locked_entity is not None:
                if Mouse.is_mouse_down():
                    self.__locked_entity = i.entity
                if self.__locked_entity is not None and i.entity != self.__locked_entity:
                    continue
                text = []
                comp = i.get_component(MoveSpeed)
                text.append(f"Entity id: {i.entity.get_id()}")
                rx, ry = "%.1f" % pos.x, "%.1f" % pos.y
                text.append(f"Position: ({rx}, {ry})")
                if comp is not None:
                    text.append(f"Speed: {'%.2f' % comp.value}")
                comp = i.get_component(Priority)
                if comp is not None:
                    text.append(f"Priority: {comp.current}")
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
    __update_order__ = 101

    def __init__(self):
        from src.simulation.utils import create_circle
        from src.core.application import Application
        self.__sprite = create_circle(round(WORLD_SIZE + 5), (0, 0, 0), (200, 10, 10), 10)
        self.__sprite.image.set_colorkey((0, 0, 0))
        self.__group = pygame.sprite.GroupSingle()
        self.__group.add(self.__sprite)

        self.__render_surface = Application.get_render_surface()
        self.__render_system = World.current_world.get_or_create_system(RenderSystem)

    def on_update(self, delta_time: float) -> None:
        self.__sprite.rect.center = (-self.__render_system.camera_position).to_tuple()
        self.__group.draw(self.__render_surface)


class DamageSystem(BaseSystem):

    def __init__(self):
        self.filter = None
        self.time = 0

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Health, Strength, Team, Position, Hunger))

    def on_update(self, delta_time: float) -> None:
        self.time += delta_time
        if self.time < 0.5:
            return
        self.time = 0
        creatures = []
        for i in self.query(self.filter):
            hp_comp = i.get_component(Health)
            if hp_comp.value <= -10000:
                res = choice(("укуса", "захвата", "царапины", "удара об тумбочку", "солнечного удара"))
                self.entity_manager.add_component(i.entity, DeadTag(res))
            elif hp_comp.value <= 0:
                self.entity_manager.add_component(i.entity, DeadTag("голода"))
            else:
                strength = i.get_component(Strength).value
                team = i.get_component(Team).value
                pos = i.get_component(Position).value
                creatures.append((i.entity, pos, hp_comp, strength, team, i.get_component(Hunger)))

        atck_dist_sqr = ATTACK_DISTANCE * ATTACK_DISTANCE
        for ent, pos, hp_comp, strength, team, hunger in creatures:
            for ent2, pos2, hp_comp2, strength2, team2, hunger2 in creatures:
                if ent == ent2:
                    continue
                if team2 != team and (pos - pos2).sqr_len() <= atck_dist_sqr:
                    p_comp = self.entity_manager.get_component(ent, Priority)
                    mult = 1 if p_comp is None or p_comp.current != "hunting" else strength
                    hp_comp2.value -= strength * DAMAGE_MULTIPLIER * mult
                    if hp_comp2.value <= 0:
                        hp_comp2.value -= 10000
                        hp_comp.value += KILL_TREATMENT
                        hunger.value += MEAT_FOOD_VALUE


class KillSystem(BaseSystem):
    __update_order__ = 200

    def __init__(self):
        self.__methods = None
        self.filter = None

    def on_create(self) -> None:
        from src.vk_bot.commands import BotMethods
        self.__methods = BotMethods
        self.filter = self.entity_manager.create_filter(required=(DeadTag,), additional=(UserId, EntityName))

    def on_update(self, delta_time: float) -> None:
        to_kill = set()
        for i in self.query(self.filter):
            to_kill.add(i)

        self.entity_manager.add_command(self.__kill, to_kill)

    def __kill(self, entities) -> None:
        for i in entities:
            id_comp = i.get_component(UserId)
            if id_comp is not None:
                name = i.get_component(EntityName).value
                message = str(name) + " умер"
                res = i.get_component(DeadTag).reason
                if not res:
                    message += ". Жаль!!"
                else:
                    message += " от " + res + ". Ну че поделать."
                self.__methods.send_message(id_comp.peer_id, message)
                if id_comp.peer_id != id_comp.value:
                    self.__methods.send_message(id_comp.value, message)
            try:
                self.entity_manager.kill_entity(i.entity)
            except EntityNotFoundError:
                continue


class LifeTimeSystem(BaseSystem):

    def __init__(self):
        self.filter = None

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(LifeTime,), without=(DeadTag,))

    def on_update(self, delta_time: float) -> None:
        for i in self.query(self.filter):
            comp = i.get_component(LifeTime)
            comp.value += delta_time
            if random() <= comp.value / 4000:
                self.entity_manager.add_component(i.entity, DeadTag("тяжёлой жизни"))


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


class SaveSystem(BaseSystem):

    def __init__(self):
        from src.sql.data import save_to_database
        self.time = 0
        self.backup_func = save_to_database

    def on_update(self, delta_time: float) -> None:
        self.time += delta_time
        if self.time >= SAVE_DELAY:
            self.backup_func()
            self.time = 0


class RunAwaySystem(BaseSystem):
    __update_order__ = 50

    def __init__(self):
        self.filter = None
        self.filter2 = None

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Priority, Position, TargetPosition, Team))
        self.filter2 = self.entity_manager.create_filter(required=(Position, Team))

    def on_update(self, delta_time: float) -> None:
        team_clusters = {team: [0, Vector(0, 0)] for team in range(len(TEAM_COLORS))}
        creatures = self.query(self.filter)
        for i in self.query(self.filter2):
            team = i.get_component(Team).value
            team_clusters[team][0] += 1
            team_clusters[team][1] += i.get_component(Position).value
        average_spots = {team: val[1] / val[0] for team, val in team_clusters.items() if val[0] != 0}
        for i in creatures:
            if i.get_component(Priority).current != "safety":
                continue
            team = i.get_component(Team).value
            avg_target_pos = average_spots[team]

            i.get_component(TargetPosition).value = avg_target_pos * 4


class ReproduceSystem(BaseSystem):

    def __init__(self):
        self.filter = None
        self.time = 0

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Team, MoveSpeed, Strength, Health, Position))

    def on_update(self, delta_time: float) -> None:
        self.time += delta_time
        if self.time >= REPRODUCE_DELAY:
            count = 0
            for i in self.query(self.filter):
                count += 1
                if random() > REPRODUCE_CHANCE:
                    continue
                if count >= MAX_CREATURES:
                    break
                count += 1
                entity = self.entity_manager.create_entity()
                create_named_creature(self.entity_manager, entity, "Bot" + str(entity.get_id()),
                                      i.get_component(Team).value)
                speed_comp = self.entity_manager.get_component(entity, MoveSpeed)
                speed_comp.value = max(1.5, i.get_component(MoveSpeed).value * (0.5 - random()) * 5)
                str_comp = self.entity_manager.get_component(entity, Strength)
                str_comp.value = max(1, i.get_component(Strength).value * (0.5 - random()) * 4)
                hp_comp = self.entity_manager.get_component(entity, Health)
                hp_comp.value = max(200, i.get_component(Health).value * (0.5 - random()) * 13)
                pos_comp = self.entity_manager.get_component(entity, Position)
                pos_comp.value = Vector.clone(i.get_component(Position).value)
            self.time = 0
