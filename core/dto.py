from __future__ import annotations
from typing import TypedDict
from decimal import Decimal


class PurchaseRow(TypedDict):
    symbol: str
    quantity: int
    cost: Decimal
    purchase_date: str  # YYYY-MM-DD



