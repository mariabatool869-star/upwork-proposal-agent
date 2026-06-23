"""Load Google Sheets data for the Vercel dashboard API."""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import project_config

SHEETS_SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

STATUS_DRAFTED = project_config.STATUS_DRAFTED


def _credentials() -> Credentials | None:
    sheet_id = os.getenv("GOOGLE_SHEETS_ID", "").strip()
    if not sheet_id:
        return None

    raw = os.getenv("GCP_SERVICE_ACCOUNT_JSON", "").strip()
    if raw:
        info = json.loads(raw)
        if isinstance(info.get("private_key"), str):
            info["private_key"] = info["private_key"].replace("\\n", "\n")
        return Credentials.from_service_account_info(info, scopes=SHEETS_SCOPE)

    creds_path = project_config.SHEETS_CREDENTIALS_FILE
    if creds_path.exists():
        return Credentials.from_service_account_file(str(creds_path), scopes=SHEETS_SCOPE)

    return None


def _parse_rows(records: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for index, record in enumerate(records, start=2):
        row = dict(record)
        row["_row"] = index
        if "Timestamp" in row and "Date" not in row:
            row["Date"] = row.pop("Timestamp")
        try:
            row["Score"] = float(row.get("Score") or 0)
        except (TypeError, ValueError):
            row["Score"] = 0.0
        rows.append(row)
    return rows


def _stats(rows: list[dict]) -> dict:
    if not rows:
        return {
            "total_jobs": 0,
            "drafts": 0,
            "skipped": 0,
            "match_rate": 0,
            "avg_score": 0,
        }

    drafts = sum(1 for row in rows if row.get("Status") == STATUS_DRAFTED)
    skipped = sum(1 for row in rows if row.get("Status") == project_config.STATUS_SKIPPED)
    scores = [float(row["Score"]) for row in rows if row.get("Score") is not None]
    avg = round(sum(scores) / len(scores), 1) if scores else 0.0
    total = len(rows)

    return {
        "total_jobs": total,
        "drafts": drafts,
        "skipped": skipped,
        "match_rate": round((drafts / total * 100) if total else 0, 1),
        "avg_score": avg,
    }


def _daily_chart(rows: list[dict]) -> list[dict]:
    counts = {name: 0 for name in DAY_NAMES}
    for row in rows:
        raw = str(row.get("Date", "")).replace(" UTC", "").strip()
        if not raw:
            continue
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            counts[parsed.strftime("%A")] = counts.get(parsed.strftime("%A"), 0) + 1
        except ValueError:
            continue

    return [{"day": label, "jobs": counts[name]} for label, name in zip(DAY_LABELS, DAY_NAMES)]


def _recent_jobs(rows: list[dict], limit: int = 10) -> list[dict]:
    ordered = sorted(rows, key=lambda row: row.get("_row", 0), reverse=True)
    recent = []
    for row in ordered[:limit]:
        date_value = str(row.get("Date", ""))[:19]
        recent.append(
            {
                "date": date_value,
                "title": row.get("Title", ""),
                "budget": row.get("Budget", ""),
                "score": row.get("Score", 0),
                "status": row.get("Status", ""),
            }
        )
    return recent


def _drafts(rows: list[dict]) -> list[dict]:
    drafted = [row for row in rows if row.get("Status") == STATUS_DRAFTED]
    drafted.sort(key=lambda row: row.get("_row", 0), reverse=True)
    return [
        {
            "title": row.get("Title", ""),
            "budget": row.get("Budget", ""),
            "score": row.get("Score", 0),
            "url": row.get("URL", ""),
            "proposal": row.get("Proposal", ""),
        }
        for row in drafted
    ]


def build_dashboard_payload() -> dict:
    sheet_id = os.getenv("GOOGLE_SHEETS_ID", project_config.GOOGLE_SHEETS_ID).strip()
    creds = _credentials()

    profile = {
        "title": project_config.PROFILE.get("title", ""),
        "rate": project_config.PROFILE.get("rate", ""),
        "bio": project_config.PROFILE.get("bio", ""),
        "skills": project_config.PROFILE.get("skills", [])[:12],
        "experience_highlights": project_config.PROFILE.get("experience_highlights", []),
        "my_name": project_config.MY_NAME,
    }

    if not sheet_id:
        return {
            "ok": False,
            "message": "GOOGLE_SHEETS_ID is not set in Vercel environment variables.",
            "profile": profile,
            "stats": _stats([]),
            "recent": [],
            "daily": _daily_chart([]),
            "status_counts": {},
            "drafts": [],
            "scores": [],
        }

    if not creds:
        return {
            "ok": False,
            "message": (
                "GCP_SERVICE_ACCOUNT_JSON is not set in Vercel. "
                "Run: python prepare_vercel_env.py"
            ),
            "profile": profile,
            "stats": _stats([]),
            "recent": [],
            "daily": _daily_chart([]),
            "status_counts": {},
            "drafts": [],
            "scores": [],
        }

    try:
        client = gspread.authorize(creds)
        worksheet = client.open_by_key(sheet_id).get_worksheet(0)
        records = worksheet.get_all_records()
        rows = _parse_rows(records)
        status_counts = dict(Counter(row.get("Status", "Unknown") for row in rows))
        scores = [float(row["Score"]) for row in rows if row.get("Score") is not None]

        return {
            "ok": True,
            "message": f'Connected to "{worksheet.spreadsheet.title}" ({len(rows)} jobs)',
            "profile": profile,
            "stats": _stats(rows),
            "recent": _recent_jobs(rows),
            "daily": _daily_chart(rows),
            "status_counts": status_counts,
            "drafts": _drafts(rows),
            "scores": scores,
        }
    except gspread.exceptions.APIError:
        email = getattr(creds, "service_account_email", "your service account")
        return {
            "ok": False,
            "message": f"Permission denied. Share the sheet with {email} (Editor).",
            "profile": profile,
            "stats": _stats([]),
            "recent": [],
            "daily": _daily_chart([]),
            "status_counts": {},
            "drafts": [],
            "scores": [],
        }
    except Exception as exc:
        return {
            "ok": False,
            "message": f"Could not load Google Sheets: {exc}",
            "profile": profile,
            "stats": _stats([]),
            "recent": [],
            "daily": _daily_chart([]),
            "status_counts": {},
            "drafts": [],
            "scores": [],
        }
