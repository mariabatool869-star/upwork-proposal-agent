"""
Print Vercel environment variable values from local files.

Run locally (do not commit the output):
    python prepare_vercel_env.py

Then paste into Vercel → Project → Settings → Environment Variables.
"""

import json
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent
ENV = dotenv_values(ROOT / ".env")
SHEETS_JSON = ROOT / "credentials" / "sheets_service.json"


def main() -> None:
    if not SHEETS_JSON.exists():
        raise SystemExit(f"Missing {SHEETS_JSON}")

    sheet_id = (ENV.get("GOOGLE_SHEETS_ID") or "").strip()
    if not sheet_id:
        raise SystemExit("GOOGLE_SHEETS_ID is empty in .env")

    sa = json.loads(SHEETS_JSON.read_text(encoding="utf-8"))
    sa_json = json.dumps(sa)

    print("Add these in Vercel → Settings → Environment Variables:\n")
    print("Name: GOOGLE_SHEETS_ID")
    print(f"Value: {sheet_id}\n")
    print("Name: GCP_SERVICE_ACCOUNT_JSON")
    print("Value: (paste the single-line JSON below)\n")
    print(sa_json)
    print()
    print("Share your Google Sheet with (Editor):")
    print(f"  {sa['client_email']}")
    print()
    print("Optional:")
    print(f"  MY_NAME = {ENV.get('MY_NAME', 'Maria')}")


if __name__ == "__main__":
    main()
