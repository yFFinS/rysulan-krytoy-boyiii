from ecs.systems import BaseSystem
from simulation.components import *


class RenderSystem(BaseSystem):

    def __init__(self):
        from pygame import sprite
        self.__sprites = sprite.Group()
        self.render_surface = None

    def on_create(self):
        from application import Application
        self.render_surface = Application.get_render_surface()
        for i in self.entity_manager.get_entities().filter(RenderSprite):
            render_comp = i.get_component(RenderSprite)
            self.__sprites.add(render_comp.sprite)

    def on_update(self, delta_time: float):
        for i in self.entity_manager.get_entities().filter(RenderSprite, Position):
            render_comp = i.get_component(RenderSprite)
            if not render_comp.sprite.groups():
                self.__sprites.add(render_comp.sprite)
            position_comp = i.get_component(Position)
            render_comp.sprite.rect.center = position_comp.value.to_tuple()
        self.__sprites.draw(self.render_surface)