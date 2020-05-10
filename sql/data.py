from ecs.world import World
import simulation.__all_components
from ecs.component import BaseComponent
from .core import Factory
from .core import SqlAlchemyBase
from .core import sa
from typing import Dict


class EntryDeletionStack:
    __to_delete: list = []

    @staticmethod
    def add(data: SqlAlchemyBase) -> None:
        EntryDeletionStack.__to_delete.append(data)

    @staticmethod
    def delete_all() -> None:
        session = Factory.get_or_create_session()
        for i in EntryDeletionStack.__to_delete:
            try:
                session.delete(i)
            except:
                pass
        EntryDeletionStack.__to_delete.clear()


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
    session = Factory.get_or_create_session()
    EntryDeletionStack.delete_all()

    world = World.default_world
    manager = world.get_manager()
    comp_types = BaseComponent.__subclasses__()
    comp_filter = manager.create_filter(required=(), additional=comp_types)
    for i in manager.get_entities().filter(comp_filter):
        entity = i.entity
        for component in i.components.values():
            component.to_database()
            component.sql_entity_id = entity.get_id()
            try:
                session.add(component)
            except BaseException as e:
                print(f"{component} can't be added to database. Reason: {e}")


def close() -> None:
    session = Factory.get_or_create_session()
    session.commit()
    session.close()