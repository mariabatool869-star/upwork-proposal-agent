# Upwork Proposal Automation

A free, local Python agent that turns **Vollna job alerts** into ready-to-send **Upwork proposals**.

It reads Gmail alerts, scores jobs against your profile, writes proposals with **Google Gemini**, saves **Gmail drafts**, logs to **Google Sheets**, and notifies you on **Slack**.

**Cost: $0** — Gmail, Gemini, Slack, and Google Sheets free tiers only. No hosting required.

---

## What It Does

1. Polls Gmail for emails from `info@vollna.com`
2. Extracts job title, budget, and Upwork URL
3. Scores each job 1–10 against your skills
4. Skips low-scoring or low-budget jobs
5. Writes a 55–75 word proposal (Nick Saraev formula) via Gemini
6. Saves the proposal as a **Gmail draft**
7. Logs every job to **Google Sheets** (matched or skipped)
8. Sends a **Slack notification** when a draft is ready

---

## Requirements

- Python 3.9+
- A Gmail account receiving Vollna alerts
- Free API keys (see setup below)

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/upwork-proposal-automation.git
cd upwork-proposal-automation
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Create your config file

```bash
# Windows
copy config_sample.py config.py

# Mac / Linux
cp config_sample.py config.py
```

Edit `config.py` and customize the `PROFILE` section with **your** skills, rate, bio, and experience.

### 4. Set up environment variables

```bash
# Windows
copy .env.example .env

# Mac / Linux
cp .env.example .env
```

Open `.env` and fill in your keys (see [How to Get API Keys](#how-to-get-api-keys) below).

### 5. Add Google OAuth credentials

Download `credentials.json` from Google Cloud Console (Desktop OAuth app) and place it in the project root. See [Google Gmail + Sheets Setup](#b-gmail--google-sheets-free).

### 6. Run

```bash
python main.py
```

On first run, a browser opens for Google sign-in. After that, `token.json` is saved automatically.

---

## How to Run

| Command | Description |
|---------|-------------|
| `python main.py` | Check Gmail **once** and exit |
| `python main.py --loop` | Run every 30 minutes until stopped |
| `python main.py --reprocess` | Re-check all emails (clears processed history) |
| `python main.py --url "UPWORK_URL" --title "Job Title" --budget "$50/hr"` | Test with a manual job URL |

**Windows shortcuts:** double-click `run_once.bat` (single run) or `run_loop.bat` (background mode).

### How to Stop

| Mode | How to stop |
|------|-------------|
| Single run (`python main.py`) | Stops automatically when finished |
| Loop mode (`python main.py --loop`) | Press **Ctrl+C** in the terminal |
| Task Scheduler | Disable or delete the scheduled task |

---

## How to Get API Keys

### A. Google Gemini (Free)

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Click **Create API Key**
3. Copy the key into `.env`:
   ```
   GEMINI_API_KEY=AIza...
   ```
   **Important:** Key must start with `AIza` (from AI Studio, not Google Cloud Console).

---

### B. Gmail + Google Sheets (Free)

Both use the same Google Cloud project.

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable **Gmail API** and **Google Sheets API** (APIs & Services → Library)
4. Set up **OAuth consent screen** (External) and add yourself as a **Test user**
5. Create **OAuth client ID** → Application type: **Desktop app**
6. Download JSON → rename to `credentials.json` → place in project root

**Create a Google Sheet for logging:**

1. Create a spreadsheet at [Google Sheets](https://sheets.google.com)
2. Copy the ID from the URL: `https://docs.google.com/spreadsheets/d/THIS_PART/edit`
3. Add to `.env`:
   ```
   GOOGLE_SHEETS_ID=THIS_PART
   ```

---

### C. Slack Webhook (Free)

1. Go to [Slack API Apps](https://api.slack.com/apps) → **Create New App** → **From scratch**
2. Enable **Incoming Webhooks**
3. **Add New Webhook to Workspace** → pick a channel
4. Copy the URL into `.env`:
   ```
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
   ```

---

## Configuration

### Environment variables (`.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | — | Google Gemini API key (starts with `AIza`) |
| `SLACK_WEBHOOK_URL` | Yes | — | Slack incoming webhook URL |
| `GOOGLE_SHEETS_ID` | Yes | — | Spreadsheet ID for job logging |
| `MY_NAME` | Yes | — | Your name in proposal signatures |
| `GEMINI_MODELS` | No | `gemini-2.0-flash-lite,...` | Models to try if one hits quota |
| `POLL_INTERVAL_MINUTES` | No | `30` | Minutes between checks in `--loop` mode |
| `SCORE_THRESHOLD` | No | `6` | Minimum score (1–10) to draft a proposal |
| `MIN_BUDGET_HOURLY` | No | `15` | Skip hourly jobs below this $/hr |
| `MIN_BUDGET_FIXED` | No | `100` | Skip fixed-price jobs below this amount |

### Profile settings (`config.py`)

Copy from `config_sample.py` and edit:

- `PROFILE["skills"]` — your skill list (used for job matching)
- `PROFILE["primary_skills"]` — weighted keywords for scoring
- `PROFILE["rate"]` — your hourly rate (mentioned in proposals)
- `PROFILE["bio"]` and `experience_highlights` — used by Gemini when writing proposals

---

## Project Structure

```
├── main.py              # Main orchestrator
├── config_sample.py     # Config template (copy to config.py)
├── config.py            # Your personal config (gitignored — do not commit)
├── gmail_reader.py      # Gmail API — fetch emails, create drafts
├── job_parser.py        # Parse Vollna email content
├── job_scorer.py        # Score jobs 1–10
├── proposal_writer.py   # Generate proposals with Gemini
├── slack_notifier.py    # Slack notifications
├── sheets_logger.py     # Google Sheets logging
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── .env                 # Your secrets (gitignored — do not commit)
├── credentials.json     # Google OAuth (gitignored — do not commit)
├── token.json           # Auto-created after Google sign-in (gitignored)
├── run_once.bat         # Windows: single run
└── run_loop.bat         # Windows: background loop
```

---

## Security

**Never commit these files:**

| File | Contains |
|------|----------|
| `.env` | Gemini key, Slack webhook, Sheets ID |
| `credentials.json` | Google OAuth client secret |
| `token.json` | Google access/refresh tokens |
| `config.py` | Your personal profile (copy from `config_sample.py` locally) |
| `logs/` / `data/` | Job history and runtime data |

If you accidentally push secrets:

1. **Rotate immediately** — regenerate Gemini key, Slack webhook, and Google OAuth credentials
2. Delete `token.json` and sign in again
3. Use [GitHub secret scanning](https://docs.github.com/en/code-security/secret-scanning) or `git filter-repo` to remove from history

---

## Publish to GitHub

Run these commands from the project folder:

```bash
# Initialize git (skip if already done)
git init

# Verify secrets are ignored BEFORE committing
git check-ignore -v .env credentials.json token.json config.py logs data

# Stage and review what will be uploaded
git add .
git status

# Commit (confirm no secret files appear in the list above)
git commit -m "Add Upwork proposal automation agent"

# Create repo on GitHub first, then:
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/upwork-proposal-automation.git
git push -u origin main
```

**Before pushing, confirm `git status` does NOT list:**

- `.env`
- `credentials.json`
- `token.json`
- `config.py`

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Missing credentials.json` | Download OAuth credentials from Google Cloud (Desktop app) |
| `Missing config.py` | Run `copy config_sample.py config.py` and customize |
| `GEMINI_API_KEY is not set` | Add key to `.env` (must start with `AIza`) |
| Gemini `429 quota exceeded` | Use a valid AI Studio key; try `GEMINI_MODELS` in `.env` |
| `credentials.json.json` error | Windows hid extensions — rename to exactly `credentials.json` |
| No Vollna emails found | Sign in with the Gmail account that receives Vollna alerts |
| Token expired | Delete `token.json` and run again |

---

## Workflow

1. Vollna sends a job alert to Gmail
2. Agent scores the job and skips poor matches
3. Gemini writes a tailored proposal
4. Draft appears in Gmail → you review and copy to Upwork
5. Slack notifies you; Sheets logs everything

---

## License

MIT — use freely, customize for your own freelance workflow.
