import feedparser
import datetime
from deep_translator import GoogleTranslator
import streamlit as st

FEEDS = {
    "nhk": "https://www3.nhk.or.jp/rss/news/cat6.xml",
    "reuters": "https://feeds.reuters.com/reuters/businessNews",
    "nikkei": "https://asia.nikkei.com/rss/feed/nar",
}

def parse_feed(url, translate=False):
    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:8]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
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
        return articles
    except Exception as e:
        return []

@st.cache_data(ttl=21600)  # 6 hour cache
def get_all_news():
    return {
        "nhk": parse_feed(FEEDS["nhk"], translate=True),
        "reuters": parse_feed(FEEDS["reuters"]),
        "nikkei": parse_feed(FEEDS["nikkei"]),
    }
