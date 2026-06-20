"""
Sheets logger — logs every processed job to Google Sheets.
Uses the same Google OAuth token as Gmail.
"""

import logging
from datetime import datetime, timezone

from googleapiclient.discovery import build

import config
from gmail_reader import get_google_credentials

logger = logging.getLogger(__name__)


def get_sheets_service():
    """Build Google Sheets API service using the same Google OAuth token as Gmail."""
    return build("sheets", "v4", credentials=get_google_credentials())


def ensure_headers(sheets_service):
    """
    Write header row to the sheet if it's empty.
    Call once on startup.
    """
    if not config.GOOGLE_SHEETS_ID:
        logger.warning("GOOGLE_SHEETS_ID not set — skipping Sheets logging.")
        return False

    try:
        result = (
            sheets_service.spreadsheets()
            .values()
            .get(spreadsheetId=config.GOOGLE_SHEETS_ID, range="A1:H1")
            .execute()
        )
        existing = result.get("values", [])

        if not existing or existing[0] != config.SHEETS_HEADERS:
            sheets_service.spreadsheets().values().update(
                spreadsheetId=config.GOOGLE_SHEETS_ID,
                range="A1:H1",
                valueInputOption="RAW",
                body={"values": [config.SHEETS_HEADERS]},
            ).execute()
            logger.info("Sheet headers written.")

        return True
    except Exception as exc:
        logger.error(f"Failed to ensure sheet headers: {exc}")
        return False


def log_job(sheets_service, job, score, status, proposal="", matched_skills=None):
    """
    Append one job row to Google Sheets.

    status: "drafted", "skipped", or "error"
    """
    if not config.GOOGLE_SHEETS_ID:
        logger.warning("GOOGLE_SHEETS_ID not set — skipping Sheets log.")
        return False

    if sheets_service is None:
        return False

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    skills_str = ", ".join(matched_skills or [])

    row = [
        timestamp,
        job.get("title", ""),
        job.get("budget_display") or job.get("budget", ""),
        score,
        status,
        job.get("url", ""),
        proposal[:500] if proposal else "",  # Truncate long proposals in sheet
        skills_str,
    ]

    try:
        sheets_service.spreadsheets().values().append(
            spreadsheetId=config.GOOGLE_SHEETS_ID,
            range="A:H",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]},
        ).execute()
        logger.info(f"Logged to Sheets: {job.get('title')} [{status}]")
        return True
    except Exception as exc:
        logger.error(f"Failed to log to Sheets: {exc}")
        return False
