import feedparser
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import streamlit as st

# JOGMEC publishes press releases via RSS — more reliable than scraping JS site
JOGMEC_RSS = "https://www.jogmec.go.jp/rss/news.xml"
JOGMEC_FALLBACK_URL = "https://www.jogmec.go.jp/news/release/index.html"
BASE = "https://www.jogmec.go.jp"

def translate(text):
    try:
        return GoogleTranslator(source='ja', target='en').translate(text[:500])
    except Exception:
        return text

@st.cache_data(ttl=86400 * 2)
def get_jogmec_data():
    articles = []

    # Try RSS first
    try:
        feed = feedparser.parse(JOGMEC_RSS)
        for entry in feed.entries[:8]:
            title_jp = entry.get("title", "")
            link = entry.get("link", "#")
            summary_jp = entry.get("summary", "")
            if len(title_jp) < 5:
                continue
            articles.append({
                "title": translate(title_jp),
                "link": link,
                "snippet": translate(summary_jp[:400]) if summary_jp else "",
            })
    except Exception:
        pass

    # Fallback: scrape HTML press release page
    if not articles:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(JOGMEC_FALLBACK_URL, headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, "lxml")
            for a in soup.find_all("a", href=True)[:15]:
                title_jp = a.get_text(strip=True)
                link = a["href"]
                if len(title_jp) < 10:
                    continue
                if not link.startswith("http"):
                    link = BASE + link
                articles.append({
                    "title": translate(title_jp),
                    "link": link,
                    "snippet": "",
                })
                if len(articles) >= 6:
                    break
        except Exception:
            pass

    if not articles:
        return "_No JOGMEC data available at this time._"

    output = []
    for art in articles:
        output.append(f"""**[{art['title']}]({art['link']})**

{art['snippet'] if art['snippet'] else '_No preview available_'}

---""")
    return "\n".join(output)
