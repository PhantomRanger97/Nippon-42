import feedparser
from deep_translator import GoogleTranslator
import streamlit as st

FEEDS = {
    "nhk": "https://www3.nhk.or.jp/rss/news/cat6.xml",
    "reuters": "https://feeds.reuters.com/reuters/businessNews",
    "nikkei": "https://asia.nikkei.com/rss/feed/nar",
}

OIL_KEYWORDS = [
    "oil", "gas", "energy", "petroleum", "crude", "lng", "lpg",
    "refinery", "opec", "fuel", "barrel", "stockpile", "eneos",
    "idemitsu", "cosmo", "inpex", "jogmec", "meti", "nuclear",
    "renewable", "carbon", "emission", "pipeline", "tanker",
    "石油", "原油", "エネルギー", "ガス", "備蓄"
]

def is_relevant(title, summary=""):
    combined = (title + " " + summary).lower()
    return any(kw.lower() in combined for kw in OIL_KEYWORDS)

def parse_feed(url, translate=False):
    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:30]:  # scan more, filter down
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            if not is_relevant(title, summary):
                continue
            if translate:
                try:
                    title = GoogleTranslator(source='ja', target='en').translate(title)
                    summary = GoogleTranslator(source='ja', target='en').translate(summary[:300])
                except Exception:
                    pass
            articles.append({
                "title": title,
                "link": entry.get("link", "#"),
                "date": entry.get("published", "")[:16],
                "summary": summary,
            })
            if len(articles) >= 8:
                break
        return articles
    except Exception:
        return []

@st.cache_data(ttl=21600)
def get_all_news():
    return {
        "nhk": parse_feed(FEEDS["nhk"], translate=True),
        "reuters": parse_feed(FEEDS["reuters"]),
        "nikkei": parse_feed(FEEDS["nikkei"]),
    }
