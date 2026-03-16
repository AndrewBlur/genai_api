from pymongo import MongoClient
from app.core.settings import DBSettings

db_settings = DBSettings()

client = MongoClient(db_settings.DB_CONN_STR)

db = client[db_settings.DB_NAME]

