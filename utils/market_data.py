# utils/market_data.py
"""
Fetches live commodity prices from Yahoo Finance's JSON API.
Symbols:
  BZ=F  — Brent Crude
  CL=F  — WTI Crude
  NG=F  — US Natural Gas
"""

import requests
import streamlit as st

_SYMBOLS = {
    "brent": "BZ=F",
    "wti": "CL=F",
    "natgas": "NG=F",
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def _fetch_price(symbol: str) -> tuple[float | None, float | None]:
    """Return (current_price, pct_change) or (None, None) on error."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
    try:
        r = requests.get(url, headers=_HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        meta = data["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice")
        prev = meta.get("chartPreviousClose") or meta.get("previousClose")
        if price and prev and prev != 0:
            chg = ((price - prev) / prev) * 100
        else:
            chg = None
        return price, chg
    except Exception:
        return None, None


@st.cache_data(ttl=21_600)  # 6-hour cache
def get_market_prices() -> dict:
    """Return dict with brent, wti, natgas prices and their % changes."""
    result = {}
    for key, symbol in _SYMBOLS.items():
        price, chg = _fetch_price(symbol)
        result[key] = price
        result[f"{key}_chg"] = chg
    return result
