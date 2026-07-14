# Pulse AI — Customer Health Intelligence Dashboard

**Enterprise Edition** | Langflow RAG-backed | v3.0

Pulse AI turns fragmented customer data (CRM, support tickets, usage analytics, billing) into a single, explainable health signal — synthesised by RAG into a clear executive narrative.

---

## Live links

| What | URL |
|---|---|
| **Docs site** | https://anshusharma-ipl.github.io/PulseAI/ |
| **Live app** | https://pulseai-anshusharma.streamlit.app |

---

## How to use it

### 1. Configure Langflow (once only)

1. Open the **[docs site](https://anshusharma-ipl.github.io/PulseAI/)**
2. Click **Connect Langflow** in the sidebar
3. Enter your Langflow instance URLs and API key:
   - **Account summary URL** — your Langflow account health flow run URL
   - **Portfolio URL** — your Langflow portfolio aggregator flow run URL
   - **API key** — your Langflow API key
4. Click **Save** — credentials are stored in your browser only, never sent anywhere

### 2. Open Live Demo

Click **Live Demo** in the sidebar — you are redirected instantly to the hosted Streamlit app with your credentials pre-configured.

---

## Architecture

```
Docs site (GitHub Pages)          Streamlit app (Streamlit Cloud)
  index.html                   →    pulseai-anshusharma.streamlit.app
  Connect Langflow modal              ↕ reads ?lf_url / ?lf_key / ?lf_portfolio
  saves to localStorage         →    calls your Langflow instance
                                      ↕
                                Langflow (your hosted instance)
                                      ↕
                                LLM (OpenAI / Anthropic / etc.)
```

**Credentials flow:**
- Langflow URLs → stored in browser `localStorage` → appended as query params to Streamlit URL
- Langflow API key → same path — never in source code, never in git, never on any server
- LLM API keys → stay inside your Langflow server only, never leave it

---

## Security

✅ No credentials in source code  
✅ No credentials in git history  
✅ LLM API keys never leave your Langflow server  
✅ Langflow API key stored only in the user's browser  
✅ All code is open source — nothing sensitive to hide  

---

## Project structure

```
PulseAI/
├── .gitignore
├── .streamlit/
│   └── config.toml         ← Streamlit server config
├── requirements.txt
├── README.md
├── index.html              ← Docs site home (GitHub Pages)
├── app/
│   ├── pulse_app.py        ← Streamlit dashboard
│   └── stlite-runtime.html ← Live Demo redirect page
├── assets/
│   ├── css/style.css
│   └── js/site.js
└── pages/
    ├── product-briefing.html
    └── press-release.html
```

---

## Run locally (optional)

Only needed if you want to develop or test changes locally.

```bash
# Install dependencies
pip install -r requirements.txt

# Run Streamlit
python -m streamlit run app/pulse_app.py
```

Configure your Langflow credentials via the **Connect Langflow** button, or pass them as environment variables:

```bash
LANGFLOW_URL=https://your-langflow.com/api/v1/run/<flow-id>
LANGFLOW_PORTFOLIO_URL=https://your-langflow.com/api/v1/run/<portfolio-flow-id>
LANGFLOW_API_KEY=sk-...
```

---

## Langflow setup

Pulse AI requires two Langflow flows:

1. **Account health flow** — takes an `account_id` (e.g. `ACC-003`), queries the RAG knowledge base, returns a structured health report
2. **Portfolio aggregator flow** — returns a scored table of all accounts sorted by health score

See the **[Product Briefing](pages/product-briefing.html)** for full details on the RAG architecture.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend docs | Plain HTML/CSS/JS — GitHub Pages |
| Dashboard | Python + Streamlit — Streamlit Community Cloud |
| AI / RAG | Langflow + vector store + LLM of your choice |
| PDF export | fpdf2 |
