from __future__ import annotations
from typing import TypedDict, Literal
from decimal import Decimal


class PurchaseRow(TypedDict):
    symbol: str
    market: str | None
    quantity: Decimal
    cost: Decimal
    purchase_date: str  # YYYY-MM-DD

class ShareAndMarket(TypedDict):
    symbol: str
    market: str

class ShareWithPrice(TypedDict):
    symbol: str
    price: Decimal


class AddPurchaseResult(TypedDict):
    success: bool
    purchase_id: int | None
    symbol: str
    market: str
    quantity: Decimal
    cost: Decimal
    purchase_date: str
    market_action: Literal["created", "updated", "unchanged"]
    error: str | None
