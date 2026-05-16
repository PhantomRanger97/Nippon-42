# streamlit_app.py — Nippon-42: Japan Oil & Gas Monitor
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import datetime
from utils.news_fetcher import get_all_news
from utils.meti_scraper import get_meti_stockpile_data, get_meti_stockpile_summary
from utils.jogmec_scraper import get_jogmec_data
from utils.gov_announcements import get_all_announcements
from utils.ai_analysis import get_ai_analysis
from utils.market_data import get_market_prices

st.set_page_config(
    page_title="Nippon-42: Japan Oil & Gas Monitor",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Auto-refresh every 6 hours
st_autorefresh(interval=21_600 * 1000, key="main_refresh")

# ── Custom CSS ──────────────────────────────────────────────────────────────
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
        line-height: 1.7;
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
    .stMetric label { color: #aab8d0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────────────
col_logo, col_title, col_ts = st.columns([1, 6, 2])
with col_logo:
    st.markdown("## 🛢️")
with col_title:
    st.markdown("# Nippon-42: Japan Oil & Gas Monitor")
    st.markdown("*Real-time intelligence on Japan's petroleum sector*")
with col_ts:
    now_str = datetime.datetime.now().strftime("%b %d, %Y %H:%M JST")
    st.markdown(
        f"<div class='timestamp'>Last updated:<br>{now_str}</div>",
        unsafe_allow_html=True,
    )

st.divider()

# ── KPI Bar ─────────────────────────────────────────────────────────────────
prices = get_market_prices()
stockpile = get_meti_stockpile_summary()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    brent = prices.get("brent")
    brent_chg = prices.get("brent_chg")
    if brent:
        delta_str = f"{brent_chg:+.2f}%" if brent_chg is not None else None
        st.metric("Brent Crude (USD/bbl)", f"${brent:.2f}", delta_str)
    else:
        st.metric("Brent Crude (USD/bbl)", "—", help="Live feed unavailable")

with kpi2:
    total_days = stockpile.get("total_days")
    iea_days = stockpile.get("iea_days")
    if total_days:
        help_txt = f"IEA basis: {iea_days} days" if iea_days else "From latest METI report"
        st.metric("Japan Stockpile (days)", f"{total_days}", help=help_txt)
    else:
        st.metric("Japan Stockpile (days)", "—", help="From latest METI report")

with kpi3:
    wti = prices.get("wti")
    wti_chg = prices.get("wti_chg")
    if wti:
        delta_str = f"{wti_chg:+.2f}%" if wti_chg is not None else None
        st.metric("WTI Crude (USD/bbl)", f"${wti:.2f}", delta_str)
    else:
        st.metric("WTI Crude (USD/bbl)", "—", help="Live feed unavailable")

with kpi4:
    natgas = prices.get("natgas")
    natgas_chg = prices.get("natgas_chg")
    if natgas:
        delta_str = f"{natgas_chg:+.2f}%" if natgas_chg is not None else None
        st.metric("US Nat Gas (USD/MMBtu)", f"${natgas:.2f}", delta_str)
    else:
        st.metric("IEA Emergency Reserve", "90 days min", help="IEA strategic reserve target")

st.divider()

# ── Zone 1: AI Analysis ─────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🤖 AI Market Analysis</div>", unsafe_allow_html=True)

# Feed current data context into AI analysis
context = {
    "prices": prices,
    "stockpile": stockpile,
}
with st.spinner("Generating AI analysis from latest data…"):
    analysis = get_ai_analysis(context)

st.markdown(f"<div class='ai-analysis-box'>{analysis}</div>", unsafe_allow_html=True)

if st.button("🔄 Refresh Analysis", key="refresh_ai"):
    get_ai_analysis.clear()
    st.rerun()

st.divider()

# ── Zone 2: News ─────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📰 Latest News</div>", unsafe_allow_html=True)
news_col1, news_col2, news_col3 = st.columns(3)
news = get_all_news()

def render_news_cards(articles, source_label):
    if not articles:
        st.caption("No articles retrieved.")
        return
    for article in articles[:5]:
        title = article.get("title", "No title")
        link = article.get("link", "#")
        date = article.get("date", "")
        summary = article.get("summary", "")[:120]
        st.markdown(f"""
        <div class='news-card'>
            <span class='source-badge'>{source_label}</span>
            <span class='timestamp'>{date}</span><br>
            <a href="{link}" target="_blank" style="color:#c8d8f0;text-decoration:none;">
                <strong>{title}</strong>
            </a>
            <p style="color:#8899bb;font-size:0.85em;margin:4px 0 0 0;">{summary}{"…" if len(summary) == 120 else ""}</p>
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

# ── Zone 3: Data Visualizations ──────────────────────────────────────────────
st.markdown("<div class='section-header'>📊 Statistical Data</div>", unsafe_allow_html=True)
tab1, tab2 = st.tabs(["🗃️ METI Petroleum Stockpile", "⛽ JOGMEC Oil & Gas Report"])

with tab1:
    with st.spinner("Loading METI stockpile data…"):
        meti_fig = get_meti_stockpile_data()
    if meti_fig:
        st.plotly_chart(meti_fig, use_container_width=True)

        # Show key numbers as a quick-read table
        if stockpile:
            st.markdown("**Key figures (latest METI report)**")
            cols = st.columns(3)
            items = [
                ("National Reserve", stockpile.get("national_days"), "days", stockpile.get("national_kl")),
                ("Commercial Reserve", stockpile.get("commercial_days"), "days", stockpile.get("commercial_kl")),
                ("Joint Producer Reserve", stockpile.get("joint_days"), "days", stockpile.get("joint_kl")),
            ]
            for col, (label, days, unit, kl) in zip(cols, items):
                with col:
                    kl_str = f" ({kl}万kl)" if kl else ""
                    st.metric(label, f"{days} {unit}{kl_str}" if days else "—")
    else:
        st.info("METI data temporarily unavailable.")

    with st.expander("ℹ️ How METI data is fetched"):
        st.markdown("""
        This panel auto-fetches the latest monthly petroleum stockpile report PDF from
        **enecho.meti.go.jp** and extracts the structured data using `pdfplumber`.

        If automatic fetching fails (e.g. METI changes their URL format), you can manually
        upload the latest PDF via the sidebar below.
        """)

    # Manual PDF upload fallback
    with st.sidebar:
        st.markdown("### 📎 Manual METI PDF Upload")
        st.caption("Use if auto-fetch fails. Download from [METI](https://www.enecho.meti.go.jp/category/resources_and_fuel/petroleum_and_coal_oil/stockpile/) and upload here.")
        uploaded = st.file_uploader("Upload METI PDF", type="pdf", key="meti_pdf")
        if uploaded:
            import os
            os.makedirs("data", exist_ok=True)
            with open("data/latest_oil.pdf", "wb") as f:
                f.write(uploaded.read())
            get_meti_stockpile_data.clear()
            get_meti_stockpile_summary.clear()
            st.success("PDF saved — data will update on next load.")
            st.rerun()

with tab2:
    with st.spinner("Loading JOGMEC data…"):
        jogmec_content = get_jogmec_data()
    if jogmec_content:
        st.markdown(jogmec_content)
    else:
        st.info("JOGMEC data temporarily unavailable.")

st.divider()

# ── Zone 4: Government Announcements ─────────────────────────────────────────
st.markdown("<div class='section-header'>🏛️ Government Announcements</div>", unsafe_allow_html=True)
ann_col1, ann_col2 = st.columns(2)
announcements = get_all_announcements()

with ann_col1:
    with st.expander("METI — Ministry of Economy, Trade and Industry", expanded=True):
        items = announcements.get("meti", [])
        if items:
            for item in items[:5]:
                st.markdown(f"- [{item['title']}]({item['link']}) *{item.get('date', '')}*")
        else:
            st.caption("No announcements retrieved.")

    with st.expander("ANRE — Agency for Natural Resources and Energy"):
        items = announcements.get("anre", [])
        if items:
            for item in items[:5]:
                st.markdown(f"- [{item['title']}]({item['link']}) *{item.get('date', '')}*")
        else:
            st.caption("No announcements retrieved.")

with ann_col2:
    with st.expander("Prime Minister's Office", expanded=True):
        items = announcements.get("pmo", [])
        if items:
            for item in items[:5]:
                st.markdown(f"- [{item['title']}]({item['link']}) *{item.get('date', '')}*")
        else:
            st.caption("No announcements retrieved.")

    with st.expander("JOGMEC — Japan Organization for Metals and Energy Security"):
        items = announcements.get("jogmec", [])
        if items:
            for item in items[:5]:
                st.markdown(f"- [{item['title']}]({item['link']}) *{item.get('date', '')}*")
        else:
            st.caption("No announcements retrieved.")

st.divider()

# ── Zone 5: Sources ───────────────────────────────────────────────────────────
with st.expander("📚 Data Sources & Methodology", expanded=False):
    st.markdown("""
    | Source | Type | URL | Refresh Cadence |
    |--------|------|-----|-----------------|
    | NHK World | RSS | nhk.or.jp/rss/news/cat6.xml | 6 hrs |
    | Reuters | RSS | rss.app (Reuters energy feed) | 6 hrs |
    | Nikkei Asia | RSS | asia.nikkei.com/rss/feed/nar | 6 hrs |
    | METI Petroleum Stockpile | Auto PDF scrape | enecho.meti.go.jp | Monthly |
    | JOGMEC Press Releases | Web scrape | jogmec.go.jp/news/release | Daily |
    | METI Announcements | RSS | meti.go.jp/rss/whatsnew.rss | 12 hrs |
    | Prime Minister's Office | RSS | kantei.go.jp | 12 hrs |
    | Brent / WTI / Nat Gas | Yahoo Finance RSS | finance.yahoo.com | 6 hrs |
    | AI Analysis | Claude API (Anthropic) | anthropic.com | Daily |

    **Translations:** Japanese sources translated via `deep-translator` (Google Translate).

    **Disclaimer:** AI-generated analysis is a synthesis tool and should not be used as the
    sole basis for investment or policy decisions.
    """)
