from __future__ import annotations
from typing import TypedDict
from decimal import Decimal


class PurchaseRow(TypedDict):
    symbol: str
    market: str | None
    quantity: int
    cost: Decimal
    purchase_date: str  # YYYY-MM-DD

class ShareAndMarket(TypedDict):
    symbol: str
    market: str

class ShareWithPrice(TypedDict):
    symbol: str
    price: Decimal
