from entities import *
from world import *


class TestComponentA(BaseComponent):
    __slots__ = ("a",)


class TestComponentB(BaseComponent):
    __slots__ = ("b",)


class TestSystem(BaseSystem):

    def on_create(self):
        print("System created.")

    def on_update(self, entity_manager: EntityManager):
        for i in entity_manager.get_entities().filter(TestComponentA, TestComponentB):
            a_comp = i.get_component(TestComponentA)
            b_comp = i.get_component(TestComponentB)
            b_comp.b = b_comp.b + a_comp.a
        print("System updated.")


world = World()
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

world.update_systems()
print(comp_b.b)