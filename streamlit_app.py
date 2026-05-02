# app.py
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import datetime
from utils.news_fetcher import get_all_news
from utils.meti_scraper import get_meti_stockpile_data
from utils.jogmec_scraper import get_jogmec_data
from utils.gov_announcements import get_all_announcements
from utils.ai_analysis import get_ai_analysis

st.set_page_config(
    page_title="Japan Oil & Gas Monitor",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Auto-refresh every 6 hours (21600 seconds)
st_autorefresh(interval=21600 * 1000, key="main_refresh")

# --- Custom CSS ---
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .kpi-card {
        background: #1c2333;
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid #e8a020;
        margin-bottom: 8px;
    }
    .news-card {
        background: #1c2333;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        border-top: 2px solid #2d3a55;
    }
    .section-header {
        color: #e8a020;
        font-size: 1.1em;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 16px 0 8px 0;
    }
    .ai-analysis-box {
        background: linear-gradient(135deg, #1a2438 0%, #1c2e44 100%);
        border: 1px solid #e8a020;
        border-radius: 12px;
        padding: 24px;
        margin: 16px 0;
    }
    .source-badge {
        display: inline-block;
        background: #2d3a55;
        color: #aab8d0;
        font-size: 0.7em;
        padding: 2px 8px;
        border-radius: 20px;
        margin-right: 6px;
    }
    .timestamp { color: #6b7a99; font-size: 0.8em; }
</style>
""", unsafe_allow_html=True)

# === HEADER ===
col_logo, col_title, col_ts = st.columns([1, 6, 2])
with col_logo:
    st.markdown("## 🛢️")
with col_title:
    st.markdown("# Japan Oil & Gas Monitor")
    st.markdown("*Real-time intelligence on Japan's petroleum sector*")
with col_ts:
    st.markdown(f"<div class='timestamp'>Last updated:<br>{datetime.datetime.now().strftime('%b %d, %Y %H:%M JST')}</div>", unsafe_allow_html=True)

st.divider()

# === KPI BAR ===
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("Brent Crude (USD/bbl)", "$82.40", "+0.8%")
with kpi2:
    st.metric("Japan Stockpile (days)", "—", help="From latest METI report")
with kpi3:
    st.metric("LNG Spot Price ($/MMBtu)", "—", help="From JOGMEC weekly data")
with kpi4:
    st.metric("IEA Emergency Reserve", "90 days min", help="IEA strategic reserve target")

st.divider()

# === ZONE 1: AI ANALYSIS (Center, Eye Level) ===
st.markdown("<div class='section-header'>🤖 AI Market Analysis</div>", unsafe_allow_html=True)
with st.spinner("Generating analysis..."):
    analysis = get_ai_analysis()
st.markdown(f"<div class='ai-analysis-box'>{analysis}</div>", unsafe_allow_html=True)

st.divider()

# === ZONE 2: NEWS (Three Columns) ===
st.markdown("<div class='section-header'>📰 Latest News</div>", unsafe_allow_html=True)
news_col1, news_col2, news_col3 = st.columns(3)

news = get_all_news()

def render_news_cards(articles, source_label):
    for article in articles[:5]:
        st.markdown(f"""
        <div class='news-card'>
            <span class='source-badge'>{source_label}</span>
            <span class='timestamp'>{article.get('date', '')}</span><br>
            <a href="{article['link']}" target="_blank" style="color:#c8d8f0; text-decoration:none;">
                <strong>{article['title']}</strong>
            </a>
            <p style="color:#8899bb; font-size:0.85em; margin:4px 0 0 0;">{article.get('summary', '')[:120]}...</p>
        </div>
        """, unsafe_allow_html=True)

with news_col1:
    st.markdown("**NHK World**")
    render_news_cards(news.get("nhk", []), "NHK")

with news_col2:
    st.markdown("**Reuters**")
    render_news_cards(news.get("reuters", []), "Reuters")

with news_col3:
    st.markdown("**Nikkei Asia**")
    render_news_cards(news.get("nikkei", []), "Nikkei")

st.divider()

# === ZONE 3: DATA VISUALIZATIONS ===
st.markdown("<div class='section-header'>📊 Statistical Data</div>", unsafe_allow_html=True)
tab1, tab2 = st.tabs(["🗃️ METI Petroleum Stockpile (Monthly)", "⛽ JOGMEC Oil & Gas Report (Weekly)"])

with tab1:
    with st.spinner("Loading METI stockpile data..."):
        meti_fig = get_meti_stockpile_data()
    if meti_fig:
        st.plotly_chart(meti_fig, use_container_width=True)
    else:
        st.info("METI data temporarily unavailable. Will retry on next refresh.")

with tab2:
    with st.spinner("Loading JOGMEC data..."):
        jogmec_content = get_jogmec_data()
    if jogmec_content:
        st.markdown(jogmec_content)
    else:
        st.info("JOGMEC data temporarily unavailable.")

st.divider()

# === ZONE 4: GOVERNMENT ANNOUNCEMENTS ===
st.markdown("<div class='section-header'>🏛️ Government Announcements</div>", unsafe_allow_html=True)
ann_col1, ann_col2 = st.columns(2)

announcements = get_all_announcements()

with ann_col1:
    with st.expander("METI — Ministry of Economy, Trade and Industry", expanded=True):
        for item in announcements.get("meti", [])[:5]:
            st.markdown(f"- [{item['title']}]({item['link']}) *{item.get('date','')}*")
    with st.expander("ANRE — Agency for Natural Resources and Energy"):
        for item in announcements.get("anre", [])[:5]:
            st.markdown(f"- [{item['title']}]({item['link']}) *{item.get('date','')}*")

with ann_col2:
    with st.expander("Prime Minister's Office", expanded=True):
        for item in announcements.get("pmo", [])[:5]:
            st.markdown(f"- [{item['title']}]({item['link']}) *{item.get('date','')}*")
    with st.expander("JOGMEC — Japan Organization for Metals and Energy Security"):
        for item in announcements.get("jogmec", [])[:5]:
            st.markdown(f"- [{item['title']}]({item['link']}) *{item.get('date','')}*")

st.divider()

# === ZONE 5: SOURCES BIBLIOGRAPHY ===
with st.expander("📚 Data Sources & Methodology", expanded=False):
    st.markdown("""
    | Source | Type | URL | Refresh Cadence |
    |--------|------|-----|-----------------|
    | NHK World | News RSS | nhk.or.jp/rss/news/cat6.xml | Every 6–12 hrs |
    | Reuters | News RSS | feeds.reuters.com/reuters/businessNews | Every 6–12 hrs |
    | Nikkei Asia | News RSS | asia.nikkei.com/rss/feed/nar | Every 6–12 hrs |
    | METI — Petroleum Stockpile | PDF Statistical Report | enecho.meti.go.jp | Monthly |
    | JOGMEC Oil & Gas Journal | Web Scrape | journal.jogmec.go.jp | Weekly |
    | METI Announcements | Web Scrape / RSS | meti.go.jp | Daily |
    | Prime Minister's Office | Web Scrape | kantei.go.jp | Daily |
    | ANRE | Web Scrape | enecho.meti.go.jp | Daily |
    | AI Analysis | Claude API (Anthropic) | anthropic.com | Daily |
    
    **Translation:** Japanese-language sources translated via `deep-translator` (Google Translate API wrapper).  
    **Disclaimer:** AI-generated analysis is a synthesis tool and should not be used as sole basis for investment or policy decisions.
    """)
