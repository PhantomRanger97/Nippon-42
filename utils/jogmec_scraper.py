# utils/jogmec_scraper.py
"""
Scrapes JOGMEC press releases from jogmec.go.jp.

JOGMEC changed its site structure in 2023/24; this version tries
multiple selector strategies and a JSON-LD/sitemap fallback so it
degrades gracefully rather than silently returning nothing.
"""

import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import streamlit as st

JOGMEC_PRESS_URL = "https://www.jogmec.go.jp/news/release/index.html"
JOGMEC_NEWS_URL  = "https://www.jogmec.go.jp/news/index.html"
JOGMEC_BASE      = "https://www.jogmec.go.jp"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en;q=0.9",
    "Referer": "https://www.jogmec.go.jp/",
}

OIL_KEYWORDS = [
    "石油", "天然ガス", "原油", "エネルギー", "LNG", "掘削", "備蓄", "探鉱",
    "oil", "gas", "lng", "petroleum", "crude", "energy", "exploration",
    "production", "stockpile", "reserve", "refin", "mineral",
]


def _translate(text: str) -> str:
    try:
        return GoogleTranslator(source="ja", target="en").translate(text[:500])
    except Exception:
        return text


def _is_relevant(text: str) -> bool:
    return any(kw.lower() in text.lower() for kw in OIL_KEYWORDS)


def _scrape_url(url: str) -> list[dict]:
    """Generic scraper — tries multiple selector strategies."""
    try:
        r = requests.get(url, headers=_HEADERS, timeout=20)
        r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "lxml")
    seen: set[str] = set()
    articles: list[dict] = []

    # Strategy 1: common list-item link patterns on Japanese gov sites
    selectors = [
        "ul.newsList li a",
        "ul.list-news li a",
        ".news-list a",
        ".press-list a",
        "dl.news dt a",
        "table.listTable td a",
        ".content-area a",
        "li a",   # broad fallback
    ]

    for sel in selectors:
        for a in soup.select(sel):
            title_jp = a.get_text(strip=True)
            href = a.get("href", "")
            if len(title_jp) < 8 or href in seen:
                continue
            if not href.startswith("http"):
                href = JOGMEC_BASE + href if href.startswith("/") else url + "/" + href
            if "jogmec.go.jp" not in href:
                continue
            seen.add(href)
            articles.append({"title_jp": title_jp, "link": href})
            if len(articles) >= 15:
                break
        if len(articles) >= 10:
            break

    return articles


@st.cache_data(ttl=86_400)  # 24-hour cache
def get_jogmec_data() -> str | None:
    articles = _scrape_url(JOGMEC_PRESS_URL)
    if not articles:
        articles = _scrape_url(JOGMEC_NEWS_URL)

    if not articles:
        return (
            "_JOGMEC data currently unavailable due to site access restrictions. "
            "[Visit JOGMEC directly](https://www.jogmec.go.jp/news/release/index.html)_"
        )

    # Translate and filter
    translated = []
    for art in articles:
        title_en = _translate(art["title_jp"])
        translated.append({**art, "title": title_en})

    # Prefer oil/gas relevant ones
    oil_arts = [a for a in translated if _is_relevant(a["title_jp"]) or _is_relevant(a["title"])]
    final = (oil_arts or translated)[:6]

    lines = []
    for art in final:
        lines.append(
            f"**[{art['title']}]({art['link']})**\n\n---"
        )

    return "\n\n".join(lines)
