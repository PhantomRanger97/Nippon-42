import feedparser
from deep_translator import GoogleTranslator
import streamlit as st

FEEDS = {
    "nhk": "https://www3.nhk.or.jp/rss/news/cat6.xml",
    "reuters": [
        "https://feeds.reuters.com/reuters/energy",
        "https://feeds.reuters.com/reuters/businessNews",
        "https://www.reutersagency.com/feed/?best-topics=energy&post_type=best",
    ],
    "nikkei": "https://asia.nikkei.com/rss/feed/nar",
}

OIL_KEYWORDS = [
    "oil", "gas", "energy", "petroleum", "crude", "lng", "lpg",
    "refinery", "opec", "fuel", "barrel", "stockpile", "eneos",
    "idemitsu", "cosmo", "inpex", "jogmec", "meti", "nuclear",
    "renewable", "carbon", "emission", "pipeline", "tanker",
    "supply", "demand", "price", "japan", "asia",
    "石油", "原油", "エネルギー", "ガス", "備蓄"
]

def is_relevant(title, summary=""):
    combined = (title + " " + summary).lower()
    return any(kw.lower() in combined for kw in OIL_KEYWORDS)

def parse_feed(url, translate=False, filter_keywords=True):
    # Accept either a single URL string or a list of fallback URLs
    urls = url if isinstance(url, list) else [url]

    for u in urls:
        try:
            feed = feedparser.parse(u)
            if not feed.entries:
                continue  # try next URL in list

            articles = []
            for entry in feed.entries[:30]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")

                if filter_keywords and not is_relevant(title, summary):
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

            if articles:
                return articles  # return on first URL that yields results

        except Exception:
            continue  # try next URL in list

    return []  # all URLs failed

@st.cache_data(ttl=21600)  # 6-hour cache
def get_all_news():
    return {
        "nhk": parse_feed(FEEDS["nhk"], translate=True, filter_keywords=True),
        "reuters": parse_feed(FEEDS["reuters"], filter_keywords=False),  # already energy-specific feed
        "nikkei": parse_feed(FEEDS["nikkei"], filter_keywords=True),
    }
