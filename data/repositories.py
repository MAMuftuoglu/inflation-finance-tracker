from __future__ import annotations
from typing import List

from data.models import SharePurchase
from core.dto import PurchaseRow


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
                "quantity": p.quantity,
                "cost": p.cost,  # Decimal from DecimalField
                "purchase_date": p.purchase_date.isoformat(),
            }
        )
    return rows


