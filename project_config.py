"""
Committed config for Vercel dashboard API and fresh clones.

Local development should still use config.py (gitignored) copied from config_sample.py.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
CREDENTIALS_DIR = BASE_DIR / "credentials"
PROCESSED_EMAILS_FILE = DATA_DIR / "processed_emails.json"


def _credential_path(preferred: Path, legacy: Path) -> Path:
    return preferred if preferred.exists() else legacy


CREDENTIALS_FILE = _credential_path(
    CREDENTIALS_DIR / "gmail_oauth.json",
    BASE_DIR / "credentials_oauth.json",
)
SHEETS_CREDENTIALS_FILE = _credential_path(
    CREDENTIALS_DIR / "sheets_service.json",
    BASE_DIR / "credentials.json",
)
TOKEN_FILE = _credential_path(
    CREDENTIALS_DIR / "token.json",
    BASE_DIR / "token.json",
)

VOLLNA_SENDER = "info@vollna.com"
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/spreadsheets",
]

POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "30"))
SCORE_THRESHOLD = int(os.getenv("SCORE_THRESHOLD", "6"))
MIN_BUDGET_HOURLY = float(os.getenv("MIN_BUDGET_HOURLY", "15"))
MIN_BUDGET_FIXED = float(os.getenv("MIN_BUDGET_FIXED", "100"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_SERVICE_ACCOUNT = os.getenv("GEMINI_SERVICE_ACCOUNT", "gemini-credentials.json")
GEMINI_MODELS = os.getenv(
    "GEMINI_MODELS",
    "gemini-2.0-flash-lite,gemini-1.5-flash,gemini-2.0-flash",
).split(",")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
MY_NAME = os.getenv("MY_NAME", "Maria")

PROFILE = {
    "title": "AI Automation Developer | Python | n8n | API Integration | 13 Years",
    "rate": "$50/hour",
    "bio": (
        "Senior developer with 13 years of experience building AI agents and "
        "automation systems that eliminate manual work. I build production-ready "
        "solutions that integrate with your existing tools — Gmail, Slack, Google Sheets, "
        "and more. I deliver reliable, documented code that you own completely."
    ),
    "skills": [
        "Python",
        "AI Agents",
        "Automation",
        "API Integration",
        "n8n",
        "Google Gemini",
        "Google Sheets API",
        "Gmail API",
        "Slack Webhooks",
        "REST APIs",
        "Data Extraction",
        "Document Processing",
        "Lead Qualification",
        "Workflow Automation",
        "Custom Scripts",
    ],
    "primary_skills": [
        "python",
        "automation",
        "api",
        "integration",
        "ai",
        "workflow",
        "n8n",
        "google sheets",
        "gmail",
        "slack",
        "webhook",
        "agent",
        "extract",
        "process",
        "scraping",
    ],
    "experience_highlights": [
        "Built an AI agent that reads job alerts, scores them, writes proposals via Google Gemini, and saves them as drafts — saving 10+ hours/week",
        "13 years of software development across automation, AI, and APIs",
        "Expert at connecting tools: Gmail, Slack, Google Sheets, CRMs",
        "Deliver production-ready solutions with clear documentation",
    ],
    "proposal_hook": (
        "Senior developer with 13 years of experience building AI automation that "
        "eliminates manual work. My recent project saved 10+ hours per week by "
        "automating the entire job search workflow — from alerts to proposals. "
        "I deliver reliable, documented solutions at $50/hour."
    ),
}

SHEETS_HEADERS = [
    "Timestamp",
    "Title",
    "Budget",
    "Score",
    "Status",
    "URL",
    "Proposal",
    "Matched Skills",
]

STATUS_DRAFTED = "Draft Saved"
STATUS_SKIPPED = "Skipped"
STATUS_ERROR = "Error"
STATUS_PENDING = "Pending"


def apply_streamlit_secrets() -> None:
    """Copy Streamlit Cloud secrets into os.environ for shared config fields."""
    global GEMINI_API_KEY, SLACK_WEBHOOK_URL, GOOGLE_SHEETS_ID, MY_NAME

    try:
        import streamlit as st

        secrets = st.secrets
    except Exception:
        return

    for key in ("GEMINI_API_KEY", "SLACK_WEBHOOK_URL", "GOOGLE_SHEETS_ID", "MY_NAME"):
        if key in secrets:
            os.environ[key] = str(secrets[key])

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
    GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
    MY_NAME = os.getenv("MY_NAME", MY_NAME)


def agent_can_run_locally() -> bool:
    """Gmail OAuth files exist — safe to run main.py from the dashboard."""
    return CREDENTIALS_FILE.exists() and TOKEN_FILE.exists()
