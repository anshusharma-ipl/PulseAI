# Pulse AI — Customer Health Intelligence Dashboard

**Enterprise Edition** | Langflow RAG-backed | v3.0

Pulse AI turns fragmented customer data (CRM, support tickets, usage analytics, billing) into a single, explainable health signal — synthesised by RAG into a clear executive narrative.

---

## Live links

| What | URL |
|---|---|
| **Docs / demo site** | https://anshusharma-ipl.github.io/PulseAI/ |

> The Streamlit app runs **locally** and is tunnelled to the doc site via ngrok. There is no permanently hosted Streamlit URL — `start.bat` handles everything automatically.

---

## How to run (one-click)

### Prerequisites
- [Python 3.9+](https://python.org)
- [ngrok](https://ngrok.com/download) on your PATH
- [Langflow Desktop](https://langflow.org) installed and your flows imported

### Steps

1. **Install Python dependencies** (once only):
   ```bash
   pip install -r requirements.txt
   ```

2. **Open Langflow Desktop** and make sure both flows are running on port `7860`.

3. **Double-click `start.bat`** — it does the rest automatically:

   | Step | What happens |
   |------|-------------|
   | 1 | Configures the ngrok auth token |
   | 2 | Waits until Langflow is healthy on `:7860` |
   | 3 | Opens an ngrok HTTPS tunnel for Langflow → `https://aaa.ngrok-free.app` |
   | 4 | Starts Streamlit on `:8501`, waits for health check |
   | 5 | Opens a second ngrok tunnel for Streamlit → `https://bbb.ngrok-free.app` |
   | 6 | Saves all URLs + API key to browser `localStorage`, opens the doc site |

4. The doc site at **http://localhost:5500/pages/product-briefing.html** loads with Streamlit embedded in the iframe — exactly as it appears on GitHub Pages.

5. **To stop everything:** double-click `stop.bat`.

---

## Architecture

```
Your PC
├── Langflow Desktop  :7860  ──► ngrok ──► https://aaa.ngrok-free.app
│     RAG flows + LLM                        (Langflow public API)
│
└── Streamlit         :8501  ──► ngrok ──► https://bbb.ngrok-free.app
      pulse_app.py                            (the dashboard)
                                                      ▲
                                                      │  iframe src
                              ┌───────────────────────┘
                    GitHub Pages  (or localhost:5500)
                    pages/product-briefing.html
                    ← localStorage: { streamlitUrl, lf_url, lf_key, lf_portfolio }
```

**Credentials flow:**

1. `start.bat` saves `{ streamlitUrl, url, portfolioUrl, key }` to browser `localStorage`
2. `site.js` reads `localStorage` on page load → builds iframe `src` with credentials as query params
3. Streamlit reads `?lf_url / ?lf_key / ?lf_portfolio` from query params on each request
4. All Langflow calls are made server-side from within Streamlit — credentials never leave the browser unintentionally

**Why ngrok instead of Streamlit Cloud?**  
Streamlit Cloud injects `X-Frame-Options: SAMEORIGIN` at the infrastructure level, which blocks the app from being embedded in the doc site iframe. Running locally with ngrok means we control the server headers — no iframe restrictions.

---

## Manual connection (without start.bat)

If ngrok is already running, open **Connect** in the doc site header and enter:

| Field | Value |
|---|---|
| Account-summary URL | `https://aaa.ngrok-free.app/api/v1/run/<account-flow-id>` |
| Portfolio URL | `https://aaa.ngrok-free.app/api/v1/run/<portfolio-flow-id>` |
| Langflow API key | your `sk-...` key |
| Streamlit URL | `https://bbb.ngrok-free.app` |

Or pass them as environment variables to Streamlit directly:

```bash
LANGFLOW_URL=https://aaa.ngrok-free.app/api/v1/run/<flow-id>
LANGFLOW_PORTFOLIO_URL=https://aaa.ngrok-free.app/api/v1/run/<portfolio-flow-id>
LANGFLOW_API_KEY=sk-...
python -m streamlit run app/pulse_app.py
```

---

## Langflow setup

Pulse AI requires two Langflow flows:

| Flow | Input | Output |
|---|---|---|
| **Account health flow** | `account_id` e.g. `ACC-003` | Structured markdown health report |
| **Portfolio aggregator flow** | `"portfolio"` | Pipe-delimited table: `account_id \| name \| score \| status` |

Flow IDs in use:
- Account health: `23c05a7b-e595-4ffb-b783-56bad5ab65dc`
- Portfolio aggregator: `c94cf6ad-4f38-4d92-9f6b-d33c50ca5ba5`

---

## Project structure

```
PulseAI/
├── start.bat                   ← one-click startup (ngrok + Streamlit + docs server)
├── stop.bat                    ← kills all services
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── config.toml             ← enableCORS=false, headless=true
├── index.html                  ← redirects to pages/product-briefing.html
├── app/
│   ├── pulse_app.py            ← Streamlit dashboard (v3.0)
│   └── stlite-runtime.html     ← legacy redirect page (kept for reference)
├── assets/
│   ├── css/style.css           ← doc site + demo-shell iframe styles
│   └── js/site.js              ← localStorage, iframe loader, settings modal
└── pages/
    ├── product-briefing.html   ← main page: full-viewport Streamlit iframe
    └── press-release.html      ← Working Backwards press release
```

---

## Security

| | |
|---|---|
| ✅ | No credentials in source code |
| ✅ | No credentials in git history |
| ✅ | LLM API keys never leave the Langflow server |
| ✅ | Langflow API key stored only in the user's browser `localStorage` |
| ✅ | ngrok token in `start.bat` only — rotate if sharing the repo publicly |
| ✅ | All code is open source |

---

## Tech stack

| Layer | Technology |
|---|---|
| Doc / demo site | Plain HTML/CSS/JS — GitHub Pages (or local `http.server`) |
| Dashboard | Python + Streamlit — runs locally, tunnelled via ngrok |
| Tunnel | ngrok (two tunnels: Langflow `:7860` + Streamlit `:8501`) |
| AI / RAG | Langflow + vector store + LLM of your choice |
| PDF export | fpdf2 |
| Markdown rendering | `markdown` Python library (optional, graceful fallback) |
