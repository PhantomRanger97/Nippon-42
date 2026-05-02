import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import streamlit as st

# Confirmed working URLs
JOGMEC_PRESS_URL = "https://www.jogmec.go.jp/news/release/index.html"
JOGMEC_BASE = "https://www.jogmec.go.jp"

OIL_KEYWORDS = [
    "石油", "天然ガス", "原油", "エネルギー", "LNG", "掘削", "備蓄",
    "oil", "gas", "lng", "petroleum", "crude", "energy", "exploration",
    "production", "stockpile", "reserve", "refin"
]

def translate(text):
    try:
        return GoogleTranslator(source='ja', target='en').translate(text[:500])
    except Exception:
        return text

def is_relevant(text):
    return any(kw.lower() in text.lower() for kw in OIL_KEYWORDS)

@st.cache_data(ttl=86400 * 2)
def get_jogmec_data():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "ja,en;q=0.9",
        }
        resp = requests.get(JOGMEC_PRESS_URL, headers=headers, timeout=20)
        soup = BeautifulSoup(resp.text, "lxml")

        articles = []

        # Try multiple selectors to find press release list items
        candidates = (
            soup.select("li a") +
            soup.select(".news-list a") +
            soup.select(".press-list a") +
            soup.select("table a") +
            soup.select(".content a")
        )

        seen = set()
        for a in candidates:
            title_jp = a.get_text(strip=True)
            href = a.get("href", "")
            if len(title_jp) < 8 or href in seen:
                continue
            seen.add(href)
            if not href.startswith("http"):
                href = JOGMEC_BASE + href
            # Only include JOGMEC domain links
            if "jogmec.go.jp" not in href:
                continue
            title_en = translate(title_jp)
            articles.append({
                "title": title_en,
                "title_jp": title_jp,
                "link": href,
            })
            if len(articles) >= 10:
                break

        # Filter to oil/gas relevant ones if we have enough
        oil_articles = [a for a in articles if is_relevant(a["title_jp"]) or is_relevant(a["title"])]
        final = oil_articles[:6] if oil_articles else articles[:6]

        if not final:
            return "_No JOGMEC press releases retrieved. [Visit JOGMEC directly](https://www.jogmec.go.jp/news/release/index.html)_"

        output = []
        for art in final:
            output.append(f"""**[{art['title']}]({art['link']})**

_No preview available_

---""")
        return "\n".join(output)

    except Exception as e:
        return f"_JOGMEC data unavailable: {str(e)[:60]}. [Visit JOGMEC directly](https://www.jogmec.go.jp/news/release/index.html)_"
