from application import Application
from sql.data import create_entities_from_database, save_to_database
import vk_bot.client
import sql.core
import os


app = Application()

vk_bot.client.init()

sql.core.init("sql/entities.sqlite")
create_entities_from_database()

app.run(True, True)

save_to_database()

os._exit(0)