Zero-Key Competitive Intelligence Agent
A Streamlit competitive-intelligence MVP that requires no API key.
Stack
Streamlit frontend
DDGS keyless public web search
Python deterministic analysis
Markdown export
The app searches the public web for competitors, product/features, pricing, reviews and recent news.
It then produces structured tables and an evidence-linked report.
Deploy
Upload:
```text
app.py
requirements.txt
README.md
```
to GitHub, then deploy `app.py` on Streamlit Community Cloud.
No Secrets are required.
Test
```text
Company: Blue Tokai
Industry: Specialty coffee
Geography: India
Competitors: 5
```
Important limitation
This version deliberately avoids paid/private LLM APIs. It is therefore an AI-assisted research
workflow using keyless search + local extraction/analysis, not a generative LLM chatbot.
Search results can be incomplete, and price/feature snippets should be verified on source pages.
