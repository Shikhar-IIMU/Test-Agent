import re
from datetime import datetime, timezone

import streamlit as st
from openai import OpenAI

APP_TITLE = "AI Competitive Intelligence"
DEFAULT_MODEL = "gpt-5.6-luna"


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container {padding-top: 2rem; padding-bottom: 3rem;}
        .ci-title {font-size: 2.25rem; font-weight: 750; margin-bottom: 0.2rem;}
        .ci-subtitle {color: #6b7280; font-size: 1rem; margin-bottom: 1.5rem;}
        .metric-card {
            border: 1px solid rgba(128,128,128,0.25);
            border-radius: 12px;
            padding: 1rem;
            min-height: 95px;
        }
        .small-muted {color: #6b7280; font-size: 0.85rem;}
        .source-box {
            border-left: 3px solid #888;
            padding-left: 0.8rem;
            margin: 0.45rem 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_api_key() -> str:
    """Read the OpenAI key from Streamlit secrets first, then environment variables."""
    try:
        key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        key = ""
    return key or os.getenv("OPENAI_API_KEY", "")


def build_prompt(company: str, industry: str, geography: str, competitor_count: int) -> str:
    checked_on = datetime.now(timezone.utc).strftime("%d %b %Y")
    industry_text = industry.strip() or "Infer the industry from current public evidence."
    geography_text = geography.strip() or "India"

    return f"""
You are an MBA strategy analyst preparing a current competitive intelligence brief.

Company to analyse:
{company}

Industry:
{industry_text}

Geography:
{geography_text}

Research date:
{checked_on}

Identify {competitor_count} meaningful competitors. Classify each as Direct, Indirect, or Emerging.

Research using the web. Prefer primary sources for company facts, product pages, official pricing pages,
regulatory filings, investor relations pages, and direct company announcements. Use reputable news sources
for recent developments. Do not rely on model memory for current facts.

STRICT EVIDENCE RULES
- Never invent pricing, features, customers, market share, funding, partnerships, or news.
- If a fact cannot be verified publicly, write "Insufficient public evidence."
- "Not found" is NOT the same as "does not exist."
- For feature comparisons, use:
  ✓ = explicitly supported by evidence
  ✕ = explicitly stated as unavailable/not offered
  ? = insufficient evidence
- Clearly distinguish FACT from INTERPRETATION and HYPOTHESIS.
- Every material current claim should have a source.
- Use absolute dates for recent developments.
- Pricing must include currency, billing period, geography where relevant, and "last checked" date.

OUTPUT FORMAT

# Executive Summary
Write 5-7 concise bullets. Cover the competitive landscape, important differences, pricing observations,
recent strategic moves, and areas that deserve management attention. Do not rank a "winner".

# Company Snapshot
| Item | Finding |
|---|---|
| Company | |
| Industry | |
| Business model | |
| Target customers | |
| Core products/services | |
| Geography | |

# Competitive Landscape
| Competitor | Type | Why it competes | Evidence |
|---|---|---|---|

# Feature Comparison
Build a comparison table with 8-12 decision-relevant features.
Use ✓, ✕, or ? only, and add a short "Evidence note" column.

# Pricing Comparison
Use the most decision-relevant publicly available plans.
Columns: Company, Plan, Price, Billing basis, Geography, Major inclusions, Last checked, Source

# Recent Developments
Provide up to 8 relevant developments from the last 12 months.
Columns: Date, Company, Development, Category, Business relevance, Source

# Customer / Market Signals
Summarise recurring customer or market themes only when supported by reliable public evidence.
Separate FACTS from INTERPRETATION.

# Strategic Implications
Provide 5-7 implications to investigate. Phrase them as business questions or evidence-backed observations,
not as unsupported recommendations.

# Data Gaps
List important facts that could not be verified.

# Sources
Provide a clean numbered list of the key sources with title + direct URL.

Tone:
Professional MBA / consulting style, concise, plain English, human and decision-oriented.
Do not use generic filler.
"""


def run_research(company: str, industry: str, geography: str, competitor_count: int, model: str) -> str:
    client = OpenAI(api_key=get_api_key())
    prompt = build_prompt(company, industry, geography, competitor_count)

    response = client.responses.create(
        model=model,
        tools=[{"type": "web_search"}],
        input=prompt,
    )
    return response.output_text or "No report was returned."


def split_report(report: str):
    """Best-effort section extraction for a cleaner Streamlit UI."""
    pattern = r"(?m)^# (.+)$"
    matches = list(re.finditer(pattern, report))
    sections = []
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(report)
        body = report[start:end].strip()
        sections.append((title, body))
    return sections


# Header
st.markdown('<div class="ci-title">📊 AI Competitive Intelligence</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="ci-subtitle">Competitor discovery, feature benchmarking, pricing intelligence and recent developments.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Research setup")
    company = st.text_input(
        "Company / product",
        placeholder="e.g., Blue Tokai",
        help="Enter a company or a specific product/category.",
    )
    industry = st.text_input(
        "Industry (optional)",
        placeholder="e.g., Specialty coffee",
    )
    geography = st.text_input(
        "Geography",
        value="India",
        help="Use a country, region or market such as India, Southeast Asia, or US.",
    )
    competitor_count = st.slider("Competitors", min_value=3, max_value=7, value=5)
    model = st.selectbox("Model", [DEFAULT_MODEL], index=0)

    st.divider()
    st.caption(
        "Evidence-first research. Current information is searched on the web and the report is dated."
    )

    run_button = st.button("🚀 Run intelligence", type="primary", use_container_width=True)

    if st.button("Clear report", use_container_width=True):
        st.session_state.pop("report", None)
        st.session_state.pop("meta", None)
        st.rerun()


if not get_api_key():
    st.warning(
        "Add OPENAI_API_KEY in Streamlit Secrets before running the agent. "
        "Never commit the API key to GitHub."
    )
    st.code('OPENAI_API_KEY = "your-key-here"', language="toml")

if run_button:
    if not company.strip():
        st.error("Please enter a company or product.")
    elif not get_api_key():
        st.error("OPENAI_API_KEY is not configured.")
    else:
        with st.spinner("Researching competitors, pricing, features and recent developments..."):
            try:
                report = run_research(
                    company=company,
                    industry=industry,
                    geography=geography,
                    competitor_count=competitor_count,
                    model=model,
                )
                st.session_state["report"] = report
                st.session_state["meta"] = {
                    "company": company.strip(),
                    "geography": geography.strip() or "India",
                    "generated_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
                }
            except Exception as exc:
                st.error(f"The research run failed: {exc}")
                st.stop()


report = st.session_state.get("report")

if report:
    meta = st.session_state.get("meta", {})
    st.success(f"Research completed for {meta.get('company', 'company')}.")

    sections = split_report(report)
    section_names = {title.lower(): body for title, body in sections}

    # Top-level navigation
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
            body = section_names.get(label.lower(), "")
            if body:
                st.markdown(body)
            else:
                st.info("This section was not returned by the research run.")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️ Download Markdown report",
            data=report,
            file_name=f"{meta.get('company', 'competitor_report').replace(' ', '_')}_competitive_intelligence.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "⬇️ Download text report",
            data=report,
            file_name=f"{meta.get('company', 'competitor_report').replace(' ', '_')}_competitive_intelligence.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.caption(
        f"Generated: {meta.get('generated_at', '')} | Geography: {meta.get('geography', '')}"
    )
else:
    st.info(
        "Enter a company in the left panel and click **Run intelligence** to generate the first report."
    )

with st.expander("How this MVP works"):
    st.write(
        "The app sends a structured research brief to the OpenAI Responses API with the built-in web search "
        "tool enabled. The model researches current public information and returns a standardised competitive "
        "intelligence report. The UI then presents the report as tabs and provides downloads."
    )
