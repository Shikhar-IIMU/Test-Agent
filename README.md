AI Competitive Intelligence Agent
A deployable Streamlit MVP for automated competitor research using:
Google Gemini for synthesis and analysis
Tavily for web research
Streamlit for the frontend
What the app does
Enter a company/product and market. The app searches the web for:
Competitors
Products and features
Public pricing
Recent developments
Partnerships/funding/expansion
Customer and market signals
Gemini then converts the collected evidence into:
Executive summary
Company snapshot
Competitive landscape
Feature comparison
Pricing comparison
Recent developments
Customer/market signals
Strategic implications
Data gaps
Source list
GitHub structure
```text
competitor_intelligence_agent/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── .streamlit/
    └── config.toml
```
1. Local run
Install dependencies:
```bash
pip install -r requirements.txt
```
Create:
```text
.streamlit/secrets.toml
```
Put your keys in it:
```toml
GEMINI_API_KEY = "your-gemini-api-key"
TAVILY_API_KEY = "your-tavily-api-key"
```
Then:
```bash
streamlit run app.py
```
2. Streamlit Cloud deployment
Upload this repository to GitHub.
On Streamlit Community Cloud:
Create a new app
Choose your GitHub repository
Set the main file to `app.py`
Open Advanced settings -> Secrets
Add:
```toml
GEMINI_API_KEY = "your-gemini-api-key"
TAVILY_API_KEY = "your-tavily-api-key"
```
Deploy.
Do not upload `.streamlit/secrets.toml` to GitHub.
3. Suggested demo
Use:
```text
Company: Blue Tokai
Industry: Specialty coffee
Geography: India
Competitors: 5
```
Other good demos:
```text
CRED
Zepto
Nykaa
boAt
MakeMyTrip
Zerodha
```
Evidence design
The app uses an evidence-first approach.
For feature comparison:
`✓` = explicitly supported by evidence
`✕` = explicitly stated as unavailable/not offered
`?` = insufficient evidence
The agent is instructed not to turn "not found" into "does not exist."
Pricing is date-stamped where possible because pricing can change.
Portfolio positioning
Use this project title on your resume/LinkedIn:
AI-Powered Competitive Intelligence System
Example description:
> Built a Streamlit-based competitive intelligence application using Gemini and Tavily to automate competitor discovery, feature/pricing benchmarking, recent-development tracking and evidence-backed strategic analysis.
