import os
import re
from datetime import datetime, timezone

import streamlit as st
from google import genai
from tavily import TavilyClient

st.set_page_config(
    page_title="AI Competitive Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {max-width: 1250px; padding-top: 2rem; padding-bottom: 3rem;}
    .ci-title {font-size: 2.3rem; font-weight: 750; margin-bottom: .2rem;}
    .ci-subtitle {color:#667085; margin-bottom:1.5rem;}
    .ci-card {border:1px solid rgba(128,128,128,.25); border-radius:12px; padding:1rem;}
    .muted {color:#667085; font-size:.86rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

MODEL = "gemini-2.5-flash"


def secret_or_env(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return value or os.getenv(name, "")


GEMINI_API_KEY = secret_or_env("GEMINI_API_KEY")
TAVILY_API_KEY = secret_or_env("TAVILY_API_KEY")


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


def tavily_research(company: str, industry: str, geography: str, max_results: int = 6):
    client = TavilyClient(api_key=TAVILY_API_KEY)
    all_results = []
    seen_urls = set()

    for query in build_queries(company, industry, geography):
        result = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=False,
            include_raw_content=False,
        )
        for item in result.get("results", []):
            url = item.get("url", "")
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            all_results.append(
                {
                    "query": query,
                    "title": item.get("title", ""),
                    "url": url,
                    "content": item.get("content", ""),
                    "published_date": item.get("published_date", ""),
                }
            )
    return all_results


def format_evidence(results: list[dict]) -> str:
    chunks = []
    for i, item in enumerate(results, start=1):
        chunks.append(
            f"""SOURCE {i}
Query: {item['query']}
Title: {item['title']}
URL: {item['url']}
Published: {item['published_date'] or 'Not available'}
Extract:
{item['content']}
"""
        )
    return "\n\n".join(chunks)


def build_analysis_prompt(
    company: str,
    industry: str,
    geography: str,
    competitor_count: int,
    evidence: str,
) -> str:
    today = datetime.now(timezone.utc).strftime("%d %b %Y")
    industry_text = industry.strip() or "Infer from evidence."
    geography_text = geography.strip() or "India"

    return f"""
You are an MBA strategy analyst preparing a competitive intelligence report.

TARGET COMPANY: {company}
INDUSTRY: {industry_text}
GEOGRAPHY: {geography_text}
REPORT DATE: {today}

Use ONLY the evidence supplied below. Do not use model memory to add current facts.

Your tasks:
1. Identify {competitor_count} relevant competitors.
2. Classify each as Direct, Indirect, or Emerging.
3. Compare decision-relevant features.
4. Compare publicly available pricing where evidence exists.
5. Summarise recent developments, prioritising the last 12 months.
6. Summarise customer/market signals only where evidence exists.
7. Produce evidence-backed strategic implications.

EVIDENCE RULES
- Never invent a price, feature, funding amount, date, partnership, customer, market share, or news item.
- "Not found" is NOT the same as "does not exist".
- For feature cells use ✓, ✕, or ?:
  ✓ = explicitly supported by supplied evidence
  ✕ = explicitly stated as unavailable/not offered
  ? = insufficient evidence
- For pricing, show currency, billing basis, geography, and last-checked date where available.
- Separate FACT from INTERPRETATION from HYPOTHESIS.
- Where evidence conflicts, state the conflict.
- Every material claim should include a source link using the URL supplied.
- Do not present a single overall winner or rank companies.
- Keep writing concise, professional, and suitable for an MBA/management audience.

OUTPUT EXACTLY THESE SECTIONS:

# Executive Summary
5-7 bullets.

# Company Snapshot
Markdown table with: Item | Finding

# Competitive Landscape
Markdown table with: Competitor | Type | Why it competes | Key evidence

# Feature Comparison
Create an 8-12 row comparison table. Columns:
Feature | {company} | Competitor 1 | Competitor 2 ... | Evidence note
Use ✓ / ✕ / ? only in company cells.

# Pricing Comparison
Markdown table:
Company | Plan | Price | Billing basis | Geography | Major inclusions | Last checked | Source

# Recent Developments
Up to 8 items. Table:
Date | Company | Development | Category | Business relevance | Source

# Customer / Market Signals
Use FACT / INTERPRETATION labels.

# Strategic Implications
5-7 evidence-backed observations or questions for management to investigate. Do not invent unsupported recommendations.

# Data Gaps
Important facts that could not be verified.

# Sources
Numbered list of the most important source titles with their direct URLs.

SUPPLIED WEB EVIDENCE:
{evidence}
"""


def analyse(company: str, industry: str, geography: str, competitor_count: int) -> tuple[str, int]:
    results = tavily_research(company, industry, geography)
    evidence = format_evidence(results)

    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = build_analysis_prompt(
        company, industry, geography, competitor_count, evidence
    )

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
    )
    return response.text or "No report was returned.", len(results)


def split_sections(report: str):
    matches = list(re.finditer(r"(?m)^# (.+)$", report))
    sections = []
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(report)
        sections.append((title, report[start:end].strip()))
    return sections


st.markdown('<div class="ci-title">📊 AI Competitive Intelligence</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="ci-subtitle">Research competitors, benchmark features and pricing, and surface recent market intelligence.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Research setup")
    company = st.text_input("Company / product", placeholder="e.g., Blue Tokai")
    industry = st.text_input("Industry (optional)", placeholder="e.g., Specialty coffee")
    geography = st.text_input("Geography", value="India")
    competitor_count = st.slider("Competitors", 3, 7, 5)

    st.divider()
    run = st.button("🚀 Run intelligence", type="primary", use_container_width=True)
    clear = st.button("Clear report", use_container_width=True)

if clear:
    st.session_state.pop("report", None)
    st.session_state.pop("meta", None)
    st.rerun()

if not GEMINI_API_KEY or not TAVILY_API_KEY:
    st.warning("Add both API keys to Streamlit Secrets before running the agent.")
    st.code(
        'GEMINI_API_KEY = "your-gemini-key"\n'
        'TAVILY_API_KEY = "your-tavily-key"',
        language="toml",
    )

if run:
    if not company.strip():
        st.error("Enter a company or product.")
    elif not GEMINI_API_KEY:
        st.error("GEMINI_API_KEY is missing.")
    elif not TAVILY_API_KEY:
        st.error("TAVILY_API_KEY is missing.")
    else:
        with st.status("Researching the competitive landscape...", expanded=True) as status:
            st.write("Searching competitor, product, pricing, news and customer-signal sources...")
            try:
                report, source_count = analyse(
                    company.strip(),
                    industry.strip(),
                    geography.strip(),
                    competitor_count,
                )
                st.session_state["report"] = report
                st.session_state["meta"] = {
                    "company": company.strip(),
                    "source_count": source_count,
                    "generated_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
                }
                status.update(label="Research completed", state="complete", expanded=False)
            except Exception as exc:
                status.update(label="Research failed", state="error", expanded=True)
                st.exception(exc)

report = st.session_state.get("report")

if report:
    meta = st.session_state.get("meta", {})
    st.success(
        f"Report ready for {meta.get('company', 'company')} · "
        f"{meta.get('source_count', 0)} unique web sources reviewed."
    )

    sections = split_sections(report)
    lookup = {title.lower(): body for title, body in sections}

    labels = [
        "Executive Summary",
        "Company Snapshot",
        "Competitive Landscape",
        "Feature Comparison",
        "Pricing Comparison",
        "Recent Developments",
        "Customer / Market Signals",
        "Strategic Implications",
        "Data Gaps",
        "Sources",
    ]

    tabs = st.tabs(labels)
    for tab, label in zip(tabs, labels):
        with tab:
            body = lookup.get(label.lower())
            if body:
                st.markdown(body)
            else:
                st.info("This section was not returned.")

    st.divider()
    c1, c2 = st.columns(2)
    filename_base = re.sub(r"[^A-Za-z0-9_-]+", "_", meta.get("company", "company")).strip("_")
    with c1:
        st.download_button(
            "⬇️ Download Markdown",
            data=report,
            file_name=f"{filename_base}_competitive_intelligence.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "⬇️ Download TXT",
            data=report,
            file_name=f"{filename_base}_competitive_intelligence.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.caption(
        f"Generated {meta.get('generated_at', '')}. "
        "Current information can change; verify important decisions against the linked sources."
    )
else:
    st.info(
        "Enter a company in the sidebar. Example: **Blue Tokai** → Industry: **Specialty coffee** → Geography: **India**."
    )

with st.expander("How the agent works"):
    st.markdown(
        """
        **1. Tavily** runs focused web searches for competitors, products/features, pricing, news,
        partnerships and customer/market signals.

        **2. Gemini** receives the collected evidence and turns it into a structured competitive
        intelligence report.

        **3. Streamlit** presents the report in tabs and lets you download it.

        The app does not store API keys in code and asks the model to mark unsupported information as
        unavailable instead of guessing.
        """
    )
