import re
from collections import Counter
from datetime import datetime, timedelta

import streamlit as st
from ddgs import DDGS

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
    """Keyless public-web search using DDGS."""
    return list(
        DDGS().text(
            query,
            region=SEARCH_REGION,
            safesearch="moderate",
            timelimit=timelimit,
            max_results=max_results,
            backend="auto",
        )
    )


def ddg_news(query: str, max_results: int = 8):
    return list(
        DDGS().news(
            query,
            region=SEARCH_REGION,
            safesearch="moderate",
            timelimit="y",
            max_results=max_results,
            backend="auto",
        )
    )


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
                "date": clean_text(r.get("date", "")),
                "source": clean_text(r.get("source", "")) or domain_of(url),
            }
        )
    return output


def discover_competitors(company: str, industry: str, geography: str, count: int):
    queries = [
        f'"{company}" competitors {industry} {geography}'.strip(),
        f'alternatives to "{company}" {industry} {geography}'.strip(),
        f'{company} vs competitors {industry} {geography}'.strip(),
    ]
    results = dedupe([r for q in queries for r in ddg_search(q, 8)])

    stop = {
        company.lower(),
        "company",
        "competitor",
        "competitors",
        "alternative",
        "alternatives",
        "india",
        "indian",
    }

    name_counts = Counter()
    evidence = {}
    for r in results:
        blob = f"{r['title']} {r['body']}"
        # Extract likely capitalised company/product names from titles/snippets.
        candidates = re.findall(
            r"\b(?:[A-Z][A-Za-z0-9&.'-]{1,}\s+){0,3}[A-Z][A-Za-z0-9&.'-]{1,}\b",
            r["title"],
        )
        for candidate in candidates:
            candidate = clean_text(candidate).strip(" -|:")
            low = candidate.lower()
            if low in stop or company.lower() in low:
                continue
            if len(candidate) < 3 or len(candidate) > 45:
                continue
            name_counts[candidate] += 1
            evidence.setdefault(candidate, []).append(r)

    # Common competitor-list phrases are often cleaner than generic named entities.
    phrase_candidates = []
    for r in results:
        text = f"{r['title']} {r['body']}"
        for pattern in [
            r"(?:competitors?|alternatives?)\s*(?:include|are|:)\s*([^.;|]+)",
            r"(?:compared with|vs\.?|versus)\s*([^.;|]+)",
        ]:
            m = re.search(pattern, text, flags=re.I)
            if m:
                phrase_candidates.extend(
                    [clean_text(x) for x in re.split(r",| and | \| ", m.group(1))]
                )

    for c in phrase_candidates:
        low = c.lower()
        if 2 < len(c) < 45 and company.lower() not in low and low not in stop:
            name_counts[c] += 2
            evidence.setdefault(c, []).extend(results[:2])

    ranked = name_counts.most_common()
    competitors = []
    for name, score in ranked:
        # Filter obvious non-business fragments.
        if any(x in name.lower() for x in ["best ", "top ", "list of", "guide to", "what is "]):
            continue
        competitors.append(
            {
                "name": name,
                "type": "Potential direct/indirect competitor",
                "signal": score,
                "evidence": evidence.get(name, [])[:2],
            }
        )
        if len(competitors) >= count:
            break

    return competitors, results


def extract_prices(text: str):
    patterns = [
        r"(?:₹|Rs\.?|INR)\s?[0-9][0-9,]*(?:\.[0-9]+)?(?:\s*(?:/\s*)?(?:month|mo|year|yr|day|meal|user|seat))?",
        r"\$\s?[0-9][0-9,]*(?:\.[0-9]+)?(?:\s*(?:/\s*)?(?:month|mo|year|yr|day|user|seat))?",
        r"(?:from|starting at|starts at)\s+(?:₹|Rs\.?|INR|\$)?\s?[0-9][0-9,]*(?:\.[0-9]+)?",
    ]
    found = []
    for p in patterns:
        found.extend(re.findall(p, text, flags=re.I))
    # Keep short unique values.
    output = []
    for x in found:
        x = clean_text(x)
        if x.lower() not in [y.lower() for y in output]:
            output.append(x)
    return output[:5]


def research_company(company: str, industry: str, geography: str, competitor_count: int):
    queries = [
        f'"{company}" official website {industry}',
        f'"{company}" pricing plans {geography}',
        f'"{company}" products features {geography}',
        f'"{company}" customer reviews {geography}',
    ]

    core = dedupe([r for q in queries for r in ddg_search(q, 6)])
    news = dedupe(ddg_news(f"{company} latest news {geography}", 8))

    competitors, comp_search = discover_competitors(
        company, industry, geography, competitor_count
    )

    all_evidence = dedupe(core + comp_search)

    return {
        "core": core,
        "news": news,
        "competitors": competitors,
        "all": all_evidence,
    }


def make_feature_signals(company: str, evidence):
    feature_keywords = [
        "mobile app", "web app", "subscription", "free plan", "premium",
        "rewards", "delivery", "analytics", "API", "integration", "financing",
        "loans", "insurance", "marketplace", "membership", "personalisation",
        "AI", "artificial intelligence", "customer support", "offline store",
    ]

    rows = []
    for feature in feature_keywords:
        hits = [
            r for r in evidence
            if feature.lower() in f"{r['title']} {r['body']}".lower()
        ]
        status = "✓" if hits else "?"
        note = (
            f"Found in {len(hits)} web result(s); verify against the source."
            if hits
            else "Insufficient public evidence in the current search."
        )
        rows.append((feature, status, note))

    return rows


def make_markdown_report(company, industry, geography, data):
    generated = datetime.now().strftime("%d %b %Y, %I:%M %p")
    price_rows = []
    for r in data["core"]:
        prices = extract_prices(f"{r['title']} {r['body']}")
        for p in prices:
            price_rows.append((p, r["title"], r["url"]))

    lines = [
        "# Executive Summary",
        f"- Target: **{company}** | Geography: **{geography or 'India'}** | Generated: {generated}",
        f"- Potential competitors surfaced from current web search: **{len(data['competitors'])}**.",
        "- Pricing observations below are extracted from public search results and should be verified on the linked source page.",
        "- Feature marks use `✓` only when a search result explicitly mentions the feature; `?` means insufficient evidence.",
        "- Recent developments are based on news-search results from the last year.",
        "",
        "# Company Snapshot",
        "| Item | Finding |",
        "|---|---|",
        f"| Company | {company} |",
        f"| Industry | {industry or 'Inferred from search context'} |",
        f"| Geography | {geography or 'India'} |",
        f"| Web sources reviewed | {len(data['all'])} |",
        "",
        "# Competitive Landscape",
        "| Competitor surfaced | Signal | Evidence |",
        "|---|---:|---|",
    ]

    for c in data["competitors"]:
        evidence_url = c["evidence"][0]["url"] if c["evidence"] else ""
        lines.append(f"| {c['name']} | {c['signal']} | {evidence_url} |")

    lines += [
        "",
        "# Feature Signals",
        "| Feature | Target company | Evidence note |",
        "|---|:---:|---|",
    ]
    for feature, status, note in make_feature_signals(company, data["all"]):
        lines.append(f"| {feature} | {status} | {note} |")

    lines += [
        "",
        "# Pricing Signals",
        "| Observed price | Search result | Source |",
        "|---|---|---|",
    ]
    for price, title, url in price_rows[:15]:
        lines.append(f"| {price} | {title} | {url} |")
    if not price_rows:
        lines.append("| Insufficient public evidence | | |")

    lines += [
        "",
        "# Recent Developments",
        "| Date | Headline | Source |",
        "|---|---|---|",
    ]
    for r in data["news"][:8]:
        lines.append(f"| {r['date'] or 'Date not shown'} | {r['title']} | {r['url']} |")

    lines += [
        "",
        "# Strategic Implications",
        "- Which competitor appears repeatedly across current search results?",
        "- Which features have clear public evidence and which still require verification?",
        "- Which pricing claims are sourced directly enough to support a pricing benchmark?",
        "- Which recent developments could materially change the competitive landscape?",
        "",
        "# Data Gaps",
        "- Public search results may not reveal negotiated enterprise pricing, internal product roadmaps, or complete feature matrices.",
        "- Search-engine snippets can be incomplete or outdated; verify high-stakes claims on the source page.",
        "",
        "# Sources",
    ]
    for i, r in enumerate(data["all"][:25], start=1):
        lines.append(f"{i}. {r['title']} — {r['url']}")

    return "\n".join(lines)


st.markdown('<div class="title">📊 Zero-Key Competitive Intelligence</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">No Gemini key. No OpenAI key. No Tavily key. Uses public web search and deterministic analysis.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Research setup")
    company = st.text_input("Company / product", placeholder="e.g., Blue Tokai")
    industry = st.text_input("Industry (optional)", placeholder="e.g., Specialty coffee")
    geography = st.text_input("Geography", value="India")
    competitor_count = st.slider("Competitors", 3, 7, 5)
    run = st.button("🚀 Run intelligence", type="primary", use_container_width=True)

if run:
    if not company.strip():
        st.error("Enter a company or product.")
    else:
        with st.status("Searching the public web...", expanded=True) as status:
            try:
                data = research_company(
                    company.strip(),
                    industry.strip(),
                    geography.strip(),
                    competitor_count,
                )
                st.session_state["data"] = data
                st.session_state["company"] = company.strip()
                st.session_state["industry"] = industry.strip()
                st.session_state["geography"] = geography.strip()
                st.session_state["generated"] = datetime.now().strftime("%d %b %Y, %I:%M %p")
                status.update(label="Research completed", state="complete", expanded=False)
            except Exception as exc:
                status.update(label="Search failed", state="error", expanded=True)
                st.exception(exc)

data = st.session_state.get("data")
if data:
    company = st.session_state["company"]
    industry = st.session_state["industry"]
    geography = st.session_state["geography"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Potential competitors", len(data["competitors"]))
    m2.metric("Web sources", len(data["all"]))
    m3.metric("News results", len(data["news"]))
    m4.metric("Pricing signals", sum(len(extract_prices(f"{r['title']} {r['body']}")) for r in data["core"]))

    tabs = st.tabs([
        "Executive Summary",
        "Competitors",
        "Features",
        "Pricing",
        "News",
        "Sources",
    ])

    with tabs[0]:
        st.markdown("### Executive Summary")
        st.write(
            f"This report uses current public search results for **{company}** in **{geography or 'India'}**."
        )
        st.write(
            "The system is evidence-first: search signals are shown with source links, and missing evidence is marked as `?` rather than treated as proof of absence."
        )
        st.markdown("### Key observations to investigate")
        for item in [
            f"{len(data['competitors'])} potential competitor names were surfaced.",
            f"{len(data['news'])} recent news results were collected.",
            "Pricing observations are extracted from public search snippets and should be verified on the source page.",
            "Feature signals indicate where public evidence exists, not a complete product audit.",
        ]:
            st.markdown(f"- {item}")

    with tabs[1]:
        st.markdown("### Competitive Landscape")
        if data["competitors"]:
            st.dataframe(
                [
                    {
                        "Competitor surfaced": c["name"],
                        "Search signal": c["signal"],
                        "Evidence": c["evidence"][0]["url"] if c["evidence"] else "",
                    }
                    for c in data["competitors"]
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No competitor names could be surfaced reliably. Try a more specific company name.")

    with tabs[2]:
        st.markdown("### Feature Signals")
        st.dataframe(
            [
                {"Feature": f, "Evidence": s, "Note": n}
                for f, s, n in make_feature_signals(company, data["all"])
            ],
            use_container_width=True,
            hide_index=True,
        )

    with tabs[3]:
        rows = []
        for r in data["core"]:
            for price in extract_prices(f"{r['title']} {r['body']}"):
                rows.append({"Observed price": price, "Result": r["title"], "Source": r["url"]})
        st.markdown("### Public Pricing Signals")
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No public price signal was detected in the current search.")

    with tabs[4]:
        st.markdown("### Recent Developments")
        st.dataframe(
            [
                {
                    "Date": r["date"] or "Date not shown",
                    "Headline": r["title"],
                    "Source": r["url"],
                }
                for r in data["news"][:10]
            ],
            use_container_width=True,
            hide_index=True,
        )

    with tabs[5]:
        st.markdown("### Sources used")
        for i, r in enumerate(data["all"][:30], start=1):
            st.markdown(f"**{i}. {r['title']}**  \n{r['url']}")

    report = make_markdown_report(company, industry, geography, data)
    st.download_button(
        "⬇️ Download full Markdown report",
        report,
        file_name=re.sub(r"[^A-Za-z0-9_-]+", "_", company).strip("_") + "_competitive_intelligence.md",
        mime="text/markdown",
        use_container_width=True,
    )

else:
    st.info(
        "Enter a company and click **Run intelligence**. Example: Blue Tokai → Specialty coffee → India."
    )

with st.expander("What makes this zero-key?"):
    st.write(
        "The app does not call Gemini, OpenAI, Tavily, or another paid API. "
        "It uses the keyless DDGS public web-search library and performs the feature, pricing, "
        "competitor-signal and report generation locally in Python."
    )
