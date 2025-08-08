from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Purchase:
    name: str
    quantity: int
    unit_cost: Decimal
    purchase_date: date


@dataclass(frozen=True)
class CompanyAggregate:
    name: str
    total_nominal_invested: Decimal
    total_real_invested: Decimal
    total_current_value: Decimal
    total_nominal_profit: Decimal
    total_real_profit: Decimal


@dataclass(frozen=True)
class PortfolioTotals:
    total_nominal_invested: Decimal
    total_real_invested: Decimal
    total_current_value: Decimal
    total_nominal_profit: Decimal
    total_real_profit: Decimal


