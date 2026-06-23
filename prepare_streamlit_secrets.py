"""
Print Streamlit Cloud secrets TOML from local .env + credentials/sheets_service.json.

Run locally (do not commit the output):
    python prepare_streamlit_secrets.py
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
    private_key = sa["private_key"].replace("\n", "\\n")

    print("# Paste into Streamlit Cloud → Settings → Secrets\n")
    print(f'GOOGLE_SHEETS_ID = "{sheet_id}"')
    print(f'MY_NAME = "{ENV.get("MY_NAME", "Maria")}"')
    if ENV.get("GEMINI_API_KEY"):
        print(f'GEMINI_API_KEY = "{ENV["GEMINI_API_KEY"]}"')
    if ENV.get("SLACK_WEBHOOK_URL"):
        print(f'SLACK_WEBHOOK_URL = "{ENV["SLACK_WEBHOOK_URL"]}"')
    print()
    print("[gcp_service_account]")
    print(f'type = "{sa["type"]}"')
    print(f'project_id = "{sa["project_id"]}"')
    print(f'private_key_id = "{sa["private_key_id"]}"')
    print(f'private_key = "{private_key}"')
    print(f'client_email = "{sa["client_email"]}"')
    print(f'client_id = "{sa["client_id"]}"')
    print(f'auth_uri = "{sa["auth_uri"]}"')
    print(f'token_uri = "{sa["token_uri"]}"')
    print(f'auth_provider_x509_cert_url = "{sa["auth_provider_x509_cert_url"]}"')
    print(f'client_x509_cert_url = "{sa["client_x509_cert_url"]}"')
    if sa.get("universe_domain"):
        print(f'universe_domain = "{sa["universe_domain"]}"')
    print()
    print("# Share your Google Sheet with this email (Editor):")
    print(f"#   {sa['client_email']}")


if __name__ == "__main__":
    main()
