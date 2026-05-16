# utils/ai_analysis.py
"""
Generates a daily energy market briefing using Claude.

Key improvement over v1: the function now accepts a `context` dict
containing live prices and METI stockpile figures, which are injected
into the prompt so the AI analysis is grounded in actual current data
rather than relying purely on training knowledge.
"""

import anthropic
import datetime
import streamlit as st


def _build_context_block(context: dict) -> str:
    """Format live data into a readable block for the prompt."""
    prices = context.get("prices", {})
    stockpile = context.get("stockpile", {})

    lines = ["--- LIVE DATA CONTEXT (use these figures in your analysis) ---"]

    if prices.get("brent"):
        chg = prices.get("brent_chg")
        chg_str = f" ({chg:+.2f}% today)" if chg is not None else ""
        lines.append(f"• Brent Crude: ${prices['brent']:.2f}/bbl{chg_str}")

    if prices.get("wti"):
        chg = prices.get("wti_chg")
        chg_str = f" ({chg:+.2f}% today)" if chg is not None else ""
        lines.append(f"• WTI Crude:   ${prices['wti']:.2f}/bbl{chg_str}")

    if prices.get("natgas"):
        chg = prices.get("natgas_chg")
        chg_str = f" ({chg:+.2f}% today)" if chg is not None else ""
        lines.append(f"• US Nat Gas:  ${prices['natgas']:.2f}/MMBtu{chg_str}")

    if stockpile.get("total_days"):
        lines.append(f"• Japan total stockpile: {stockpile['total_days']} days of cover")
    if stockpile.get("national_days"):
        lines.append(f"  – National reserve: {stockpile['national_days']} days")
    if stockpile.get("commercial_days"):
        lines.append(f"  – Commercial reserve: {stockpile['commercial_days']} days")
    if stockpile.get("iea_days"):
        lines.append(f"  – IEA-basis total: {stockpile['iea_days']} days")

    if len(lines) == 1:
        return ""  # No real data, omit the block
    return "\n".join(lines)


@st.cache_data(ttl=86_400)  # 24-hour cache
def get_ai_analysis(context: dict | None = None) -> str:
    context = context or {}
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
        client = anthropic.Anthropic(api_key=api_key)
    except (KeyError, Exception):
        return (
            "<i>AI analysis unavailable: <code>ANTHROPIC_API_KEY</code> not found "
            "in Streamlit secrets. Add it under Settings → Secrets.</i>"
        )

    today = datetime.date.today().strftime("%B %d, %Y")
    context_block = _build_context_block(context)

    prompt = f"""You are a senior energy analyst specializing in Japan's oil and gas sector.

Today is {today}.

{context_block}

Using the data above (where available) plus your knowledge of current market conditions,
provide a concise 180–220 word market intelligence briefing covering:

1. Current global crude oil price context and what it means for Japan as a major importer
2. Status of Japan's strategic petroleum stockpiles relative to IEA obligations (90-day rule)
3. Notable activity or developments from major Japanese refiners (ENEOS, Idemitsu, Cosmo Energy, INPEX)
4. Significant government policy or regulatory updates from METI or ANRE
5. One key risk or opportunity to watch in the next 30 days

Format rules:
- Write in a professional, factual tone suitable for an energy sector briefing
- Use <b>bold</b> tags for key figures and company names
- Structure as flowing paragraphs (no bullet points)
- Keep it sharp, data-anchored, and actionable
- Do not make up specific figures that aren't in the data context above"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=450,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception as e:
        return f"<i>AI analysis temporarily unavailable: {str(e)[:120]}</i>"
