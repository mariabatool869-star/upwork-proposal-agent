"""
Vercel entrypoint — serves dashboard (public/) and /api/jobs.

Local agent: python run_agent.py
"""

from __future__ import annotations

import traceback
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

ROOT = Path(__file__).parent
PUBLIC = ROOT / "public"

app = FastAPI()


@app.get("/api/jobs")
def api_jobs():
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


@app.get("/")
def index():
    return FileResponse(PUBLIC / "index.html")


@app.get("/css/{asset:path}")
def css(asset: str):
    return FileResponse(PUBLIC / "css" / asset, media_type="text/css")


@app.get("/js/{asset:path}")
def js(asset: str):
    return FileResponse(PUBLIC / "js" / asset, media_type="application/javascript")
