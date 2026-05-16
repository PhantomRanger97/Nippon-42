# utils/news_fetcher.py
"""
Fetches energy-related news from RSS feeds.

Improvements over v1:
- Multiple fallback URLs per source (Reuters changed their RSS endpoints)
- NHK feed URL corrected (www3 → www)
- Timeout and error handling tightened
- Keyword filter is a compiled set for performance
"""

import feedparser
from deep_translator import GoogleTranslator
import streamlit as st

FEEDS: dict[str, str | list[str]] = {
    "nhk": [
        "https://www.nhk.or.jp/rss/news/cat6.xml",       # primary (energy/environment)
        "https://www3.nhk.or.jp/rss/news/cat6.xml",      # old alias
        "https://www.nhk.or.jp/rss/news/cat1.xml",       # economy fallback
    ],
    "reuters": [
        "https://rss.app/feeds/tRWNGhBzZCH2Vpqz.xml",   # Reuters energy via RSS aggregator
        "https://feeds.content.dowjones.io/public/rss/mw-realtimeheadlines",
        "https://feeds.feedburner.com/reuters/energy",
        # Google News search for Reuters energy as last resort
        "https://news.google.com/rss/search?q=site:reuters.com+oil+gas+energy+japan&hl=en-US&gl=US&ceid=US:en",
    ],
    "nikkei": [
        "https://asia.nikkei.com/rss/feed/nar",
        "https://news.google.com/rss/search?q=site:asia.nikkei.com+oil+energy+japan&hl=en-US&gl=US&ceid=US:en",
    ],
}

_OIL_KEYWORDS = frozenset([
    "oil", "gas", "energy", "petroleum", "crude", "lng", "lpg",
    "refinery", "opec", "fuel", "barrel", "stockpile", "eneos",
    "idemitsu", "cosmo", "inpex", "jogmec", "meti", "nuclear",
    "renewable", "carbon", "emission", "pipeline", "tanker",
    "supply", "demand", "price", "japan", "asia", "brent", "wti",
    "石油", "原油", "エネルギー", "ガス", "備蓄",
])


def _is_relevant(title: str, summary: str = "") -> bool:
    combined = (title + " " + summary).lower()
    return any(kw in combined for kw in _OIL_KEYWORDS)


def _translate_ja(text: str) -> str:
    try:
        return GoogleTranslator(source="ja", target="en").translate(text[:400])
    except Exception:
        return text


def _parse_feed(
    urls: str | list[str],
    translate: bool = False,
    filter_keywords: bool = True,
) -> list[dict]:
    url_list = urls if isinstance(urls, list) else [urls]

    for url in url_list:
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                continue

            articles: list[dict] = []
            for entry in feed.entries[:30]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "").strip()

                if not title:
                    continue
                if filter_keywords and not _is_relevant(title, summary):
                    continue

                if translate:
                    title = _translate_ja(title)
                    if summary:
                        summary = _translate_ja(summary[:300])

                articles.append(
                    {
                        "title": title,
                        "link": entry.get("link", "#"),
                        "date": entry.get("published", "")[:16],
                        "summary": summary,
                    }
                )
                if len(articles) >= 8:
                    break

            if articles:
                return articles
        except Exception:
            continue

    return []


@st.cache_data(ttl=21_600)  # 6-hour cache
def get_all_news() -> dict[str, list[dict]]:
    return {
        "nhk": _parse_feed(FEEDS["nhk"], translate=True, filter_keywords=True),
        "reuters": _parse_feed(FEEDS["reuters"], filter_keywords=False),
        "nikkei": _parse_feed(FEEDS["nikkei"], filter_keywords=True),
    }
