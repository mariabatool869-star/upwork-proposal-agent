# Upwork AI Proposal Agent

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Streamlit](https://img.shields.io/badge/dashboard-Streamlit-FF4B4B.svg)](https://streamlit.io)

An open-source Python agent that turns **Vollna job alerts** into ready-to-send **Upwork proposals** — with a **Streamlit portfolio dashboard** to showcase your automation work.

**Cost: $0** — Gmail, Gemini, Slack, and Google Sheets free tiers only.

**Repository:** [github.com/mariabatool869-star/upwork-proposal-agent](https://github.com/mariabatool869-star/upwork-proposal-agent)

---

## Features

| Component | Description |
|-----------|-------------|
| **Gmail reader** | Fetches Vollna HTML emails (`info@vollna.com`) |
| **Job parser** | Extracts title, budget, description, Upwork/Vollna URLs from HTML |
| **Job scorer** | Rates jobs 1–10 against your skills profile |
| **Proposal writer** | Generates proposals via Google Gemini (with safe fallback) |
| **Gmail drafts** | Saves proposals for review before you submit on Upwork |
| **Google Sheets** | Logs every job — powers the dashboard |
| **Slack alerts** | Notifies you when a draft is ready |
| **Streamlit dashboard** | Overview, proposals, analytics, live refresh from Sheets |

---

## Architecture

```text
Vollna Email (Gmail)
        │
        ▼
   job_parser.py ──► job_scorer.py ──► proposal_writer.py (Gemini)
        │                    │                    │
        │                    │                    ▼
        │                    │            gmail_reader.py (draft)
        │                    ▼                    │
        └────────────► sheets_logger.py ◄───────┘
                              │
                              ▼
                    dashboard/app.py (Streamlit)
                              │
                              ▼
                      slack_notifier.py
```

---

## Prerequisites

- **Python 3.9+** (3.11 or 3.12 recommended)
- **Gmail account** receiving Vollna job alerts
- **Google Cloud project** with Gmail API + Sheets API enabled
- **Free API keys:** Gemini, Slack webhook, Google Sheets ID

---

## Local setup

### 1. Clone the repository

```bash
git clone https://github.com/mariabatool869-star/upwork-proposal-agent.git
cd upwork-proposal-agent
```

### 2. Create a virtual environment (recommended)

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Create configuration files

```bash
# Windows
copy config_sample.py config.py
copy .env.example .env

# macOS / Linux
cp config_sample.py config.py
cp .env.example .env
```

Edit **`config.py`** — customize `PROFILE` (skills, rate, bio, experience).

Edit **`.env`** — add your API keys locally (see [Configuration](#configuration)).

> **Never commit `.env` to GitHub.** Only `.env.example` (placeholders) is tracked.

### 5. Add Google credentials

Create a `credentials/` folder and add:

| File | Purpose |
|------|---------|
| `credentials/gmail_oauth.json` | OAuth client for Gmail (Web application type) |
| `credentials/sheets_service.json` | Service account JSON for Google Sheets |

Steps:

1. [Google Cloud Console](https://console.cloud.google.com/) → create a project
2. Enable **Gmail API** and **Google Sheets API**
3. OAuth consent screen → add yourself as a test user
4. Create OAuth client (Web app) → download as `credentials/gmail_oauth.json`
5. Create a service account → download key as `credentials/sheets_service.json`
6. Share your Google Sheet with the service account email (Editor access)

On first Gmail run, complete OAuth in the browser. A token is saved to `credentials/token.json` automatically.

### 6. Verify setup

```bash
python -m py_compile main.py dashboard/app.py
```

---

## Running locally

### Agent (process job emails once)

```bash
python main.py
```

| Windows shortcut | Action |
|------------------|--------|
| `run_once.bat` | Single agent run |
| `run_loop.bat` | Run every 30 minutes (loop) |
| `run_dashboard.bat` | Start Streamlit dashboard |

**First run:** you may be prompted to authorize Gmail via URL + auth code.

**Re-process emails** after parser changes:

```bash
# Windows
del data\processed_emails.json

# macOS / Linux
rm data/processed_emails.json

python main.py
```

### Dashboard (portfolio web app)

```bash
python -m streamlit run dashboard/app.py
```

Open **http://localhost:8501**

| Demo login | Password |
|------------|----------|
| `demo` | `demo123` |

Dashboard pages: **Overview** · **Proposals** · **Analytics** · **About**

After running the agent, click **Refresh data** in the sidebar to load new jobs from Google Sheets. **Recent jobs** shows the newest entries first.

---

## Configuration

### Environment variables (`.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | — | Gemini key from [AI Studio](https://aistudio.google.com/apikey) (must start with `AIza`) |
| `SLACK_WEBHOOK_URL` | Yes | — | Slack incoming webhook URL |
| `GOOGLE_SHEETS_ID` | Yes | — | Spreadsheet ID from the Google Sheets URL |
| `MY_NAME` | Yes | — | Your name in proposal signatures |
| `GEMINI_MODELS` | No | `gemini-2.0-flash-lite,...` | Fallback models if one hits quota |
| `POLL_INTERVAL_MINUTES` | No | `30` | Minutes between checks in loop mode |
| `SCORE_THRESHOLD` | No | `6` | Minimum score (1–10) to draft a proposal |
| `MIN_BUDGET_HOURLY` | No | `15` | Skip hourly jobs below this rate |
| `MIN_BUDGET_FIXED` | No | `100` | Skip fixed-price jobs below this amount |

### Profile (`config.py`)

Copy from `config_sample.py` and edit:

- `PROFILE["skills"]` — skill list for matching
- `PROFILE["primary_skills"]` — weighted scoring keywords
- `PROFILE["rate"]` — hourly rate used in proposals
- `PROFILE["bio"]` and `experience_highlights` — used by Gemini and the dashboard

---

## Project structure

```text
├── main.py                 # Agent orchestrator
├── config_sample.py        # Config template → copy to config.py locally
├── gmail_reader.py         # Gmail API
├── job_parser.py           # Vollna HTML email parser
├── job_scorer.py           # Job scoring (1–10)
├── proposal_writer.py      # Gemini proposals
├── sheets_client.py        # Shared Google Sheets connection
├── sheets_logger.py        # Write rows to Sheets
├── slack_notifier.py       # Slack webhooks
├── dashboard/
│   ├── app.py              # Streamlit portfolio dashboard
│   ├── auth.py             # Demo login
│   └── data_utils.py       # Sheets data, charts, recent jobs
├── credentials/            # Google keys (gitignored — local only)
├── .streamlit/config.toml  # Dashboard theme (local)
├── pyrightconfig.json      # Type-checker config
├── requirements.txt
├── LICENSE                 # MIT License
├── .env.example            # Template only (safe for GitHub)
├── .env                    # Your keys (gitignored — never push)
└── run_*.bat               # Windows shortcuts
```

---

## Security

**Never commit these files:**

| Path | Contains |
|------|----------|
| `.env` | Gemini key, Slack webhook, Sheets ID |
| `credentials/` | Gmail OAuth, service account, token |
| `config.py` | Personal profile |
| `logs/` / `data/` | Runtime history |

Before every push:

```powershell
git check-ignore -v .env credentials config.py
git status
```

If secrets were ever pushed, rotate all keys immediately and use [git filter-repo](https://github.com/newren/git-filter-repo) to scrub history.

---

## Contributing

Contributions are welcome under the [MIT License](LICENSE).

1. **Fork** the repository on GitHub
2. **Create a branch:** `git checkout -b feature/your-feature`
3. **Make changes** — do not commit secrets
4. **Test locally:** `python main.py` and `streamlit run dashboard/app.py`
5. **Open a Pull Request**

### Pull request checklist

- [ ] No `.env`, `credentials/`, or `config.py` in the commit
- [ ] Changes tested locally
- [ ] README updated if setup or behavior changed

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Recent jobs not updating | Click **Refresh data** in dashboard sidebar |
| Recent jobs show old entries | Fixed in latest `data_utils.py` — pull latest and restart Streamlit |
| `Missing credentials/gmail_oauth.json` | Add OAuth JSON to `credentials/` |
| `Missing credentials/sheets_service.json` | Add service account JSON to `credentials/` |
| `GEMINI_API_KEY is not set` | Add key to `.env` (must start with `AIza`) |
| Gemini `429 quota exceeded` | Use AI Studio key; set `GEMINI_MODELS` in `.env` |
| No Vollna emails found | Use the Gmail account that receives Vollna alerts |
| Token expired | Delete `credentials/token.json` and run `python main.py` again |
| Dashboard empty | Run `python main.py` first; click **Refresh data** |
| `.env` on git status | Do not `git add .env` — it must stay gitignored |

---

## Workflow

1. Vollna sends a job alert to Gmail
2. Agent parses, scores, and skips poor matches
3. Gemini writes a tailored proposal
4. Draft saved in Gmail; row logged in Google Sheets
5. Slack notifies you
6. Dashboard shows stats and recent jobs

---

## License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE).

You are free to use, modify, and distribute this software. Attribution is appreciated.

---

## Author

**Maria Batool** — AI Automation Developer

Portfolio project demonstrating end-to-end workflow automation with Python, AI, and free-tier cloud APIs.
