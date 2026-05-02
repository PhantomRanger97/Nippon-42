import feedparser
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import streamlit as st

SOURCES = {
    "meti": {
        "url": "https://www.meti.go.jp/press/index.html",
        "rss": "https://www.meti.go.jp/rss/whatsnew.rss",
        "translate": True,
    },
    "pmo": {
        "url": "https://www.kantei.go.jp/jp/headline/index.html",
        "rss": "https://www.kantei.go.jp/jp/rss/kantei.rdf",
        "translate": True,
    },
    "anre": {
        "url": "https://www.enecho.meti.go.jp/information/press/index.html",
        "rss": None,
        "translate": True,
    },
    "jogmec": {
        "url": "https://www.jogmec.go.jp/news/release/index.html",
        "rss": None,
        "translate": True,
    },
}

def translate(text):
    try:
        return GoogleTranslator(source='ja', target='en').translate(text[:400])
    except Exception:
        return text

def fetch_rss(rss_url, translate_text=False):
    try:
        feed = feedparser.parse(rss_url)
        items = []
        for entry in feed.entries[:6]:
            title = entry.get("title", "No title")
            link = entry.get("link", "#")
            date = entry.get("published", "")[:16]
            if translate_text:
                title = translate(title)
            items.append({"title": title, "link": link, "date": date})
        return items
    except Exception:
        return []

def fetch_html_announcements(url, translate_text=False):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "lxml")
        items = []
        # Generic anchor tag scrape — captures most gov news list formats
        for a in soup.find_all("a", href=True)[:10]:
            title = a.get_text(strip=True)
            link = a["href"]
            if len(title) < 10:
                continue
            if not link.startswith("http"):
                base = "/".join(url.split("/")[:3])
                link = base + link
            if translate_text:
                title = translate(title)
            items.append({"title": title, "link": link, "date": ""})
        return items
    except Exception:
        return []

@st.cache_data(ttl=43200)  # 12-hour cache
def get_all_announcements():
    results = {}
    for key, source in SOURCES.items():
        if source["rss"]:
            results[key] = fetch_rss(source["rss"], translate_text=source["translate"])
        else:
            results[key] = fetch_html_announcements(source["url"], translate_text=source["translate"])
    return results
