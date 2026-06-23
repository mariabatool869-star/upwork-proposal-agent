"""
Gmail API — fetch Vollna alerts (HTML + text) and create proposal drafts.
"""
import base64
import logging
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

import config

logger = logging.getLogger(__name__)


def get_gmail_service():
    """Authenticate via web OAuth credentials and return Gmail service."""
    import json
    import pickle
    import os

    creds = None
    token_path = config.TOKEN_FILE
    creds_path = config.CREDENTIALS_FILE

    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            with open(creds_path, "r") as f:
                client_config = json.load(f)

            web_cfg = client_config.get("web") or client_config.get("installed")
            if not web_cfg:
                raise ValueError("credentials file must contain 'web' or 'installed' key")

            redirect_uri = web_cfg.get("redirect_uris", ["http://localhost"])[0]
            flow = Flow.from_client_config(
                {"web": web_cfg} if "web" in client_config else {"installed": web_cfg},
                scopes=config.GMAIL_SCOPES,
                redirect_uri=redirect_uri,
            )
            auth_url, _ = flow.authorization_url(prompt="consent")
            print("\nOpen this URL in your browser:\n", auth_url)
            code = input("\nPaste the authorization code: ").strip()
            flow.fetch_token(code=code)
            creds = flow.credentials

        with open(token_path, "wb") as token:
            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)


def fetch_vollna_emails(service, max_results=20):
    """Fetch recent Vollna emails with HTML and plain-text bodies."""
    query = f"from:{config.VOLLNA_SENDER}"
    result = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )

    messages = result.get("messages", [])
    if not messages:
        logger.info("No Vollna emails found")
        return []

    emails = []
    for meta in messages:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=meta["id"], format="full")
            .execute()
        )
        parsed = _parse_message(msg)
        if parsed.get("body_html") or parsed.get("body_text") or parsed.get("body"):
            emails.append(parsed)

    logger.info(f"Fetched {len(emails)} Vollna emails")
    return emails


def _parse_message(msg):
    headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
    body_html, body_text = _extract_body(msg["payload"])

    return {
        "id": msg["id"],
        "subject": headers.get("subject", ""),
        "from": headers.get("from", ""),
        "body_html": body_html,
        "body_text": body_text,
        "body": body_text or body_html,
    }


def _extract_body(payload):
    html_parts, text_parts = [], []

    def walk(part):
        mime = part.get("mimeType", "")
        data = part.get("body", {}).get("data")
        if data:
            decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            if mime == "text/html":
                html_parts.append(decoded)
            elif mime == "text/plain":
                text_parts.append(decoded)
        for sub in part.get("parts", []):
            walk(sub)

    walk(payload)
    return "\n".join(html_parts), "\n".join(text_parts)


def create_draft(service, subject, body, to_email=None):
    """Create Gmail draft. Returns (draft_id, draft_link) or (None, None)."""
    try:
        message = MIMEText(body, "plain", "utf-8")
        message["subject"] = subject
        if to_email:
            message["to"] = to_email

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        draft = (
            service.users()
            .drafts()
            .create(userId="me", body={"message": {"raw": raw}})
            .execute()
        )
        draft_id = draft["id"]
        link = f"https://mail.google.com/mail/u/0/#drafts?compose={draft_id}"
        logger.info(f"Draft created: {subject}")
        return draft_id, link
    except Exception as exc:
        logger.error(f"Failed to create draft: {exc}")
        return None, None
