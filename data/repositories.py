from __future__ import annotations
from typing import Dict, List

from data.models import SharePurchase


def load_share_purchases_as_rows() -> List[Dict]:
    """Return share purchases as simple dict rows for the service layer.

    Keys: name (str), quantity (int), cost (Decimal), purchase_date (YYYY-MM-DD)
    """
    purchases = SharePurchase.select()
    rows: List[Dict] = []
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


