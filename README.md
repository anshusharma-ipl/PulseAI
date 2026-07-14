# Pulse AI — Customer Health Intelligence Dashboard

**Enterprise Edition** | Langflow RAG-backed | v3.0

Pulse AI turns fragmented customer data (CRM, support tickets, usage analytics, billing) into a single, explainable health signal. Every insight is cited back to the data it came from.

---

## What's inside

- **`index.html`** — Documentation site home page
- **`app/pulse_app.py`** — Streamlit dashboard app
- **`app/stlite-runtime.html`** — Live Demo launcher page (embeds Streamlit in an iframe)
- **`assets/`** — Shared CSS + JS for the doc site
- **`pages/`** — Product briefing & press release

---

## Quick start (local)

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install streamlit requests markdown fpdf2
```

### 2. Start Streamlit

```bash
python -m streamlit run app/pulse_app.py
```

Streamlit opens at `http://localhost:8501`.

### 3. *(Optional)* View the docs site

In a second terminal:
```bash
python -m http.server 5500
```
Open `http://localhost:5500` → click **Live Demo** → **Connect**.

---

## Connect your Langflow backend

Pulse AI needs two Langflow flows:

1. **Account health flow** — RAG query that takes an `account_id` (e.g. `ACC-003`) and returns a health report
2. **Portfolio aggregator flow** — returns a summary table of all accounts sorted by health score

### Option A: Via the doc site (browser-only, no files touched)

1. Open the docs site (`index.html` or `http://localhost:5500`)
2. Click **Connect Langflow** in the sidebar
3. Enter your Langflow URLs + API key
4. Click **Save**

The credentials save to `localStorage` (browser only — never written to disk). The Live Demo launcher auto-appends them as query params to the Streamlit URL.

### Option B: Environment variables (persistent, server-friendly)

Create a `.env` file in the project root (already in `.gitignore` — never commit this):

```bash
LANGFLOW_URL=http://localhost:7860/api/v1/run/<account-flow-id>
LANGFLOW_PORTFOLIO_URL=http://localhost:7860/api/v1/run/<portfolio-flow-id>
LANGFLOW_API_KEY=sk-...
```

Then load it before running Streamlit:

**macOS/Linux:**
```bash
export $(cat .env | xargs) && streamlit run app/pulse_app.py
```

**Windows PowerShell:**
```powershell
Get-Content .env | ForEach-Object { if ($_ -match '^([^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process') } }
python -m streamlit run app/pulse_app.py
```

---

## Security & credentials

✅ **Safe to commit:**
- All code files (credentials read from env vars or query params only)
- `.gitignore` (already blocks secrets)
- `requirements.txt`
- HTML/CSS/JS

❌ **NEVER commit:**
- `.env` or any file containing API keys
- `.streamlit/secrets.toml`
- Langflow JSON exports **without reviewing first** — they MAY contain API keys embedded in component config fields (e.g. OpenAI key inside a `ChatOpenAI` component)

### Before committing a Langflow JSON export:

1. Open it in a text editor
2. Search for strings like `"api_key"`, `"openai_api_key"`, `"token"`, `"password"`
3. Replace any found keys with placeholder text: `"REPLACE_WITH_YOUR_KEY"`
4. Add a note in the JSON or README explaining which fields need user-supplied keys

---

## Deploy to a public URL

### Option 1: GitHub Pages (docs site only, Streamlit runs locally)

1. Push this repo to GitHub
2. Go to **Settings → Pages → Source** → select `main` branch, `/ (root)` folder
3. GitHub deploys `index.html` to `https://<username>.github.io/<repo>/`
4. Users open that URL, click **Connect Langflow**, start Streamlit locally, click **Connect** on the Live Demo page

**Pros:** Free, instant, no server needed  
**Cons:** Each user runs Streamlit on their own machine

---

### Option 2: Streamlit Community Cloud (full app hosted, Langflow required)

1. Push this repo to GitHub (public or private)
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Point it to your repo, `main` branch, `app/pulse_app.py`
4. Under **Advanced settings → Secrets**, add:
   ```toml
   LANGFLOW_URL = "https://your-langflow.com/api/v1/run/<flow-id>"
   LANGFLOW_API_KEY = "sk-..."
   LANGFLOW_PORTFOLIO_URL = "https://your-langflow.com/api/v1/run/<portfolio-flow-id>"
   ```
5. Deploy

**Pros:** Fully hosted, no local setup needed, Streamlit runs in the cloud  
**Cons:** Requires a publicly accessible Langflow instance (or use ngrok/Cloudflare Tunnel)

---

### Option 3: Hybrid (docs on GitHub Pages, Streamlit on Cloud)

Best of both: docs site at `https://<user>.github.io/<repo>/`, Streamlit at `https://<app>.streamlit.app`.

1. Deploy docs to GitHub Pages (Option 1)
2. Deploy Streamlit to Community Cloud (Option 2)
3. Update `app/stlite-runtime.html` line 178 to default to your Streamlit Cloud URL instead of `localhost:8501`:
   ```html
   value="https://<your-app>.streamlit.app"
   ```

Users visit GitHub Pages → click Live Demo → auto-connects to your hosted Streamlit (no local install needed).

---

## Project structure

```
PulseAI/
├── .gitignore              ← blocks secrets, .env, __pycache__
├── .streamlit/
│   └── config.toml         ← enables iframe embedding
├── requirements.txt
├── README.md
├── index.html              ← docs site home
├── app/
│   ├── pulse_app.py        ← Streamlit dashboard
│   └── stlite-runtime.html ← Live Demo launcher
├── assets/
│   ├── css/style.css
│   └── js/site.js          ← Settings modal, Langflow config
└── pages/
    ├── product-briefing.html
    └── press-release.html
```

---

## Langflow JSON exports: do they contain my LLM API keys?

**Short answer:** **Maybe. It depends.**

Langflow JSON exports include the full flow definition — nodes, edges, and **all component field values**. If a component (e.g. `ChatOpenAI`, `OpenAIEmbeddings`) has an API key field that you filled in the Langflow UI, **that key is saved in the JSON** as plaintext.

### Safe fields (no secrets):
- Model names (`gpt-4`, `text-embedding-ada-002`)
- Temperature, max tokens, system prompts
- Vector store names, collection names
- URLs (if they don't contain auth tokens in the query string)

### Unsafe fields (contain secrets):
- `api_key`, `openai_api_key`, `anthropic_api_key`
- `token`, `access_token`, `bearer_token`
- Database passwords
- Any field marked "password" or "secret" in the UI

### How to safely share a Langflow JSON:

1. Export your flow from Langflow
2. Open the `.json` file in VS Code / text editor
3. Search for: `"api_key"`, `"openai_api_key"`, `"password"`, `"token"`
4. Replace all found values with `"REPLACE_WITH_YOUR_KEY"`
5. At the top of the file, add a comment block (inside a `"_instructions"` field if Langflow allows, or in a README):
   ```json
   {
     "_instructions": "Before importing: replace all 'REPLACE_WITH_YOUR_KEY' placeholders with your actual API keys in the OpenAI, Anthropic, and VectorStore components.",
     "nodes": [ ... ]
   }
   ```
6. Commit the sanitized JSON

**Alternative:** Use Langflow's **Global Variables** feature (if available in your version) to store API keys outside the flow JSON — then the export won't contain them.

---

## License

[Add your license here — e.g. MIT, Apache 2.0, or proprietary]

---

## Questions?

See the **Product Briefing** and **Press Release** in the `pages/` folder for full context on what Pulse AI does and why.
