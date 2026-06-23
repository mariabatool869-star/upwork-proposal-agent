"""Vercel serverless API — dashboard data from Google Sheets."""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.sheets_data import build_dashboard_payload


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            payload = build_dashboard_payload()
            status = 200 if payload.get("ok") else 503
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            body = json.dumps(
                {"ok": False, "message": f"Server error: {exc}"}
            ).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
