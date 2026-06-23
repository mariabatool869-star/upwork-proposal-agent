"""
Shared Google Sheets connection (service account).
Used by the agent (sheets_logger) and the Streamlit dashboard (data_utils).
"""

import logging

import gspread
from google.oauth2.service_account import Credentials

from config_loader import load_config

config = load_config()

logger = logging.getLogger(__name__)

SHEETS_SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_last_error: str | None = None


def _normalize_service_account_info(info: dict) -> dict:
    """Fix private_key newlines when pasted into Streamlit secrets TOML."""
    normalized = {str(key): value for key, value in info.items()}
    private_key = normalized.get("private_key", "")
    if isinstance(private_key, str) and "\\n" in private_key:
        normalized["private_key"] = private_key.replace("\\n", "\n")
    return normalized


def get_last_sheets_error() -> str | None:
    return _last_error


def diagnose_sheets_connection() -> tuple[bool, str]:
    """Return (connected, message) for dashboard troubleshooting."""
    global _last_error

    if hasattr(config, "apply_streamlit_secrets"):
        config.apply_streamlit_secrets()

    if not config.GOOGLE_SHEETS_ID:
        return False, (
            "GOOGLE_SHEETS_ID is not set. Add it in Streamlit Cloud → Settings → Secrets, "
            "then reboot the app."
        )

    creds = _credentials_from_streamlit_secrets() or _credentials_from_file()
    if not creds:
        return False, (
            "Google Sheets credentials missing. Add a [gcp_service_account] section in "
            "Streamlit secrets (copy from credentials/sheets_service.json). "
            "Locally run: python prepare_streamlit_secrets.py"
        )

    try:
        client = gspread.authorize(creds)
        workbook = client.open_by_key(config.GOOGLE_SHEETS_ID)
        worksheet = workbook.get_worksheet(0)
        row_count = max(len(worksheet.get_all_values()) - 1, 0) if worksheet else 0
        _last_error = None
        return True, f"Connected to “{workbook.title}” ({row_count} job row(s))."
    except gspread.exceptions.SpreadsheetNotFound:
        _last_error = "Spreadsheet not found"
        return False, (
            "Spreadsheet not found. Check GOOGLE_SHEETS_ID in Streamlit secrets."
        )
    except gspread.exceptions.APIError as exc:
        _last_error = str(exc)
        email = _service_account_email(creds)
        if email:
            return False, (
                f"Permission denied. Share your Google Sheet with **{email}** "
                "(Editor access), then refresh."
            )
        return False, f"Google Sheets API error: {exc}"
    except Exception as exc:
        _last_error = str(exc)
        return False, f"Could not connect to Google Sheets: {exc}"


def _service_account_email(creds) -> str | None:
    try:
        return getattr(creds, "service_account_email", None)
    except Exception:
        return None


def _credentials_from_streamlit_secrets():
    try:
        import streamlit as st

        if "gcp_service_account" not in st.secrets:
            return None

        info = _normalize_service_account_info(dict(st.secrets["gcp_service_account"]))
        return Credentials.from_service_account_info(info, scopes=SHEETS_SCOPE)
    except Exception as exc:
        global _last_error
        _last_error = f"Invalid Streamlit secrets: {exc}"
        return None


def _credentials_from_file():
    creds_path = config.SHEETS_CREDENTIALS_FILE
    if not creds_path.exists():
        return None

    return Credentials.from_service_account_file(str(creds_path), scopes=SHEETS_SCOPE)


def get_sheets_workbook():
    """Return the spreadsheet workbook, or None if unavailable."""
    global _last_error

    if hasattr(config, "apply_streamlit_secrets"):
        config.apply_streamlit_secrets()

    if not config.GOOGLE_SHEETS_ID:
        _last_error = "GOOGLE_SHEETS_ID not set"
        logger.warning(_last_error)
        return None

    creds = _credentials_from_streamlit_secrets() or _credentials_from_file()
    if not creds:
        _last_error = "Sheets service account credentials not found"
        logger.error(_last_error)
        return None

    try:
        client = gspread.authorize(creds)
        workbook = client.open_by_key(config.GOOGLE_SHEETS_ID)
        logger.info("Connected to Google Sheets")
        _last_error = None
        return workbook
    except Exception as exc:
        _last_error = str(exc)
        logger.error("Could not connect to Sheets: %s", exc)
        return None


def get_worksheet(index=0):
    """Return worksheet at index, or None."""
    workbook = get_sheets_workbook()
    if not workbook:
        return None
    return workbook.get_worksheet(index)


def update_row_status(sheet_row: int, status: str) -> bool:
    """Update the Status cell for a sheet row (1-based, row 1 = headers)."""
    worksheet = get_worksheet(0)
    if not worksheet or sheet_row < 2:
        return False

    try:
        headers = worksheet.row_values(1)
        if "Status" not in headers:
            return False
        status_col = headers.index("Status") + 1
        worksheet.update_cell(sheet_row, status_col, status)
        return True
    except Exception as exc:
        logger.error("Failed to update row %s: %s", sheet_row, exc)
        return False
