from __future__ import annotations
from functools import lru_cache
from typing import Optional
import os
from twelvedata import TDClient


def _resolve_api_key(explicit_key: Optional[str]) -> str:
    if explicit_key:
        return explicit_key
    key = os.getenv("TWELVE_DATA_KEY") or os.getenv("TD_API_KEY")
    if not key:
        raise RuntimeError(
            "TwelveData API key not found. Set TWELVE_DATA_KEY or TD_API_KEY in the environment/.env."
        )
    return key


@lru_cache(maxsize=1)
def get_td_client(api_key: Optional[str] = None) -> TDClient:
    """Return a cached TwelveData client. Optionally pass `api_key` to override env."""
    key = _resolve_api_key(api_key)
    return TDClient(apikey=key)


