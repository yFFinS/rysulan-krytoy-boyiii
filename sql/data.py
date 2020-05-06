from ecs.world import World
import simulation.__all_components
from ecs.component import BaseComponent
from sql.core import Factory


def create_entities_from_database() -> None:
    world = World.default_world
    manager = world.get_manager()
    entities = []
    session = Factory.get_or_create_session()
    for component_type in BaseComponent.__subclasses__():
        for component in session.query(component_type):
            while len(entities) <= component.sql_entity_id:
                entities.append(manager.create_entity())
            entity = entities[component.sql_entity_id]
            component.from_database(manager)
            manager.add_component(entity, component)


def save_to_database() -> None:
    world = World.default_world
    manager = world.get_manager()
    comp_types = BaseComponent.__subclasses__()
    session = Factory.get_or_create_session()
    comp_filter = manager.create_filter(required=(), additional=comp_types)
    for i in manager.get_entities().filter(comp_filter):
        entity = i.entity
        for component in i.components:
            component.to_database()
            component.sql_entity_id = entity.get_id()
            try:
                session.add(component)
            except:
                session.rollback()
                print(component, "can't be added to db.")
    session.commit()
    session.close()
