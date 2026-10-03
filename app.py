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
