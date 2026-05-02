import feedparser
from deep_translator import GoogleTranslator
import streamlit as st

# JOGMEC RSS feeds
JOGMEC_FEEDS = [
    "https://www.jogmec.go.jp/rss/news.xml",
    "https://www.jogmec.go.jp/rss/press.xml",
]

OIL_KEYWORDS = [
    "oil", "gas", "lng", "petroleum", "crude", "energy",
    "石油", "天然ガス", "原油", "エネルギー", "LNG", "掘削",
    "exploration", "production", "refin", "stockpile", "reserve"
]

def translate(text):
    try:
        return GoogleTranslator(source='ja', target='en').translate(text[:500])
    except Exception:
        return text

def is_relevant(title):
    return any(kw.lower() in title.lower() for kw in OIL_KEYWORDS)

@st.cache_data(ttl=86400 * 2)
def get_jogmec_data():
    articles = []

    for feed_url in JOGMEC_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:20]:
                title_jp = entry.get("title", "")
                link = entry.get("link", "#")
                summary_jp = entry.get("summary", "")
                date = entry.get("published", "")[:16]
                if len(title_jp) < 5:
                    continue
                title_en = translate(title_jp)
                snippet_en = translate(summary_jp[:400]) if summary_jp else ""
                articles.append({
                    "title": title_en,
                    "link": link,
                    "snippet": snippet_en,
                    "date": date,
                })
                if len(articles) >= 8:
                    break
        except Exception:
            continue
        if articles:
            break

    if not articles:
        return "_No JOGMEC press releases available at this time. [Visit JOGMEC directly](https://www.jogmec.go.jp/news/release/index.html)_"

    output = []
    for art in articles:
        date_str = f" *{art['date']}*" if art['date'] else ""
        output.append(f"""**[{art['title']}]({art['link']})**{date_str}

{art['snippet'] if art['snippet'] else '_No preview available_'}

---""")
    return "\n".join(output)
