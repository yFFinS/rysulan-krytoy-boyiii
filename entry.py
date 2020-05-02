from application import Application
from simulation.systems import *
from ecs.world import World
from simulation.systems import *
from simulation.utils import create_rect
import vk_bot.client


app = Application()

vk_bot.client.init()

app.run(True, True)