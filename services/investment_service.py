from __future__ import annotations
from typing import Iterable, List, Tuple

from core.analysis import analyze
from core.models import CompanyAggregate, PortfolioTotals
from core.ports import CpiDataProvider
from infra.google_finance_price_provider import get_prices

from core.dto import PurchaseRow, ShareAndMarket


def run_investment_analysis(
    purchase_rows: Iterable[PurchaseRow],
    initial_year: str,
    cpi_data_provider: CpiDataProvider,
) -> Tuple[List[CompanyAggregate], PortfolioTotals]:
    cpi_index = cpi_data_provider.get_cpi_from_initial_date(initial_year)

    unique_pairs: set[tuple[str, str]] = set()
    for purchase in purchase_rows:
        market = purchase["market"]
        if market:
            unique_pairs.add((purchase["symbol"], market))
        else:
            print(f"No market found for {purchase['symbol']}. Skipping. Please add a market to the share purchase.")

    shares_and_markets: list[ShareAndMarket] = [
        {"symbol": symbol, "market": market} for (symbol, market) in unique_pairs
    ]

    current_prices = {p["symbol"]: p["price"] for p in get_prices(shares_and_markets)}
    return analyze(purchase_rows, cpi_index, current_prices)


