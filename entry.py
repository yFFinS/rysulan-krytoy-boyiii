from ecs.component import *
from ecs.world import *
from application import Application


class TestComponentA(BaseComponent):
    __slots__ = ("a",)


class TestComponentB(BaseComponent):
    __slots__ = ("b",)


class TestSystem(BaseSystem):

    def __init__(self):
        self.__secret_value = 7.5

    def on_update(self, entity_manager: EntityManager, delta_time: float):
        for i in entity_manager.get_entities().filter(TestComponentA, TestComponentB):
            a_comp = i.get_component(TestComponentA)
            b_comp = i.get_component(TestComponentB)
            b_comp.b = b_comp.b + a_comp.a / self.__secret_value


app = Application()
world = World.default_world
world.create_system(TestSystem)
manager = world.get_manager()
entity1 = manager.create_entity()
entity2 = manager.create_entity()
entity3 = manager.create_entity()
manager.add_component(entity1, TestComponentA())
manager.add_component(entity2, TestComponentB())
comp_a = TestComponentA()
comp_a.a = 10
comp_b = TestComponentB()
comp_b.b = 6
manager.add_component(entity3, comp_a)
manager.add_component(entity3, comp_b)

app.run()

print(comp_b.b)