import re
import requests
from bs4 import BeautifulSoup
from decimal import Decimal, InvalidOperation
from typing import Dict, Iterable
from core.dto import ShareAndMarket, ShareWithPrice

URL = "https://www.google.com/finance/quote/"

def get_price(symbol: str, market: str) -> Decimal:
    url = f"{URL}{symbol}:{market}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.text, "html.parser")
    price = soup.find_all("div", class_="YMlKec fxKbKc")
    if not price or len(price) == 0:
        raise ValueError(f"No price found for {symbol} on {market}")
    raw_text = price[0].get_text(strip=True)
    # Remove currency symbols, commas, and any non-numeric characters except sign and decimal point
    cleaned = re.sub(r"[^0-9+\-.]", "", raw_text)
    if cleaned == "" or cleaned in {"+", "-", ".", "+.", "-."}:
        raise ValueError(f"Invalid price text: '{raw_text}' for {symbol} on {market}")
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(
            f"Could not parse price '{raw_text}' (cleaned '{cleaned}') for {symbol} on {market}"
        ) from exc

def get_prices(shares_and_markets: Iterable[ShareAndMarket]) -> Iterable[ShareWithPrice]:
    for share_and_market in shares_and_markets:
        yield ShareWithPrice(
            symbol=share_and_market["symbol"],
            price=get_price(share_and_market["symbol"], share_and_market["market"]),
        )