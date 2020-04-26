from entities import *

manager = EntityManager()
entity = manager.create_entity()


class TestComponent(BaseComponent):
    __slots__ = ("a",)


comp = TestComponent()
comp.a = 2
manager.add_component(entity, comp)
for i in manager.get_entities().filter(TestComponent):
    c = i.get_component(TestComponent)
    c.a = 3
    print(c.a)
print(comp.a)