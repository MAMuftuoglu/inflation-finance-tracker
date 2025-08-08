from __future__ import annotations
from datetime import date
from decimal import Decimal
from typing import Dict, Iterable, List, Tuple

from core.analysis import analyze
from core.models import Purchase, CompanyAggregate, PortfolioTotals
from core.ports import PriceProvider


def build_cpi_index(cpi_rows: Iterable[Dict]) -> Dict[str, Decimal]:
    # cpi_rows like: {"month": "YYYY-MM", "cpi": float}
    index: Dict[str, Decimal] = {}
    for r in cpi_rows:
        index[r["month"]] = Decimal(str(r["cpi"]))
    # ensure chronological order for latest lookup; dict preserves insertion
    return dict(sorted(index.items()))


def map_purchases(rows: Iterable[Dict]) -> List[Purchase]:
    purchases: List[Purchase] = []
    for r in rows:
        purchases.append(
            Purchase(
                name=r.get("symbol") or r["name"],
                quantity=int(r["quantity"]),
                unit_cost=Decimal(str(r["cost"])),
                purchase_date=date.fromisoformat(r["purchase_date"]),
            )
        )
    return purchases


def run_investment_analysis(
    purchase_rows: Iterable[Dict],
    cpi_rows: Iterable[Dict[str, float]],
    price_provider: PriceProvider,
) -> Tuple[List[CompanyAggregate], PortfolioTotals]:
    purchases = map_purchases(purchase_rows)
    cpi_index = build_cpi_index(cpi_rows)
    symbols = {p.name for p in purchases}
    current_prices = price_provider.get_prices(symbols)
    return analyze(purchases, cpi_index, current_prices)


