from src.sql.core import SqlAlchemyBase, sa
from sqlalchemy.ext.declarative import declared_attr


class BaseComponent(SqlAlchemyBase):
    __abstract__ = True
    sql_entity_id = sa.Column(sa.Integer, primary_key=True, index=True, name="entity_id")
    __slots__ = ()

    @declared_attr
    def __tablename__(self) -> str:
        return self.__name__.lower()

    def to_database(self) -> None:
        pass

    def from_database(self, entity_manager) -> None:
        pass

    def on_remove(self) -> None:
        pass
