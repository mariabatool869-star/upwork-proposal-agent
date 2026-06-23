"""
Cloud-safe configuration for Streamlit Community Cloud.
Used when local config.py is not present (gitignored).

Secrets: set in Streamlit Cloud → App settings → Secrets (see .streamlit/secrets.toml.example).
Local dev: still uses .env via python-dotenv.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

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
    "https://www.googleapis.com/auth/spreadsheets",
]


def _secret(key: str, default: str = "") -> str:
    """Read from Streamlit secrets (cloud) or environment (.env local)."""
    try:
        import streamlit as st

        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)


POLL_INTERVAL_MINUTES = int(_secret("POLL_INTERVAL_MINUTES", "30"))
SCORE_THRESHOLD = int(_secret("SCORE_THRESHOLD", "6"))
MIN_BUDGET_HOURLY = float(_secret("MIN_BUDGET_HOURLY", "15"))
MIN_BUDGET_FIXED = float(_secret("MIN_BUDGET_FIXED", "100"))

GEMINI_API_KEY = _secret("GEMINI_API_KEY", "")
GEMINI_MODELS = _secret(
    "GEMINI_MODELS",
    "gemini-2.0-flash-lite,gemini-1.5-flash,gemini-2.0-flash",
).split(",")
SLACK_WEBHOOK_URL = _secret("SLACK_WEBHOOK_URL", "")
GOOGLE_SHEETS_ID = _secret("GOOGLE_SHEETS_ID", "")
MY_NAME = _secret("MY_NAME", "Maria")

PROFILE = {
    "title": "AI Automation Developer | Python | n8n | API Integration | 13 Years",
    "rate": "$50/hour",
    "bio": (
        "Senior developer with 13 years of experience building AI agents and "
        "automation systems that eliminate manual work."
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
        "Workflow Automation",
    ],
    "primary_skills": [
        "python",
        "automation",
        "api",
        "ai",
        "workflow",
        "n8n",
        "google sheets",
        "gmail",
        "slack",
    ],
    "experience_highlights": [
        "Built an AI agent that reads job alerts, scores them, and writes proposals via Gemini",
        "13 years of software development across automation, AI, and APIs",
        "Expert at connecting tools: Gmail, Slack, Google Sheets, CRMs",
    ],
    "proposal_hook": (
        "Senior developer with 13 years of experience building AI automation that "
        "eliminates manual work."
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
STATUS_DEMO = "Demo Draft"
STATUS_SKIPPED = "Skipped"
STATUS_ERROR = "Error"
STATUS_PENDING = "Pending"
