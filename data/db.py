import os
from peewee import Model, SqliteDatabase


DB_PATH = os.getenv("DB_PATH", os.path.join(os.getcwd(), "financial_report.db"))


db = SqliteDatabase(
    DB_PATH,
    pragmas={
        "journal_mode": "wal",
        "foreign_keys": 1,
        "cache_size": -64 * 1024,
        "synchronous": 0,
    },
    timeout=5.0,
)


class BaseModel(Model):
    class Meta:
        database = db


