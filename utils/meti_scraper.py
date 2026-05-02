import requests
from bs4 import BeautifulSoup
import pdfplumber
import pandas as pd
import plotly.graph_objects as go
import io
import re
import streamlit as st

BASE_URL = "https://www.enecho.meti.go.jp/statistics/petroleum_and_lpgas/pl001/results.html"
PDF_ROOT = "https://www.enecho.meti.go.jp"

STOCKPILE_LABELS = {
    "国家備蓄": "National Reserve",
    "民間備蓄": "Commercial Reserve",
    "産油国共同備蓄": "Joint Producer Reserve",
    "合計": "Total",
    "原油": "Crude Oil",
    "製品": "Products",
    "ガソリン": "Gasoline",
    "灯油": "Kerosene",
    "軽油": "Diesel",
    "重油": "Heavy Oil",
}

def translate_label(text):
    for jp, en in STOCKPILE_LABELS.items():
        if jp in text:
            return en
    return text

@st.cache_data(ttl=86400 * 7)
def get_meti_stockpile_data():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
        }
        resp = requests.get(BASE_URL, headers=headers, timeout=30)
        soup = BeautifulSoup(resp.text, "lxml")

        pdf_links = [
            a["href"] for a in soup.find_all("a", href=True)
            if "oil.pdf" in a["href"]
        ]
        if not pdf_links:
            return _placeholder_chart("No PDF links found on METI page.")

        pdf_url = PDF_ROOT + pdf_links[0]
        pdf_resp = requests.get(pdf_url, headers=headers, timeout=30)

        rows = []
        with pdfplumber.open(io.BytesIO(pdf_resp.content)) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table:
                        if row and any(cell for cell in row if cell):
                            rows.append(row)

        if not rows:
            return _placeholder_chart("PDF opened but no table data found.")

        df = pd.DataFrame(rows)
        df = df.dropna(how="all").reset_index(drop=True)

        chart_data = []
        for _, row in df.iterrows():
            cells = [str(c).strip() if c else "" for c in row]
            label = cells[0] if cells else ""
            nums = []
            for c in cells[1:]:
                clean = re.sub(r"[^\d.]", "", c)
                if clean:
                    try:
                        nums.append(float(clean))
                    except ValueError:
                        pass
            if label and nums and len(label) > 1:
                chart_data.append({
                    "label": translate_label(label),
                    "value": nums[0]
                })

        if not chart_data:
            return _placeholder_chart("Could not parse numeric data from PDF.")

        chart_df = pd.DataFrame(chart_data[:12])
        fig = go.Figure(go.Bar(
            x=chart_df["value"],
            y=chart_df["label"],
            orientation="h",
            marker_color="#e8a020",
            text=chart_df["value"].apply(lambda x: f"{x:,.0f}"),
            textposition="outside",
        ))
        fig.update_layout(
            title="Japan Petroleum Stockpile Status (Latest METI Report)",
            xaxis_title="Volume (kiloliters)",
            paper_bgcolor="#1c2333",
            plot_bgcolor="#1c2333",
            font=dict(color="white", size=12),
            height=450,
            margin=dict(l=160, r=40, t=60, b=40),
        )
        return fig

    except requests.exceptions.Timeout:
        return _placeholder_chart("METI server timed out. Will retry on next refresh.")
    except Exception as e:
        return _placeholder_chart(f"Error: {str(e)[:80]}")

def _placeholder_chart(message):
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=13, color="#aab8d0")
    )
    fig.update_layout(
        paper_bgcolor="#1c2333",
        plot_bgcolor="#1c2333",
        height=200
    )
    return fig
