from ecs.systems import BaseSystem
from .__all_components import *
from input import Mouse
from ecs.world import World
from simulation.math import Vector


class RenderSystem(BaseSystem):

    def __init__(self):
        from pygame import sprite
        self.__sprites = sprite.Group()
        self.__render_surface = None
        self.camera_position: Vector = Vector(0, 0)
        self.__cached_positions = []

    def on_create(self):
        from application import Application
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
        if self.__drag_position is not None:
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
