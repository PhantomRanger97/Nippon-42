# utils/gov_announcements.py
"""
Fetches announcements from Japanese government agencies.

Sources:
  meti   — METI RSS feed (press releases)
  pmo    — Prime Minister's Office RSS
  anre   — Agency for Natural Resources and Energy (HTML scrape; no RSS)
  jogmec — JOGMEC press releases (HTML scrape; no RSS)

Translation: Japanese → English via deep-translator.
"""

import feedparser
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import streamlit as st

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en;q=0.8",
}

SOURCES = {
    "meti": {
        "rss": "https://www.meti.go.jp/rss/whatsnew.rss",
        "url": "https://www.meti.go.jp/press/index.html",
        "translate": True,
    },
    "pmo": {
        "rss": "https://www.kantei.go.jp/jp/rss/kantei.rdf",
        "url": "https://www.kantei.go.jp/jp/headline/index.html",
        "translate": True,
    },
    "anre": {
        "rss": None,
        "url": "https://www.enecho.meti.go.jp/information/press/index.html",
        "translate": True,
    },
    "jogmec": {
        "rss": None,
        "url": "https://www.jogmec.go.jp/news/release/index.html",
        "translate": True,
    },
}


def _translate(text: str) -> str:
    try:
        return GoogleTranslator(source="ja", target="en").translate(text[:400])
    except Exception:
        return text


def _fetch_rss(rss_url: str, do_translate: bool = False) -> list[dict]:
    try:
        feed = feedparser.parse(rss_url)
        items = []
        for entry in feed.entries[:8]:
            title = entry.get("title", "No title").strip()
            link = entry.get("link", "#")
            date = entry.get("published", "")[:16]
            if do_translate:
                title = _translate(title)
            items.append({"title": title, "link": link, "date": date})
        return items
    except Exception:
        return []


def _fetch_html(url: str, do_translate: bool = False) -> list[dict]:
    try:
        r = requests.get(url, headers=_HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        seen: set[str] = set()

        # Try common Japanese gov news-list patterns first
        for sel in [
            "ul.newsList li a",
            "ul.list-press li a",
            ".pressRelease a",
            ".news-list a",
            "dl.list dt a",
            "table a",
        ]:
            for a in soup.select(sel):
                title = a.get_text(strip=True)
                href = a.get("href", "")
                if len(title) < 10 or href in seen:
                    continue
                seen.add(href)
                if not href.startswith("http"):
                    base = "/".join(url.split("/")[:3])
                    href = base + href if href.startswith("/") else base + "/" + href
                if do_translate:
                    title = _translate(title)
                items.append({"title": title, "link": href, "date": ""})
                if len(items) >= 8:
                    break
            if items:
                break

        # Generic fallback
        if not items:
            for a in soup.find_all("a", href=True)[:20]:
                title = a.get_text(strip=True)
                href = a["href"]
                if len(title) < 10 or href in seen:
                    continue
                seen.add(href)
                if not href.startswith("http"):
                    base = "/".join(url.split("/")[:3])
                    href = base + href if href.startswith("/") else base + "/" + href
                if do_translate:
                    title = _translate(title)
                items.append({"title": title, "link": href, "date": ""})
                if len(items) >= 8:
                    break

        return items
    except Exception:
        return []


@st.cache_data(ttl=43_200)  # 12-hour cache
def get_all_announcements() -> dict[str, list[dict]]:
    results: dict[str, list[dict]] = {}
    for key, source in SOURCES.items():
        if source["rss"]:
            data = _fetch_rss(source["rss"], do_translate=source["translate"])
            # Fall back to HTML if RSS returns nothing
            if not data:
                data = _fetch_html(source["url"], do_translate=source["translate"])
        else:
            data = _fetch_html(source["url"], do_translate=source["translate"])
        results[key] = data
    return results
