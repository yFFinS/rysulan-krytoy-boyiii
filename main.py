from core.application import Application
import sql.data as db_session
import vk_bot.client
import sql.core

# Set to False if you don't want vk bot to broadcast messages
BROADCAST_MESSAGES = False

if __name__ == "__main__":
    app = Application()

    vk_bot.client.init()

    sql.core.init("sql/entities.sqlite")
    db_session.create_entities_from_database()

    app.run(True, True)

    db_session.save_to_database()
    db_session.close()

    Application.terminate()
