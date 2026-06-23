"""
Load job data from Google Sheets for the dashboard.
"""

import logging
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config_loader import load_config
from sheets_client import diagnose_sheets_connection, get_worksheet

config = load_config()

logger = logging.getLogger(__name__)

STATUS_ALIASES = {
    "drafted": config.STATUS_DRAFTED,
    "skipped": config.STATUS_SKIPPED,
    "error": config.STATUS_ERROR,
}


def get_jobs_dataframe() -> pd.DataFrame:
    """Fetch all rows from the job log spreadsheet."""
    try:
        worksheet = get_worksheet(0)
        if not worksheet:
            return pd.DataFrame()

        records = worksheet.get_all_records()
        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)
        df["_row"] = range(2, len(df) + 2)  # matches Google Sheet row numbers
        return _normalize(df)

    except Exception as exc:
        logger.error("Failed to load Sheets: %s", exc)
        return pd.DataFrame()


def get_sheets_status() -> tuple[bool, str]:
    """Connection check for the dashboard (Streamlit Cloud troubleshooting)."""
    return diagnose_sheets_connection()


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    if "Timestamp" in df.columns and "Date" not in df.columns:
        df = df.rename(columns={"Timestamp": "Date"})

    if "Status" in df.columns:
        df["Status"] = df["Status"].replace(STATUS_ALIASES)

    if "Score" in df.columns:
        scores = pd.to_numeric(df["Score"], errors="coerce")
        df["Score"] = scores.fillna(0) if isinstance(scores, pd.Series) else scores

    if "Date" in df.columns:
        cleaned = df["Date"].astype(str).str.replace(" UTC", "", regex=False)
        df["Date"] = pd.to_datetime(cleaned, errors="coerce", utc=True, format="mixed")

    return df


def get_recent_jobs(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    """Return the newest jobs first (Sheets appends rows at the bottom)."""
    if df.empty:
        return df

    columns = ["Date", "Title", "Budget", "Score", "Status"]
    work = df.copy()

    # Sheet row order is the source of truth — newest rows are appended last.
    if "_row" in work.columns:
        work = work.sort_values("_row", ascending=False)
    elif "Date" in work.columns:
        work = work.sort_values("Date", ascending=False, na_position="last")
    else:
        work = work.iloc[::-1]

    available = [col for col in columns if col in work.columns]
    return work.head(limit)[available].reset_index(drop=True)


def get_stats(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "total_jobs": 0,
            "drafts": 0,
            "skipped": 0,
            "match_rate": 0,
            "avg_score": 0,
        }

    total = len(df)
    drafts = len(df[df["Status"] == config.STATUS_DRAFTED]) if "Status" in df.columns else 0
    skipped = len(df[df["Status"] == config.STATUS_SKIPPED]) if "Status" in df.columns else 0
    if "Score" in df.columns:
        score_values = [float(x) for x in df["Score"].tolist() if pd.notna(x)]
        avg = round(sum(score_values) / len(score_values), 1) if score_values else 0.0
    else:
        avg = 0.0

    return {
        "total_jobs": total,
        "drafts": drafts,
        "skipped": skipped,
        "match_rate": round((drafts / total * 100) if total else 0, 1),
        "avg_score": avg,
    }


def get_daily_chart(df: pd.DataFrame) -> pd.DataFrame:
    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    full = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    if df.empty or "Date" not in df.columns:
        return pd.DataFrame({"Day": labels, "Jobs": [0] * 7})

    valid = df.dropna(subset=["Date"])
    if valid.empty:
        return pd.DataFrame({"Day": labels, "Jobs": [0] * 7})

    counts = valid.groupby(valid["Date"].dt.day_name()).size().reindex(full, fill_value=0)
    return pd.DataFrame({"Day": labels, "Jobs": counts.values})
