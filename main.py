from src.core.application import Application
import src.sql.data as db_session
import src.vk_bot.client
import src.sql.core

# Set to False if you don't want vk bot to broadcast messages
BROADCAST_MESSAGES = False

if __name__ == "__main__":
    app = Application()

    src.vk_bot.client.init()

    src.sql.core.init("entities.sqlite")
    db_session.create_entities_from_database()

    app.run(True, True)

    db_session.save_to_database()
    db_session.close()

    Application.terminate()
