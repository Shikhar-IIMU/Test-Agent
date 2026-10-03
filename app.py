import re
from collections import Counter
from datetime import datetime, timedelta

import streamlit as st
from ddgs import DDGS
from ddgs.exceptions import DDGSException, TimeoutException, RatelimitException

st.set_page_config(
    page_title="Zero-Key Competitive Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {max-width: 1250px; padding-top: 2rem; padding-bottom: 3rem;}
    .title {font-size: 2.25rem; font-weight: 750; margin-bottom: .25rem;}
    .subtitle {color: #667085; margin-bottom: 1.5rem;}
    .card {border:1px solid rgba(128,128,128,.25); border-radius:12px; padding:1rem;}
    .muted {color:#667085; font-size:.85rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

SEARCH_REGION = "in-en"


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()


def ddg_search(query: str, max_results: int = 8, timelimit: str | None = None):
    """Keyless public-web search with fallback backends and timeout handling."""
    for backend in ["google,bing,brave", "bing,yahoo", "google", "wikipedia"]:
        try:
            return list(
                DDGS(timeout=12).text(
                    query,
                    region=SEARCH_REGION,
                    safesearch="moderate",
                    timelimit=timelimit,
                    max_results=max_results,
                    backend=backend,
                )
            )
        except (TimeoutException, RatelimitException, DDGSException):
            continue
        except Exception:
            continue
    return []


def ddg_news(query: str, max_results: int = 8):
    """Keyless news search with fallback backends and timeout handling."""
    for backend in ["bing,yahoo", "bing", "yahoo"]:
        try:
            return list(
                DDGS(timeout=12).news(
                    query,
                    region=SEARCH_REGION,
                    safesearch="moderate",
                    timelimit="y",
                    max_results=max_results,
                    backend=backend,
                )
            )
        except (TimeoutException, RatelimitException, DDGSException):
            continue
        except Exception:
            continue
    return []

def domain_of(url: str) -> str:
    match = re.search(r"https?://(?:www\.)?([^/]+)", url or "")
    return match.group(1) if match else ""


def dedupe(results):
    seen = set()
    output = []
    for r in results:
        url = r.get("href") or r.get("url") or ""
        title = clean_text(r.get("title", ""))
        key = url.lower() or title.lower()
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(
            {
                "title": title,
                "url": url,
                "body": clean_text(r.get("body", "")),
