from src.core.application import Application
import src.sql.data as db_session
import src.vk_bot.client
import src.sql.core

# Если 1, то бот будет всем участникам сообщества писать при включении и отключении.
BROADCAST_MESSAGES = 0

if __name__ == "__main__":

    # Инициализация приложения.
    app = Application()

    # Инициализация vk бота. С этого момента он отвечает на команды.
    src.vk_bot.client.init()

    # Файл базы данных. Можно указать другое имя файла для другой симуляции.
    src.sql.core.init("entities.sqlite")

    # Загрузка из базы данных.
    db_session.create_entities_from_database()

    # Главный цикл.
    # Должен запускаться после всех инициализаций.
    # profile=True - будет подсчитано время работы некоторых функций в папку profiling.
    # clear_log=False - при True все предыдушие файлы в папке profiling будут удалены.
    app.run(profile=True, clear_log=False)

    # Сохранение всех существ в базу данных.
    db_session.save_to_database()
    db_session.close()

    # Остановка всех потоков.
    Application.terminate()
