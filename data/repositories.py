from __future__ import annotations
from typing import List
from decimal import Decimal
from datetime import date

from data.models import SharePurchase, ShareMarketMap
from data.db import db
from core.dto import PurchaseRow, AddPurchaseResult

def get_market_for_symbol(symbol: str) -> str | None:
    record = ShareMarketMap.get_or_none(ShareMarketMap.symbol == symbol)
    return record.market if record else None

def load_share_purchases_as_rows() -> List[PurchaseRow]:
    """Return share purchases as simple dict rows for the service layer.

    Keys: symbol (str), quantity (int), cost (Decimal), purchase_date (YYYY-MM-DD)
    """
    purchases = SharePurchase.select().order_by(SharePurchase.purchase_date.asc())
    rows: List[PurchaseRow] = []
    for p in purchases:
        rows.append(
            {
                "symbol": p.symbol,
                "market": get_market_for_symbol(p.symbol),
                "quantity": p.quantity,
                "cost": p.cost,  # Decimal from DecimalField
                "purchase_date": p.purchase_date.isoformat(),
            }
        )
    return rows

def add_share_purchase(
    symbol: str,
    market: str,
    quantity: Decimal,
    cost: Decimal,
    purchase_date: date,
) -> AddPurchaseResult:
    market_action: str = "unchanged"
    try:
        with db.atomic():
            purchase = SharePurchase.create(
                symbol=symbol, quantity=quantity, cost=cost, purchase_date=purchase_date
            )
            mapping, created = ShareMarketMap.get_or_create(
                symbol=symbol, defaults={"market": market}
            )
            if created:
                market_action = "created"
            elif mapping.market != market:
                mapping.market = market
                mapping.save()
                market_action = "updated"

        return {
            "success": True,
            "purchase_id": purchase.id,
            "symbol": symbol,
            "market": market,
            "quantity": quantity,
            "cost": cost,
            "purchase_date": purchase_date.isoformat(),
            "market_action": market_action,
            "error": None,
        }
    except Exception as exc:
        return {
            "success": False,
            "purchase_id": None,
            "symbol": symbol,
            "market": market,
            "quantity": quantity,
            "cost": cost,
            "purchase_date": purchase_date.isoformat(),
            "market_action": "unchanged",
            "error": str(exc),
        }
