"""
Google Sheets integration — log jobs from the agent.
"""

import logging

from config import SHEETS_HEADERS
from sheets_client import get_sheets_workbook

logger = logging.getLogger(__name__)


def get_sheets_service():
    """Return spreadsheet workbook (alias kept for main.py)."""
    return get_sheets_workbook()


def ensure_headers(sheet):
    """Ensure row 1 has the expected column headers."""
    try:
        if not sheet:
            return False
        worksheet = sheet.get_worksheet(0)
        headers = worksheet.row_values(1)
        if not headers or headers != SHEETS_HEADERS:
            worksheet.insert_row(SHEETS_HEADERS, 1)
        return True
    except Exception as exc:
        logger.error("Headers error: %s", exc)
        return False


def log_job(sheet, job_data):
    """Log a job row to the spreadsheet."""
    try:
        if not sheet:
            return False
        worksheet = sheet.get_worksheet(0)
        worksheet.append_row([
            job_data.get("timestamp", ""),
            job_data.get("title", ""),
            job_data.get("budget", ""),
            job_data.get("score", ""),
            job_data.get("status", ""),
            job_data.get("url", ""),
            job_data.get("proposal", ""),
            ", ".join(job_data.get("matched_skills", [])),
        ])
        logger.info("Logged: %s", job_data.get("title", "Unknown"))
        return True
    except Exception as exc:
        logger.error("Log error: %s", exc)
        return False
