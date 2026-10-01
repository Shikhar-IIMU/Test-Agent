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
                {
                    "query": query,
                    "title": item.get("title", ""),
                    "url": url,
                    "content": item.get("content", ""),
                    "published_date": item.get("published_date", ""),
                }
            )

    return all_results, used_keyless


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


def build_prompt(company, industry, geography, competitor_count, evidence):
    report_date = datetime.now(timezone.utc).strftime("%d %b %Y")
    return f"""
You are an MBA strategy analyst preparing a current competitive intelligence report.

TARGET COMPANY: {company}
INDUSTRY: {industry or "Infer from the evidence"}
GEOGRAPHY: {geography or "India"}
REPORT DATE: {report_date}

Use ONLY the supplied evidence. Do not add current facts from model memory.

Identify {competitor_count} relevant competitors and classify them as Direct, Indirect or Emerging.

EVIDENCE RULES
- Never invent prices, features, dates, funding, partnerships, customers, market share or news.
- "Not found" is NOT the same as "does not exist".
- Feature comparison cells:
  ✓ = explicitly supported
  ✕ = explicitly stated unavailable/not offered
  ? = insufficient evidence
- Pricing must include currency, billing basis, geography and last checked date when available.
- Separate FACT, INTERPRETATION and HYPOTHESIS.
- When evidence conflicts, state the conflict.
- Include source URLs for material claims.
- Do not produce an overall winner or rank companies.

OUTPUT:

# Executive Summary
5-7 concise bullets.

# Company Snapshot
Table: Item | Finding

# Competitive Landscape
Table: Competitor | Type | Why it competes | Key evidence

# Feature Comparison
8-12 decision-relevant features. Columns:
Feature | Target company | Competitor 1 | Competitor 2 ... | Evidence note

# Pricing Comparison
Table:
Company | Plan | Price | Billing basis | Geography | Major inclusions | Last checked | Source

# Recent Developments
Up to 8 recent developments, prioritising the last 12 months.
Table:
Date | Company | Development | Category | Business relevance | Source

# Customer / Market Signals
Clearly label FACT and INTERPRETATION.

# Strategic Implications
5-7 evidence-backed observations or questions for management to investigate.

# Data Gaps
List important facts that could not be verified.

# Sources
Numbered list of important source titles and direct URLs.

Keep the report concise, professional, human and suitable for an MBA/management audience.

SUPPLIED WEB EVIDENCE:
{evidence}
"""


def analyse(company, industry, geography, competitor_count):
    results, used_keyless = tavily_research(company, industry, geography)
    if not results:
        raise RuntimeError(
            "No web results were returned. Try a broader company name or add a valid Tavily API key."
        )

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=MODEL,
        contents=build_prompt(
            company,
            industry,
            geography,
            competitor_count,
            format_evidence(results),
        ),
    )
    return response.text or "No report was returned.", len(results), used_keyless


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
    '<div class="ci-subtitle">Competitor discovery, feature benchmarking, pricing intelligence and recent developments.</div>',
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

    if TAVILY_API_KEY:
        st.caption("Tavily key detected. The app will use it and fall back to keyless search if it is rejected.")
    else:
        st.caption("No Tavily key detected. The app will use Tavily's rate-limited keyless search mode.")

if not GEMINI_API_KEY:
    st.warning("Add your Gemini API key in Streamlit Secrets.")
    st.code('GEMINI_API_KEY = "your-gemini-key"', language="toml")

if run:
    if not company.strip():
        st.error("Enter a company or product.")
    elif not GEMINI_API_KEY:
        st.error("GEMINI_API_KEY is missing.")
    else:
        with st.status("Researching the competitive landscape...", expanded=True) as status:
            st.write("Searching competitors, features, pricing, news and market signals...")
            try:
                report, source_count, used_keyless = analyse(
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
                    "used_keyless": used_keyless,
                }

                status.update(
                    label="Research completed",
                    state="complete",
                    expanded=False,
                )
            except Exception as exc:
                status.update(
                    label="Research failed",
                    state="error",
                    expanded=True,
                )
                st.exception(exc)

report = st.session_state.get("report")

if report:
    meta = st.session_state.get("meta", {})
    if meta.get("used_keyless"):
        st.info(
            "Tavily API key was not used. The app successfully used Tavily's "
            "rate-limited keyless search mode. Adding a valid Tavily key gives you higher limits."
        )
    else:
        st.success(
            f"Report ready for {meta.get('company', 'company')} · "
            f"{meta.get('source_count', 0)} unique web sources reviewed."
        )

    lookup = {title.lower(): body for title, body in split_sections(report)}

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
            st.markdown(body or "This section was not returned.")

    st.divider()
    base = re.sub(r"[^A-Za-z0-9_-]+", "_", meta.get("company", "company")).strip("_")

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "⬇️ Download Markdown",
            report,
            file_name=f"{base}_competitive_intelligence.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "⬇️ Download TXT",
            report,
            file_name=f"{base}_competitive_intelligence.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.caption(
        f"Generated {meta.get('generated_at', '')}. Current information can change; "
        "verify important decisions against linked sources."
    )
else:
    st.info(
        "Enter a company in the sidebar. Example: Blue Tokai → Specialty coffee → India."
    )

with st.expander("How the agent works"):
    st.markdown(
        """
        **Tavily** searches current public web sources. If a supplied Tavily key is
        rejected, the app automatically retries using Tavily's keyless search mode.

        **Gemini** synthesises the retrieved evidence into a structured competitive
        intelligence report.

        **Streamlit** provides the dashboard and downloads.
        """
    )
