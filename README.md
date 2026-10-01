# AI Competitive Intelligence Agent

A simple Streamlit MVP for MBA students and business teams.

## What it does

Enter a company/product and the app researches:

- company snapshot
- competitors
- feature comparison
- pricing
- recent developments
- customer/market signals
- strategic implications
- data gaps
- sources

It uses the OpenAI Responses API with web search.

## Files

```text
competitor_intelligence_agent/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── .streamlit/
    └── config.toml
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Create `.streamlit/secrets.toml` locally:

```toml
OPENAI_API_KEY = "your-api-key"
```

Do NOT commit `secrets.toml`.

## Deploy on Streamlit Community Cloud

1. Upload these files to a GitHub repository.
2. Go to Streamlit Community Cloud and create an app.
3. Select your GitHub repository, branch and `app.py`.
4. Open Advanced settings -> Secrets.
5. Paste:

```toml
OPENAI_API_KEY = "your-api-key"
```

6. Deploy.

## Example

Try:

```text
Company: Blue Tokai
Industry: Specialty coffee
Geography: India
Competitors: 5
```

## Important

Pricing and other current information can change. The app asks the model to use current web evidence,
include source links, date-stamp pricing, and mark unavailable evidence rather than guessing.
