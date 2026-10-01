import os
import re
from datetime import datetime, timezone

import streamlit as st
from google import genai
from tavily import TavilyClient
from tavily.errors import InvalidAPIKeyError

st.set_page_config(
    page_title="AI Competitive Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {max-width:1250px; padding-top:2rem; padding-bottom:3rem;}
    .ci-title {font-size:2.3rem; font-weight:750; margin-bottom:.2rem;}
    .ci-subtitle {color:#667085; margin-bottom:1.5rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

MODEL = "gemini-3.8-flash"


def get_secret(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return (value or os.getenv(name, "")).strip()


GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
TAVILY_API_KEY = get_secret("TAVILY_API_KEY")


def build_queries(company: str, industry: str, geography: str) -> list[str]:
    context = f"{company} {industry}".strip()
    geo = geography.strip() or "India"
    return [
        f"{context} competitors {geo}",
        f"{company} official products features {geo}",
        f"{company} official pricing plans {geo}",
        f"{company} latest news developments {geo}",
        f"{company} funding partnerships expansion {geo}",
        f"{company} customer reviews market feedback {geo}",
    ]


def search_tavily(client: TavilyClient, query: str, max_results: int = 5):
    return client.search(
        query=query,
        search_depth="advanced",
        max_results=max_results,
        include_answer=False,
        include_raw_content=False,
    )


def tavily_research(company: str, industry: str, geography: str, max_results: int = 5):
    """
    Uses a supplied Tavily API key when available.
    If the key is missing OR rejected, automatically falls back to Tavily's
    current keyless search mode for a free/demo experience.
    """
    authenticated = bool(TAVILY_API_KEY)
    client = TavilyClient(api_key=TAVILY_API_KEY) if authenticated else TavilyClient()

    all_results = []
    seen_urls = set()
    used_keyless = not authenticated

    for query in build_queries(company, industry, geography):
        try:
            result = search_tavily(client, query, max_results)
        except InvalidAPIKeyError:
            # A bad/expired key should not crash the whole app.
            # Tavily's current Python SDK supports keyless search mode.
            client = TavilyClient()
            used_keyless = True
            result = search_tavily(client, query, max_results)

        for item in result.get("results", []):
            url = item.get("url", "")
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)

            all_results.append(
