from ecs.systems import BaseSystem
from simulation.components import *
from input import Mouse
from ecs.world import World


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
        for i in self.entity_manager.get_entities().filter(RenderSprite):
            render_comp = i.get_component(RenderSprite)
            self.__sprites.add(render_comp.sprite)

    def on_update(self, delta_time: float):
        self.__cached_positions.clear()
        for i in self.entity_manager.get_entities().filter(RenderSprite, Position):

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
        if Mouse.is_mouse() and self.__drag_position is not None:
            offset = Mouse.get_position() - self.__drag_position
            self.__render_system.camera_position = self.__prev_camera_position + offset
        elif Mouse.is_mouse_up():
            self.__drag_position = None
            self.__prev_camera_position = self.__render_system.camera_position
