from ecs.systems import BaseSystem
from .__all_components import *
from core.input import Mouse
from ecs.world import World
from simulation.math import Vector
from pygame import sprite
from .utils import create_food
from .settings import *


class RenderSystem(BaseSystem):

    def __init__(self):
        self.__sprites = sprite.Group()
        self.__render_surface = None
        self.camera_position: Vector = Vector(0, 0)
        self.__cached_positions = []

    def on_create(self):
        from core.application import Application
        self.__render_surface = Application.get_render_surface()
        self.filter = self.entity_manager.create_filter(required=(RenderSprite, Position))

    def on_update(self, delta_time: float):
        self.__cached_positions.clear()
        for i in self.query():

            render_comp = i.get_component(RenderSprite)
            if not render_comp.sprite.groups():
                self.__sprites.add(render_comp.sprite)

            position_comp = i.get_component(Position)

            self.__cached_positions.append((render_comp.sprite, position_comp.value.to_tuple()))
            render_comp.sprite.rect.center = (position_comp.value + self.camera_position).to_tuple()

        self.__sprites.draw(self.__render_surface)

        for i in self.__cached_positions:
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
        for i in self.query():
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
        for i in self.query():
            target_pos = i.get_component(TargetPosition).value
            pos_comp = i.get_component(Position)
            if target_pos is not None and (target_pos - pos_comp.value).sqr_len() > 1.5:
                speed = i.get_component(MoveSpeed).value
                pos_comp.value += (target_pos - pos_comp.value).normalized() * (speed * delta_time)


class CreateFood(BaseSystem):

    def __init__(self):
        self.time = 3

    def on_update(self, delta_time: float) -> None:
        self.time += delta_time
        if self.time >= FOOD_CREATE_DELAY:
            self.entity_manager.add_command(create_food, self.entity_manager, self.entity_manager.create_entity())
            self.time = 0

            
class Hungry(BaseSystem):

    def __init__(self):
        self.hunger_time = 0

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Hunger, Priority))

    def on_update(self, delta_time: float) -> None:
        self.hunger_time += delta_time
        if self.hunger_time >= HUNGER_TICK_DELAY:
            for i in self.query():
                hunger_comp = i.get_component(Hunger)
                hunger_comp.value -= 1
                if hunger_comp.value <= EXTREME_HUNGER_DELAY:
                    priority_comp = i.get_component(Priority)
                    priority_comp.value = 'gathering'
            self.hunger_time = 0


class GatheringPriority(BaseSystem):

    def __init__(self):
        self.gathering_time = 1

    def on_create(self) -> None:
        self.filter = self.entity_manager.create_filter(required=(Position, TargetPosition, Hunger))
        self.filter2 = self.entity_manager.create_filter(required=(Position, BushTag))

    def on_update(self, delta_time: float) -> None:
        self.gathering_time += delta_time
        bush_pos = []
        if self.gathering_time >= 1:
            for i in self.entity_manager.get_entities().filter(self.filter2):
                bush_pos_comp = i.get_component(Position)
                bush_pos.append(bush_pos_comp.value)
            if not bush_pos:
                return
            for i in self.query():
                creature_pos_comp = i.get_component(Position)
                creature_target_comp = i.get_component(TargetPosition)
                mini = bush_pos[0]
                for j in bush_pos:
                    if (creature_pos_comp.value - j).sqr_len() < (creature_pos_comp.value - mini).sqr_len():
                        mini = j
                creature_target_comp.value = mini
                if (creature_target_comp.value - creature_pos_comp.value).sqr_len() <= EAT_DISTANCE:
                    hunger_comp = i.get_component(Hunger)
                    hunger_comp.value += BUSH_FOOD_VALUE
                    #Тут надо убить куст
            self.gathering_time = 0
