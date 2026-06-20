"""
Configuration template for Upwork Proposal Automation.

SETUP:
  1. Copy this file to config.py:
       copy config_sample.py config.py        (Windows)
       cp config_sample.py config.py          (Mac/Linux)

  2. Edit config.py — customize PROFILE with your skills, rate, and bio.

  3. Create .env from .env.example and add your API keys there.
     Never put API keys in config.py.

Secrets belong in .env only:
  - GEMINI_API_KEY
  - SLACK_WEBHOOK_URL
  - GOOGLE_SHEETS_ID
  - MY_NAME

Google OAuth belongs in credentials.json (download from Google Cloud Console).
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
PROCESSED_EMAILS_FILE = DATA_DIR / "processed_emails.json"
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

# ---------------------------------------------------------------------------
# Gmail settings
# ---------------------------------------------------------------------------
VOLLNA_SENDER = "info@vollna.com"
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/spreadsheets",
]

# ---------------------------------------------------------------------------
# Polling & filtering (override via .env)
# ---------------------------------------------------------------------------
POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "30"))
SCORE_THRESHOLD = int(os.getenv("SCORE_THRESHOLD", "6"))
MIN_BUDGET_HOURLY = float(os.getenv("MIN_BUDGET_HOURLY", "15"))
MIN_BUDGET_FIXED = float(os.getenv("MIN_BUDGET_FIXED", "100"))

# ---------------------------------------------------------------------------
# API keys & URLs — loaded from .env (never hard-code here)
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODELS = os.getenv(
    "GEMINI_MODELS",
    "gemini-2.0-flash-lite,gemini-1.5-flash,gemini-2.0-flash",
).split(",")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
MY_NAME = os.getenv("MY_NAME", "Your Name")

# ---------------------------------------------------------------------------
# Your Upwork profile — CUSTOMIZE THIS for your skills and experience
# ---------------------------------------------------------------------------
PROFILE = {
    "title": "Senior AI & Automation Developer | 10+ Years Experience",
    "rate": "$30/hour",
    "bio": (
        "I'm a senior developer with over 10 years of experience building AI agents, "
        "automating workflows, and creating scalable SaaS solutions. I specialize in "
        "helping businesses save time and money through intelligent automation."
    ),
    "skills": [
        "AI Development",
        "AI Agents",
        "n8n",
        "Workflow Automation",
        "API Development",
        "SaaS Development",
        "Python",
        "JavaScript",
        "React",
        "Node.js",
        "REST API",
        "Web Development",
        "Full-Stack Development",
    ],
    "primary_skills": [
        "AI",
        "AI agent",
        "automation",
        "n8n",
        "API",
        "SaaS",
        "Python",
        "workflow",
        "chatbot",
        "LLM",
        "integration",
        "webhook",
    ],
    "experience_highlights": [
        "Built 50+ custom AI agents and chatbots",
        "Automated workflows using n8n saving 20+ hours/week",
        "Developed multiple SaaS platforms from concept to production",
        "Created 100+ APIs for various applications",
    ],
    "proposal_hook": (
        "Senior developer with 10+ years experience offering expert work at $30/hour. "
        "You get senior quality at affordable rates. I specialize in AI, n8n automation, "
        "and API development."
    ),
}

# Google Sheets column headers (row 1 in your spreadsheet)
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
