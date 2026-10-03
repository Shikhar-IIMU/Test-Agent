# Competitive Intelligence Streamlit App

## What changed in the overhaul

- Removed the DDGS dependency that was timing out on `html.duckduckgo.com`.
- No API keys or secrets are required.
- No network request is made during app startup.
- Added concurrent web research with hard request timeouts.
- Added Bing / Google / Google News public search endpoints.
- Added automatic demo fallback when live search is unavailable.
- Added a complete UX shell: hero, setup sidebar, metrics, tabs, source cards and downloadable report.
- Added a visible method + UX rubric inside the app.

## Files

```text
app.py
requirements.txt
README.md
```

## Deploy

Upload these three files to GitHub and deploy `app.py` with Streamlit Community Cloud.

No Secrets are required.

## First test

Use:

```text
Company: Blue Tokai
Industry: Specialty coffee
Geography: India
```

Or click **Load demo** to verify the interface before making any web requests.

## UX / QA rubric

100 points total:

- App startup reliability: 20
- Interaction flow: 15
- Resilience: 20
- Visual hierarchy: 15
- Data trust: 15
- Deployment simplicity: 10
- Portfolio readiness: 5

Target: 100/100.
