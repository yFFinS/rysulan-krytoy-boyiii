from application import Application
from simulation.systems import *
from ecs.world import World
from simulation.systems import *
from simulation.utils import create_rect
import vk_bot.client


app = Application()
world = World.default_world
manager = world.get_manager()
for x in range(0, 100):
    for y in range(0, 100):
        entity = manager.create_entity()
        sprite_comp = RenderSprite()
        sprite_comp.sprite = create_rect(20, 20, (100, 50, 40), (100, 20, 0), 5)
        pos_comp = Position()
        pos_comp.value = Vector(x * 20, y * 20)
        manager.add_component(entity, sprite_comp)
        manager.add_component(entity, pos_comp)

vk_bot.client.init()

app.run(True, True)