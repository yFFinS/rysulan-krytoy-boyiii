import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

SqlAlchemyBase = dec.declarative_base()


class Factory:
    __slots__ = ()
    __factory = None
    __session = None

    @staticmethod
    def init(connection_string: str):
        if Factory.__factory is not None:
            return
        engine = sa.create_engine(connection_string, echo=False)
        Factory.__factory = orm.sessionmaker(bind=engine)
        import sql.data
        SqlAlchemyBase.metadata.create_all(engine)

    @staticmethod
    def get_or_create_session() -> Session:
        if Factory.__session is None:
            Factory.__session = Factory.__factory()

        return Factory.__session


def init(db_file: str) -> None:
    if not db_file or not db_file.strip():
        raise Exception("Необходимо указать файл базы данных.")

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    Factory.init(conn_str)


if __name__ == "__main__":
    init("entities.sqlite")
