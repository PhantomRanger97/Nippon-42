# 🛢️ Nippon-42: Japan Oil & Gas Monitor

Real-time intelligence dashboard tracking Japan's petroleum sector — prices, government stockpile data, news, and AI-generated market analysis.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)

---

## What it does

| Zone | Content | Source |
|------|---------|--------|
| **KPI Bar** | Brent, WTI, Nat Gas (live) + Japan stockpile days | Yahoo Finance · METI PDF |
| **AI Briefing** | 200-word analyst memo grounded in live data | Claude API (Anthropic) |
| **News** | NHK World · Reuters · Nikkei Asia (auto-translated) | RSS feeds |
| **METI Stockpile** | Bar chart of national/commercial/joint reserves | Auto-fetched METI PDF |
| **JOGMEC** | Latest press releases (translated) | jogmec.go.jp scrape |
| **Gov Announcements** | METI · ANRE · PMO · JOGMEC releases | RSS + HTML scrape |

Auto-refreshes every **6 hours**.

---

## Setup

### 1. Clone & install

```bash
git clone <your-repo>
cd nippon-42
pip install -r requirements.txt
```

### 2. Set your Anthropic API key

Create `.streamlit/secrets.toml`:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

On Streamlit Cloud: **Settings → Secrets** and paste the same key.

### 3. Run

```bash
streamlit run streamlit_app.py
```

---

## METI PDF

The METI petroleum stockpile PDF (`石油備蓄の現況`) is published monthly by ANRE.

- **Auto-fetch** is attempted first from `enecho.meti.go.jp`
- If the site blocks scraping, use the **sidebar uploader** in the app
- Download manually from: https://www.enecho.meti.go.jp/category/resources_and_fuel/petroleum_and_coal_oil/stockpile/

The parsed PDF is cached locally at `data/latest_oil.pdf` for 7 days.

---

## Project structure

```
nippon-42/
├── streamlit_app.py          # Main app
├── requirements.txt
├── .streamlit/
│   └── config.toml           # Theme + server config
├── data/
│   └── latest_oil.pdf        # Auto-cached or manually uploaded METI PDF
└── utils/
    ├── __init__.py
    ├── market_data.py         # Live Brent/WTI/NatGas prices
    ├── meti_scraper.py        # METI PDF auto-fetch + parse
    ├── jogmec_scraper.py      # JOGMEC press release scraper
    ├── news_fetcher.py        # RSS news feeds
    ├── gov_announcements.py   # Gov agency announcements
    ├── ai_analysis.py         # Claude API briefing (data-grounded)
    └── translator.py          # Japanese → English helpers
```

---

## Data sources

| Source | Type | Cadence |
|--------|------|---------|
| Yahoo Finance (BZ=F, CL=F, NG=F) | JSON API | 6 hrs |
| METI — 石油備蓄の現況 | PDF auto-fetch | 7 days |
| JOGMEC press releases | HTML scrape | 24 hrs |
| NHK World RSS | RSS | 6 hrs |
| Reuters energy RSS | RSS | 6 hrs |
| Nikkei Asia RSS | RSS | 6 hrs |
| METI/ANRE/PMO announcements | RSS + HTML | 12 hrs |
| AI Analysis | Claude API | 24 hrs |

**Disclaimer:** AI-generated analysis is a synthesis tool. Do not use as the sole basis for investment or policy decisions.
