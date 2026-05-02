import anthropic
import streamlit as st
import datetime
import os

@st.cache_data(ttl=86400)
def get_ai_analysis():
    try:
        # Read directly from Streamlit secrets
        api_key = st.secrets["ANTHROPIC_API_KEY"]
        client = anthropic.Anthropic(api_key=api_key)
        today = datetime.date.today().strftime("%B %d, %Y")
        prompt = f"""You are a senior energy analyst specializing in Japan's oil and gas sector.

Today is {today}. Provide a concise 150-200 word market intelligence briefing covering:
1. Current global crude oil price context and impact on Japan
2. Key supply chain or stockpile developments in Japan
3. Notable activity from major Japanese refiners (ENEOS, Idemitsu, Cosmo Energy)
4. Any significant government policy updates from METI or ANRE
5. One key risk or opportunity to watch

Write in a professional, factual tone. Use HTML formatting with <b> tags for emphasis. Keep it sharp and actionable."""

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except KeyError:
        return "<i>AI analysis unavailable: ANTHROPIC_API_KEY not found in secrets.</i>"
    except Exception as e:
        return f"<i>AI analysis temporarily unavailable: {str(e)}</i>"
