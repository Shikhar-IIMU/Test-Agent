import html
import re
import textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import quote_plus, urljoin

import requests
import streamlit as st
from bs4 import BeautifulSoup

# -------------------------------------------------------------------
# Page + theme
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Competitive Intelligence",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #111827;
        --muted: #667085;
        --line: #E5E7EB;
        --soft: #F8FAFC;
        --panel: #FFFFFF;
        --accent: #2563EB;
        --accent-soft: #EFF6FF;
        --success: #15803D;
        --warning: #B45309;
    }

    .stApp {
        background: #F7F8FA;
    }

    .block-container {
        max-width: 1280px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    [data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid var(--line);
    }

    .hero {
        background: linear-gradient(135deg, #0F172A 0%, #172554 100%);
        color: white;
        border-radius: 18px;
        padding: 28px 30px;
        margin-bottom: 22px;
        box-shadow: 0 10px 35px rgba(15, 23, 42, .10);
    }

    .hero h1 {
        margin: 0 0 8px 0;
        font-size: 2.35rem;
        line-height: 1.05;
        letter-spacing: -0.04em;
    }

    .hero p {
        margin: 0;
        max-width: 820px;
        color: #CBD5E1;
        font-size: 1rem;
        line-height: 1.55;
    }

    .pill {
        display: inline-block;
        margin: 0 7px 8px 0;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(255,255,255,.10);
        border: 1px solid rgba(255,255,255,.15);
        color: #E2E8F0;
        font-size: .78rem;
        font-weight: 600;
    }

    .section-title {
        color: var(--ink);
        font-size: 1.12rem;
        font-weight: 750;
        margin: 6px 0 10px;
    }

    .section-note {
        color: var(--muted);
