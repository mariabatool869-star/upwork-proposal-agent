"""
Shared Google Sheets connection (service account).
Used by the agent (sheets_logger) and the Streamlit dashboard (data_utils).
"""

import logging

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from config_loader import load_config

config = load_config()

logger = logging.getLogger(__name__)

SHEETS_SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def _credentials_from_streamlit_secrets():
    try:
        import streamlit as st

        if "gcp_service_account" not in st.secrets:
            return None

        info = dict(st.secrets["gcp_service_account"])
        return ServiceAccountCredentials.from_json_keyfile_dict(
            info,
            SHEETS_SCOPE,  # pyright: ignore[reportArgumentType]
        )
    except Exception:
        return None


def _credentials_from_file():
    creds_path = config.SHEETS_CREDENTIALS_FILE
    if not creds_path.exists():
        return None

    return ServiceAccountCredentials.from_json_keyfile_name(
        str(creds_path),
        SHEETS_SCOPE,  # pyright: ignore[reportArgumentType]
    )


def get_sheets_workbook():
    """Return the spreadsheet workbook, or None if unavailable."""
    if hasattr(config, "apply_streamlit_secrets"):
        config.apply_streamlit_secrets()

    if not config.GOOGLE_SHEETS_ID:
        logger.warning("GOOGLE_SHEETS_ID not set")
        return None

    creds = _credentials_from_streamlit_secrets() or _credentials_from_file()
    if not creds:
        logger.error("Sheets service account credentials not found")
        return None

    try:
        client = gspread.authorize(creds)  # type: ignore[arg-type]
        workbook = client.open_by_key(config.GOOGLE_SHEETS_ID)
        logger.info("Connected to Google Sheets")
        return workbook
    except Exception as exc:
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
