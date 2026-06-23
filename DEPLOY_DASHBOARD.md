# Deploy dashboard online (same UI as localhost)

**Vercel = landing page only.**  
**Streamlit Cloud = full dashboard** (login, jobs, charts, proposals).

## 5-minute deploy

### 1. Open Streamlit Cloud
https://share.streamlit.io → **Continue with GitHub**

### 2. Create app
| Field | Value |
|-------|--------|
| Repository | `mariabatool869-star/upwork-proposal-agent` |
| Branch | `main` |
| Main file | **`streamlit_app.py`** |

### 3. Secrets (required)
App settings → **Secrets** → paste from `.streamlit/secrets.toml.example`

Minimum:
- `GEMINI_API_KEY`
- `GOOGLE_SHEETS_ID`
- `MY_NAME`
- Full `[gcp_service_account]` block from `credentials/sheets_service.json`

### 4. Deploy
Click **Deploy**. Your public URL:
`https://upwork-proposal-agent.streamlit.app`

Login: **demo** / **demo123**

### 5. Update Vercel link (optional)
After deploy, edit `public/index.html` → set **Open Live Dashboard** href to your Streamlit URL.

---

## Two URLs

| URL | What you see |
|-----|----------------|
| `upwork-proposal-agent.vercel.app` | Portfolio intro page |
| `upwork-proposal-agent.streamlit.app` | **Full dashboard (like localhost)** |

## Local still works
```powershell
python -m streamlit run streamlit_app.py
```
→ http://localhost:8501
