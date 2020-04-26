class World:
    __current_id = 0

    def __init__(self):
        self.__id = World.__current_id
        World.__current_id += 1

        self.__systems = set()
        self.__entity_manager = None

    def get_id(self) -> int:
        return self.__id
    