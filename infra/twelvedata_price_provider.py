from __future__ import annotations
from decimal import Decimal
import time
from typing import Dict, Iterable, Optional

from core.ports import PriceProvider
from infra.tw_client import get_td_client


class TwelveDataPriceProvider(PriceProvider):
    """Fetch current prices using TwelveData in batch via the quote endpoint.

    Input keys are symbols; no name mapping required.
    """

    def __init__(self, max_symbols_per_minute: int = 8, throttle: bool = True) -> None:
        self.max_symbols_per_minute = max_symbols_per_minute
        self.throttle = throttle

    def get_prices(self, names: Iterable[str]) -> Dict[str, Decimal]:
        # Treat the iterable as symbols directly
        unique_symbols = list(dict.fromkeys(names))  # preserve order, dedupe

        if not unique_symbols:
            return {}

        # Chunk symbols to respect an 8-symbols-per-minute policy (configurable)
        chunk_size = max(1, int(self.max_symbols_per_minute))
        symbol_chunks = [
            unique_symbols[i : i + chunk_size] for i in range(0, len(unique_symbols), chunk_size)
        ]

        td = get_td_client()
        all_data = []
        for idx, chunk in enumerate(symbol_chunks):
            symbol_csv = ",".join(chunk)
            endpoint = td.price(symbol=symbol_csv)
            data = endpoint.as_json()
            all_data.append((chunk, data))
            # If more chunks remain and throttling is enabled, sleep ~60s per minute window
            if self.throttle and idx < len(symbol_chunks) - 1:
                time.sleep(60)

        # Normalize response into symbol -> price (Decimal)
        symbol_to_price: Dict[str, Decimal] = {}

        def coerce_decimal(value: object) -> Optional[Decimal]:
            try:
                return Decimal(str(value))
            except Exception:
                return None

        for _, data in all_data:
            if isinstance(data, dict) and "price" in data and "symbol" in data:
                # Single symbol case
                price = coerce_decimal(data.get("price"))
                sym = data.get("symbol")
                if price is not None and isinstance(sym, str):
                    symbol_to_price[sym] = price
            elif isinstance(data, dict):
                # Batch: expect mapping symbol -> { ... 'price': x, 'symbol': sym }
                for key, payload in data.items():
                    if isinstance(payload, dict):
                        sym = payload.get("symbol") or key
                        price = coerce_decimal(payload.get("price"))
                        if isinstance(sym, str) and price is not None:
                            symbol_to_price[sym] = price
            elif isinstance(data, list):
                # Some endpoints may return a list of quote dicts
                for payload in data:
                    if isinstance(payload, dict):
                        sym = payload.get("symbol")
                        price = coerce_decimal(payload.get("price"))
                        if isinstance(sym, str) and price is not None:
                            symbol_to_price[sym] = price

        # Return mapping symbol -> price
        result: Dict[str, Decimal] = {}
        for sym in unique_symbols:
            price = symbol_to_price.get(sym)
            if price is not None:
                result[sym] = price
        return result


