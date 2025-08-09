from peewee import (
    DateField,
    DecimalField,
    IntegerField,
    TextField,
)

from data.db import BaseModel, db


class SharePurchase(BaseModel):
    symbol = TextField(index=True)
    quantity = IntegerField()
    cost = DecimalField(max_digits=18, decimal_places=6, auto_round=True)
    purchase_date = DateField(index=True)
class ShareMarketMap(BaseModel):
    symbol = TextField(unique=True, index=True)
    market = TextField()

def init_db():
    db.connect(reuse_if_open=True)
    db.create_tables([SharePurchase, ShareMarketMap])


