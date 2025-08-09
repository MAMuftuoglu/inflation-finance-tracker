from __future__ import annotations
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Dict, Iterable, List, Tuple

from core.models import CompanyAggregate, PortfolioTotals
from core.dto import PurchaseRow


def _month_key(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def calculate_inflation_factor(purchase_date: date, cpi_index: Dict[str, Decimal]) -> Decimal:
    purchase_month = _month_key(purchase_date)
    purchase_cpi = cpi_index.get(purchase_month)
    if purchase_cpi is None:
        return Decimal("1")
    latest_cpi = cpi_index[max(cpi_index.keys())]
    return latest_cpi / purchase_cpi if purchase_cpi != 0 else Decimal("1")


def analyze(
    purchases: Iterable[PurchaseRow],
    cpi_index: Dict[str, Decimal],
    current_prices: Dict[str, Decimal],
) -> Tuple[List[CompanyAggregate], PortfolioTotals]:
    grouped: Dict[str, List[PurchaseRow]] = defaultdict(list)
    for p in purchases:
        grouped[p["symbol"]].append(p)

    results: List[CompanyAggregate] = []

    total_nominal_invested = Decimal("0")
    total_real_invested = Decimal("0")
    total_current_value = Decimal("0")
    total_nominal_profit = Decimal("0")
    total_real_profit = Decimal("0")

    for name, items in grouped.items():
        company_nominal_invested = Decimal("0")
        company_real_invested = Decimal("0")
        company_current_value = Decimal("0")
        company_nominal_profit = Decimal("0")
        company_real_profit = Decimal("0")

        price = current_prices.get(name)
        if price is None:
            price = Decimal("0")

        for purchase in items:
            qty = Decimal(purchase["quantity"])
            batch_cost = qty * purchase["cost"]
            batch_current = qty * price

            inflation_factor = calculate_inflation_factor(date.fromisoformat(purchase["purchase_date"]), cpi_index)
            adjusted_cost = batch_cost * inflation_factor

            company_nominal_invested += batch_cost
            company_real_invested += adjusted_cost
            company_current_value += batch_current
            company_nominal_profit += batch_current - batch_cost
            company_real_profit += batch_current - adjusted_cost

        results.append(
            CompanyAggregate(
                name=name,
                total_nominal_invested=company_nominal_invested,
                total_real_invested=company_real_invested,
                total_current_value=company_current_value,
                total_nominal_profit=company_nominal_profit,
                total_real_profit=company_real_profit,
            )
        )

        total_nominal_invested += company_nominal_invested
        total_real_invested += company_real_invested
        total_current_value += company_current_value
        total_nominal_profit += company_nominal_profit
        total_real_profit += company_real_profit

    totals = PortfolioTotals(
        total_nominal_invested=total_nominal_invested,
        total_real_invested=total_real_invested,
        total_current_value=total_current_value,
        total_nominal_profit=total_nominal_profit,
        total_real_profit=total_real_profit,
    )

    return results, totals


