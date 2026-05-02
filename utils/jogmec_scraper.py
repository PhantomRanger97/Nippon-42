import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import streamlit as st

JOGMEC_URL = "https://journal.jogmec.go.jp/oilgas/nglng/index.html"
BASE = "https://journal.jogmec.go.jp"

def translate(text):
    try:
        return GoogleTranslator(source='ja', target='en').translate(text[:500])
    except Exception:
        return text

@st.cache_data(ttl=86400 * 2)  # 2-day cache (updates weekly)
def get_jogmec_data():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(JOGMEC_URL, headers=headers, timeout=20)
        soup = BeautifulSoup(resp.text, "lxml")

        articles = []
        # Grab article listings — adjust selectors after inspecting live page
        for item in soup.select("li, .article-item, .news-item")[:8]:
            a_tag = item.find("a", href=True)
            if not a_tag:
                continue
            title_jp = a_tag.get_text(strip=True)
            link = a_tag["href"]
            if not link.startswith("http"):
                link = BASE + link
            if len(title_jp) < 5:
                continue
            title_en = translate(title_jp)

            # Try to get a snippet from the article page
            snippet = ""
            try:
                art_resp = requests.get(link, headers=headers, timeout=10)
                art_soup = BeautifulSoup(art_resp.text, "lxml")
                paras = art_soup.find_all("p")
                for p in paras[:3]:
                    text = p.get_text(strip=True)
                    if len(text) > 40:
                        snippet = translate(text[:400])
                        break
            except Exception:
                pass

            articles.append({
                "title": title_en,
                "link": link,
                "snippet": snippet,
            })

        if not articles:
            return "<i>No articles retrieved from JOGMEC journal. The page structure may have changed.</i>"

        # Format as markdown for display in Streamlit
        output = []
        for art in articles:
            output.append(f"""
**[{art['title']}]({art['link']})**

{art['snippet'] if art['snippet'] else '_No preview available_'}

---""")
        return "\n".join(output)

    except Exception as e:
        return f"<i>JOGMEC data unavailable: {str(e)}</i>"
