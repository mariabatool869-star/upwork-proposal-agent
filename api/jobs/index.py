"""Vercel API — /api/jobs reads Google Sheets for the dashboard."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

app = FastAPI()


@app.get("/")
@app.get("/jobs")
def get_jobs():
    try:
        from lib.sheets_data import build_dashboard_payload

        payload = build_dashboard_payload()
        status = 200 if payload.get("ok") else 503
        return JSONResponse(content=payload, status_code=status)
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "message": "Server error loading dashboard data.",
                "detail": str(exc),
                "trace": traceback.format_exc(),
            },
        )
