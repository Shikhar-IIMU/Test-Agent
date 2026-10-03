import re
from collections import Counter
from datetime import datetime

import streamlit as st
from ddgs import DDGS
from ddgs.exceptions import DDGSException, RatelimitException, TimeoutException

st.set_page_config(
    page_title="Zero-Key Competitive Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {max-width:1250px; padding-top:2rem; padding-bottom:3rem;}
    .title {font-size:2.25rem; font-weight:750; margin-bottom:.25rem;}
    .subtitle {color:#667085; margin-bottom:1.5rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

SEARCH_REGION = "in-en"


def clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def text_search(query, max_results=6):
    # Avoid backend="auto": on Streamlit Cloud that can route to
    # html.duckduckgo.com and cause the timeout seen in the previous version.
    for backend in ["bing", "brave", "yahoo", "google", "wikipedia"]:
        try:
            return list(
                DDGS(timeout=10).text(
                    query,
                    region=SEARCH_REGION,
                    safesearch="moderate",
                    max_results=max_results,
                    backend=backend,
                )
            )
        except (TimeoutException, RatelimitException, DDGSException):
            continue
        except Exception:
            continue
    return []


def news_search(query, max_results=8):
    for backend in ["bing", "yahoo", "brave"]:
        try:
            return list(
                DDGS(timeout=10).news(
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


def normalize(item):
    return {
        "title": clean_text(item.get("title")),
        "url": item.get("href") or item.get("url") or "",
        "body": clean_text(item.get("body") or item.get("snippet")),
        "date": clean_text(item.get("date")),
    }


def dedupe(items):
    result = []
    seen = set()

    for raw in items:
        item = normalize(raw)
        key = item["url"].lower() or item["title"].lower()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)

    return result
