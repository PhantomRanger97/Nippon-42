# utils/meti_scraper.py
"""
Fetches Japan's official petroleum stockpile data from METI.

Strategy (in order):
1. Auto-download the latest monthly PDF from enecho.meti.go.jp
2. Fall back to data/latest_oil.pdf (manually uploaded via sidebar)
3. Show a placeholder chart with instructions if both fail.

The PDF text is parsed with pdfplumber using a regex approach tuned to
the known structure of the 石油備蓄の現況 monthly release.
"""

import io
import os
import re
import requests
from bs4 import BeautifulSoup

import pandas as pd
import plotly.graph_objects as go
import pdfplumber
import streamlit as st

LOCAL_PDF_PATH = "data/latest_oil.pdf"

_BASE = "https://www.enecho.meti.go.jp"
_INDEX_URL = (
    "https://www.enecho.meti.go.jp/category/resources_and_fuel/"
    "petroleum_and_coal_oil/stockpile/"
)
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en;q=0.8",
    "Referer": _BASE,
}

# Japanese → English label mapping for chart display
_LABEL_MAP = {
    "国家備蓄": "National Reserve",
    "民間備蓄": "Commercial Reserve",
    "産油国共同備蓄": "Joint Producer Reserve",
    "合計": "Total",
    "原油": "Crude Oil",
    "製品": "Refined Products",
    "ガソリン": "Gasoline",
    "灯油": "Kerosene",
    "軽油": "Diesel",
    "重油": "Heavy Oil",
}

# Regex patterns for the summary section (known format)
_DAYS_PATTERN = re.compile(r"(国家備蓄|民間備蓄|産油国共同備蓄|合\s*計)[\s\S]{0,30}?(\d{1,3})日分")
_IEA_PATTERN = re.compile(r"(\d{2,3})日分[^\n]*?＜ＩＥＡ基準＞")
_KL_PATTERN = re.compile(
    r"(国家備蓄|民間備蓄|産油国共同備蓄|合\s*計)[\s\S]{0,60}?([\d，,]+)万ｋｌ"
)


def _normalize_num(s: str) -> float | None:
    """Convert full-width or comma-separated number string to float."""
    s = s.replace("，", "").replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def _fetch_latest_pdf_bytes() -> bytes | None:
    """Try to download the latest stockpile PDF from METI."""
    try:
        r = requests.get(_INDEX_URL, headers=_HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        pdf_links = [
            a["href"]
            for a in soup.find_all("a", href=True)
            if a["href"].lower().endswith(".pdf")
            and ("stockpile" in a["href"].lower() or "備蓄" in a.get_text())
        ]
        if not pdf_links:
            # Broader fallback — take any PDF on the page
            pdf_links = [
                a["href"]
                for a in soup.find_all("a", href=True)
                if a["href"].lower().endswith(".pdf")
            ]
        if not pdf_links:
            return None
        href = pdf_links[0]
        if not href.startswith("http"):
            href = _BASE + href
        pr = requests.get(href, headers=_HEADERS, timeout=30)
        pr.raise_for_status()
        return pr.content
    except Exception:
        return None


def _load_pdf_bytes() -> bytes | None:
    """Return PDF bytes from auto-download or local file, whichever works first."""
    pdf_bytes = _fetch_latest_pdf_bytes()
    if pdf_bytes:
        # Cache to local path so next load is fast
        try:
            os.makedirs("data", exist_ok=True)
            with open(LOCAL_PDF_PATH, "wb") as f:
                f.write(pdf_bytes)
        except Exception:
            pass
        return pdf_bytes

    # Fallback: local file
    if os.path.exists(LOCAL_PDF_PATH):
        with open(LOCAL_PDF_PATH, "rb") as f:
            return f.read()

    return None


def _parse_pdf(pdf_bytes: bytes) -> tuple[list[dict], dict]:
    """
    Returns:
      chart_data  — list of {label, value_kl} for the bar chart
      summary     — dict of key metrics extracted via regex
    """
    chart_data: list[dict] = []
    summary: dict = {}

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text() or ""
            full_text += text + "\n"

            # Table-based extraction for chart data
            for table in page.extract_tables():
                for row in table:
                    if not row:
                        continue
                    cells = [str(c).strip() if c else "" for c in row]
                    label_jp = cells[0]
                    if len(label_jp) < 2:
                        continue
                    # Find the first numeric cell
                    nums = []
                    for c in cells[1:]:
                        clean = re.sub(r"[^\d.]", "", c)
                        if clean:
                            try:
                                nums.append(float(clean))
                            except ValueError:
                                pass
                    if nums:
                        label_en = next(
                            (v for k, v in _LABEL_MAP.items() if k in label_jp),
                            label_jp,
                        )
                        chart_data.append({"label": label_en, "value": nums[0]})

    # Parse key summary metrics from full text via regex
    # Days of cover per category
    categories = {
        "国家備蓄": "national_days",
        "民間備蓄": "commercial_days",
        "産油国共同備蓄": "joint_days",
        "合　計": "total_days",
        "合 計": "total_days",
    }
    for jp, key in categories.items():
        m = re.search(
            re.escape(jp) + r"[\s\S]{0,40}?(\d{1,3})日分", full_text
        )
        if m and key not in summary:
            summary[key] = int(m.group(1))

    # IEA basis days
    iea_matches = _IEA_PATTERN.findall(full_text)
    if iea_matches:
        # The last match is typically the total
        summary["iea_days"] = int(iea_matches[-1])

    # kl volumes
    kl_hits = re.findall(
        r"(国家備蓄|民間備蓄|産油国共同備蓄|合\s*計)[\s\S]{0,60}?([\d，,]+)万ｋｌ",
        full_text,
    )
    for jp_cat, kl_str in kl_hits:
        key_map = {
            "国家備蓄": "national_kl",
            "民間備蓄": "commercial_kl",
            "産油国共同備蓄": "joint_kl",
            "合": "total_kl",
        }
        for k, v in key_map.items():
            if k in jp_cat and v not in summary:
                summary[v] = kl_str.replace("，", "")
                break

    return chart_data, summary


def _summary_to_chart_data(summary: dict) -> list[dict]:
    """
    Build chart rows from the regex-parsed summary when pdfplumber table
    extraction finds no tables (common for text-layout METI PDFs).
    Shows days-of-cover as the primary metric with kl volume as label.
    """
    import unicodedata

    def _kl(raw: str | None) -> float | None:
        if not raw:
            return None
        s = unicodedata.normalize("NFKC", str(raw)).replace(",", "").replace("，", "")
        try:
            return float(s)
        except ValueError:
            return None

    rows = []
    mappings = [
        ("national_days",    "national_kl",    "National Reserve"),
        ("commercial_days",  "commercial_kl",  "Commercial Reserve"),
        ("joint_days",       "joint_kl",       "Joint Producer Reserve"),
        ("total_days",       "total_kl",       "TOTAL"),
    ]
    for days_key, kl_key, label in mappings:
        days = summary.get(days_key)
        kl   = _kl(summary.get(kl_key))
        if days is not None:
            rows.append({
                "label": label,
                "days": days,
                "value": kl if kl else float(days),  # fallback to days for chart width
                "unit": "万kl" if kl else "days",
                "kl": kl,
            })
    return rows


@st.cache_data(ttl=86_400 * 7)  # 7-day cache (monthly releases)
def get_meti_stockpile_data():
    """Returns a Plotly figure or None."""
    pdf_bytes = _load_pdf_bytes()
    if not pdf_bytes:
        return _placeholder_chart(
            "METI PDF unavailable. Use the sidebar to upload the latest PDF from "
            "enecho.meti.go.jp, or wait for auto-fetch to succeed."
        )

    try:
        chart_data, summary = _parse_pdf(pdf_bytes)
    except Exception as e:
        return _placeholder_chart(f"Error parsing METI PDF: {str(e)[:80]}")

    # Most METI PDFs use text layout, not tables — build from summary instead
    if not chart_data and summary:
        chart_data = _summary_to_chart_data(summary)

    if not chart_data:
        return _placeholder_chart(
            "PDF loaded but no structured data found. The PDF format may have changed."
        )

    df = pd.DataFrame(chart_data)
    df = df.drop_duplicates(subset="label")

    # Dual-axis bar: kl volumes (primary) + days labels
    has_kl = "kl" in df.columns and df["kl"].notna().any()

    if has_kl:
        x_vals = df["kl"].fillna(0)
        x_title = "Volume (万kl  ·  10,000 kiloliters)"
        text_vals = df.apply(
            lambda r: f"{r['kl']:,.0f} 万kl  ({r['days']} days)" if pd.notna(r.get("kl")) else f"{r['days']} days",
            axis=1,
        )
    else:
        x_vals = df["days"] if "days" in df.columns else df["value"]
        x_title = "Days of Cover"
        text_vals = df["days"].apply(lambda d: f"{d} days") if "days" in df.columns else df["value"]

    # Highlight total row
    colors = ["#e8a020" if lbl != "TOTAL" else "#f5c842" for lbl in df["label"]]

    fig = go.Figure(
        go.Bar(
            x=x_vals,
            y=df["label"],
            orientation="h",
            marker_color=colors,
            text=text_vals,
            textposition="outside",
        )
    )

    # Add IEA 90-day obligation line (in days space this doesn't map to kl,
    # so we annotate as text instead)
    fig.update_layout(
        title="Japan Petroleum Stockpile Status (Latest METI Report)",
        xaxis_title=x_title,
        paper_bgcolor="#1c2333",
        plot_bgcolor="#1c2333",
        font=dict(color="white", size=12),
        height=360,
        margin=dict(l=200, r=80, t=60, b=40),
    )

    # Add IEA days annotation if available
    if summary.get("iea_days"):
        fig.add_annotation(
            text=f"IEA basis (total): {summary['iea_days']} days",
            xref="paper", yref="paper",
            x=1.0, y=-0.12,
            showarrow=False,
            font=dict(size=11, color="#aab8d0"),
            xanchor="right",
        )

    return fig


@st.cache_data(ttl=86_400 * 7)
def get_meti_stockpile_summary() -> dict:
    """Returns the parsed summary dict (days of cover, kl volumes, IEA days)."""
    pdf_bytes = _load_pdf_bytes()
    if not pdf_bytes:
        return {}
    try:
        _, summary = _parse_pdf(pdf_bytes)
        return summary
    except Exception:
        return {}


def _placeholder_chart(message: str):
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=13, color="#aab8d0"),
        align="center",
    )
    fig.update_layout(
        paper_bgcolor="#1c2333",
        plot_bgcolor="#1c2333",
        height=200,
    )
    return fig
