"""
Gmail reader — connects to Gmail API and fetches Vollna job alert emails.
"""

import base64
import logging
from email.mime.text import MIMEText
from email.utils import parsedate_to_datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import config

logger = logging.getLogger(__name__)


def get_google_credentials():
    """
    Authenticate with Google and return credentials.
    Shared by Gmail and Google Sheets APIs.
    On first run, opens a browser window for you to sign in.
    """
    creds = None

    if config.TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(config.TOKEN_FILE), config.GMAIL_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired Google credentials...")
            creds.refresh(Request())
        else:
            if not config.CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"Missing {config.CREDENTIALS_FILE.name}. "
                    "Download OAuth credentials from Google Cloud Console — see README.md."
                )
            logger.info("Opening browser for Google sign-in (first time only)...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(config.CREDENTIALS_FILE), config.GMAIL_SCOPES
            )
            creds = flow.run_local_server(port=0)

        config.TOKEN_FILE.write_text(creds.to_json())
        logger.info("Google credentials saved to token.json")

    return creds


def get_gmail_service():
    """Return an authenticated Gmail API service object."""
    return build("gmail", "v1", credentials=get_google_credentials())


def fetch_vollna_emails(service, max_results=20, after_date=None):
    """
    Fetch unread (or recent) emails from info@vollna.com.

    Returns a list of dicts:
        { "id", "subject", "date", "body_html", "body_text" }
    """
    query_parts = [f"from:{config.VOLLNA_SENDER}"]
    if after_date:
        # Gmail uses YYYY/MM/DD format
        query_parts.append(f"after:{after_date}")

    query = " ".join(query_parts)
    logger.info(f"Searching Gmail: {query}")

    result = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )

    messages = result.get("messages", [])
    if not messages:
        logger.info("No Vollna emails found.")
        return []

    logger.info(f"Found {len(messages)} Vollna email(s)")
    emails = []

    for msg_meta in messages:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_meta["id"], format="full")
            .execute()
        )
        emails.append(_parse_message(msg))

    return emails


def _parse_message(msg):
    """Extract subject, date, and body from a Gmail API message object."""
    headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
    subject = headers.get("subject", "(no subject)")
    date_str = headers.get("date", "")

    try:
        date = parsedate_to_datetime(date_str)
    except Exception:
        date = None

    body_html, body_text = _extract_body(msg["payload"])

    return {
        "id": msg["id"],
        "subject": subject,
        "date": date,
        "body_html": body_html,
        "body_text": body_text,
    }


def _extract_body(payload):
    """Recursively extract HTML and plain-text body from email payload."""
    html_parts = []
    text_parts = []

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
    """
    Create a Gmail draft with the proposal.
    Returns the draft ID and a link to open it in Gmail.
    """
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
    # Link format to open drafts in Gmail web UI
    draft_link = f"https://mail.google.com/mail/u/0/#drafts?compose={draft_id}"

    logger.info(f"Draft created: {subject}")
    return draft_id, draft_link
