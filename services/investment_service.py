from __future__ import annotations
from datetime import date
from decimal import Decimal
from typing import Dict, Iterable, List, Tuple

from core.analysis import analyze
from core.models import Purchase, CompanyAggregate, PortfolioTotals
from core.ports import PriceProvider, CpiDataProvider

from core.dto import PurchaseRow


def map_purchases(rows: Iterable[PurchaseRow]) -> List[Purchase]:
    purchases: List[Purchase] = []
    for r in rows:
        purchases.append(
            Purchase(
                name=r["symbol"],
                quantity=int(r["quantity"]),
                unit_cost=Decimal(str(r["cost"])),
                purchase_date=date.fromisoformat(r["purchase_date"]),
            )
        )
    return purchases


def run_investment_analysis(
    purchase_rows: Iterable[PurchaseRow],
    initial_year: str,
    price_provider: PriceProvider,
    cpi_data_provider: CpiDataProvider,
) -> Tuple[List[CompanyAggregate], PortfolioTotals]:
    purchases = map_purchases(purchase_rows)
    cpi_index = cpi_data_provider.get_cpi_from_initial_date(initial_year)
    symbols = {p.name for p in purchases}
    current_prices = price_provider.get_prices(symbols)
    return analyze(purchases, cpi_index, current_prices)


