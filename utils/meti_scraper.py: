import requests
from bs4 import BeautifulSoup
import pdfplumber
import pandas as pd
import plotly.graph_objects as go
import io
import re
import streamlit as st
from deep_translator import GoogleTranslator

BASE_URL = "https://www.enecho.meti.go.jp/statistics/petroleum_and_lpgas/pl001/results.html"
PDF_ROOT = "https://www.enecho.meti.go.jp"

@st.cache_data(ttl=86400 * 7)  # weekly cache (PDF updates monthly)
def get_meti_stockpile_data():
    try:
        resp = requests.get(BASE_URL, timeout=15)
        soup = BeautifulSoup(resp.text, "lxml")
        # Grab the first (most recent) PDF link
        pdf_links = [a["href"] for a in soup.find_all("a", href=True) if "oil.pdf" in a["href"]]
        if not pdf_links:
            return None
        pdf_url = PDF_ROOT + pdf_links[0]
        pdf_resp = requests.get(pdf_url, timeout=20)
        
        with pdfplumber.open(io.BytesIO(pdf_resp.content)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            tables = []
            for page in pdf.pages:
                t = page.extract_table()
                if t:
                    tables.append(t)

        # Build a simple visualization from extracted text (stockpile numbers)
        # Real parsing will depend on table structure — this is a scaffold
        fig = go.Figure()
        fig.add_annotation(
            text=f"Latest METI PDF parsed.<br>Table data extracted — configure pandas parsing to your PDF structure.",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=14, color="white")
        )
        fig.update_layout(
            title="Japan Petroleum Stockpile Status (METI)",
            paper_bgcolor="#1c2333",
            plot_bgcolor="#1c2333",
            font_color="white"
        )
        return fig
    except Exception as e:
        return None
