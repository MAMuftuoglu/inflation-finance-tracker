from __future__ import annotations
from typing import Dict, Iterable, Protocol
from decimal import Decimal


class PriceProvider(Protocol):
    def get_prices(self, names: Iterable[str]) -> Dict[str, Decimal]:
        """Return mapping of symbol/name -> current price as Decimals."""
        ...

class CpiDataProvider(Protocol):
    def get_cpi_from_initial_date(self, initial_year: str) -> Dict[str, Decimal]:
        """Return mapping of YYYY-MM -> CPI on that date as Decimals."""
        ...
