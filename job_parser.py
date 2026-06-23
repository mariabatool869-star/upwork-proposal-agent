"""
Job parser — extracts jobs from Vollna HTML emails.
Vollna uses vollna.com/go links (not direct Upwork URLs) with job details in HTML.
"""

import logging
import re
from urllib.parse import unquote, urlparse, parse_qs

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

UPWORK_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?upwork\.com/(?:jobs|ab/jobs/search)/[^\s\"'<>]+",
    re.IGNORECASE,
)

SUMMARY_SUBJECT_PATTERN = re.compile(
    r"^here are \d+ new freelance jobs for you\.?$",
    re.I,
)

NEW_JOB_SUBJECT_PATTERN = re.compile(r"^New Job:\s*(.+)$", re.I)

SKIP_LINK_TEXTS = {
    "view project", "open results", "show live feed", "pick a plan",
    "unsubscribe", "my jobs", "notifications settings", "contact us",
    "show live feed", "view project →", "view project",
}

BUDGET_PATTERNS = [
    re.compile(r"hourly rate[:\s]*([\d,]+(?:\.\d+)?)\s*[-–]\s*([\d,]+(?:\.\d+)?)\s*usd", re.I),
    re.compile(r"([\d,]+(?:\.\d+)?)\s*[-–]\s*([\d,]+(?:\.\d+)?)\s*usd\s*\n?\s*hourly", re.I),
    re.compile(r"\$\s*([\d,]+(?:\.\d+)?)\s*[-–]\s*\$\s*([\d,]+(?:\.\d+)?)\s*/?\s*hr", re.I),
    re.compile(r"\$\s*([\d,]+(?:\.\d+)?)\s*/?\s*hr", re.I),
    re.compile(r"([\d,]+(?:\.\d+)?)\s*[-–]\s*([\d,]+(?:\.\d+)?)\s*usd", re.I),
]


def parse_vollna_email(email_data):
    """Return list of job dicts from one Vollna email."""
    if isinstance(email_data, str):
        email_data = {"body": email_data, "body_text": email_data, "subject": ""}

    html = email_data.get("body_html") or ""
    text = email_data.get("body_text") or email_data.get("body") or ""
    subject = email_data.get("subject") or ""
    email_id = email_data.get("id", "")

    content = html if html.strip() else text
    soup = BeautifulSoup(content, "lxml") if html.strip() else None
    full_text = soup.get_text("\n", strip=True) if soup else text

    jobs = []
    seen_pids = set()

    if soup:
        for anchor in soup.find_all("a", href=True):
            href = _unwrap_tracking(unquote(str(anchor["href"])))
            title = anchor.get_text(strip=True)

            if not _is_job_link(href, title):
                continue

            pid = _extract_pid(href)
            if pid and pid in seen_pids:
                continue
            if pid:
                seen_pids.add(pid)

            if not _is_valid_job_title(title):
                title = _find_title_near(anchor, subject)
            if not _is_valid_job_title(title):
                continue

            url = _resolve_job_url(href)
            block = _parent_block_text(anchor)
            budget_val, budget_type, budget_display = _extract_budget(
                block + "\n" + full_text, title
            )
            description = _extract_description(full_text, title)

            jobs.append(_build_job(
                email_id, title, description, budget_val, budget_type,
                budget_display, url,
            ))

    # Subject-only email: "New Job: Title Here"
    if not jobs:
        match = NEW_JOB_SUBJECT_PATTERN.match(subject.strip())
        if match:
            title = match.group(1).strip()
            budget_val, budget_type, budget_display = _extract_budget(full_text, title)
            description = _extract_description(full_text, title)
            url = _find_first_job_url(soup, full_text)
            jobs.append(_build_job(
                email_id, title, description, budget_val, budget_type,
                budget_display, url,
            ))

    for job in jobs:
        logger.info(
            f"Parsed job: {job['title']} | Budget: {job['budget_display']} | "
            f"URL: {(job.get('url') or 'vollna link')[:80]}"
        )

    return jobs


def parse_manual_url(url, title=None, budget=None, description=None):
    budget_val, budget_type, display = None, None, "Not specified"
    if budget is not None:
        if isinstance(budget, (int, float)):
            budget_val, budget_type, display = float(budget), "hourly", f"${budget}/hr"
        else:
            budget_val, budget_type, display = _extract_budget(str(budget), title or "")
    return {
        "title": title or "Manual Test Job",
        "description": description or "",
        "budget": budget_val,
        "budget_display": display,
        "budget_type": budget_type,
        "url": url,
        "client_name": "there",
        "client_rating": None,
    }


def _unwrap_tracking(href):
    """Unwrap AWS tracking redirect URLs."""
    if "awstrack.me" in href:
        match = re.search(r"awstrack\.me/L\d+/(.+)$", href, re.I)
        if match:
            return unquote(match.group(1))
    return href


def _is_job_link(href, link_text):
    """True if this anchor points to a Vollna job (not dashboard/settings)."""
    href_l = href.lower()
    text_l = link_text.lower().strip()

    if any(skip in text_l for skip in SKIP_LINK_TEXTS):
        return False
    if len(link_text.strip()) < 8:
        return False

    if "vollna.com/go" in href_l and "place=title" in href_l:
        return True
    if "vollna.com/go" in href_l and _is_valid_job_title(link_text):
        return True
    if UPWORK_URL_PATTERN.search(href):
        return True
    return False


def _extract_pid(href):
    match = re.search(r"[?&]pid=(\d+)", href)
    return match.group(1) if match else None


def _resolve_job_url(href):
    """Get best URL for the job — prefer embedded Upwork link inside Vollna go URL."""
    href = _unwrap_tracking(href)

    upwork = UPWORK_URL_PATTERN.search(href)
    if upwork:
        return _clean_upwork_url(upwork.group(0))

    if "vollna.com/go" in href.lower():
        qs = parse_qs(urlparse(href).query)
        embedded = qs.get("url", [""])[0]
        for _ in range(3):
            embedded = unquote(embedded)
        if "upwork.com" in embedded:
            return _clean_upwork_url(embedded)
        return href.split("&utm_")[0]

    return href


def _find_first_job_url(soup, full_text):
    if soup:
        for a in soup.find_all("a", href=True):
            href = _unwrap_tracking(unquote(a["href"]))
            if "vollna.com/go" in href.lower():
                return _resolve_job_url(href)
    match = UPWORK_URL_PATTERN.search(full_text)
    return match.group(0) if match else ""


def _is_valid_job_title(title):
    if not title or len(title.strip()) < 8:
        return False
    if SUMMARY_SUBJECT_PATTERN.match(title.strip()):
        return False
    if title.lower().strip() in SKIP_LINK_TEXTS:
        return False
    return True


def _find_title_near(anchor, subject):
    match = NEW_JOB_SUBJECT_PATTERN.match(subject.strip())
    if match:
        return match.group(1).strip()
    parent = anchor.parent
    for _ in range(4):
        if not parent:
            break
        for tag in ("strong", "b", "h1", "h2", "h3", "td"):
            el = parent.find(tag)
            if el:
                t = el.get_text(strip=True)
                if _is_valid_job_title(t):
                    return t
        parent = parent.parent
    return ""


def _parent_block_text(anchor):
    parts = []
    parent = anchor.parent
    for _ in range(4):
        if parent:
            parts.append(parent.get_text("\n", strip=True))
            parent = parent.parent
    return "\n".join(parts)


def _extract_budget(text, title=""):
    if not text:
        return None, None, "Not specified"

    search = text
    if title and title in text:
        idx = text.find(title)
        search = text[idx: idx + 800]

    for pattern in BUDGET_PATTERNS:
        match = pattern.search(search)
        if match:
            groups = [g for g in match.groups() if g]
            raw = match.group(0).lower()
            if "hourly" in raw or "/hr" in raw or "hr" in raw:
                if len(groups) >= 2:
                    low = float(groups[0].replace(",", ""))
                    high = float(groups[1].replace(",", ""))
                    return high, "hourly", f"${groups[0]}-${groups[1]}/hr"
                val = float(groups[0].replace(",", ""))
                return val, "hourly", f"${groups[0]}/hr"
            if len(groups) >= 2:
                val = float(groups[0].replace(",", ""))
                return val, "fixed", f"${groups[0]}-${groups[1]}"
            val = float(groups[0].replace(",", ""))
            return val, "fixed", f"${groups[0]}"

    return None, None, "Not specified"


def _extract_description(full_text, title):
    """Get job description text following the title in the email body."""
    if not full_text or not title:
        return full_text[:3000] if full_text else ""

    idx = full_text.find(title)
    if idx == -1:
        return full_text[:3000]

    desc = full_text[idx + len(title):]
    stop_markers = [
        "Open results", "Show live feed", "Already found a job",
        "Filter Result", "Your filter", "Unsubscribe",
        "Your Vollna trial", "Pick a plan", "2026 © Vollna",
    ]
    for marker in stop_markers:
        pos = desc.find(marker)
        if pos > 50:
            desc = desc[:pos]

    lines = [
        ln.strip() for ln in desc.splitlines()
        if len(ln.strip()) > 20
        and "unsubscribe" not in ln.lower()
        and "vollna trial" not in ln.lower()
    ]
    return "\n".join(lines[:40])[:3000]


def _clean_upwork_url(url):
    parsed = urlparse(url)
    if "upwork.com" in parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
    return url


def _build_job(email_id, title, description, budget_val, budget_type, budget_display, url):
    return {
        "email_id": email_id,
        "title": title,
        "description": description,
        "budget": budget_val,
        "budget_display": budget_display,
        "budget_type": budget_type,
        "url": url or "",
        "client_name": "there",
        "client_rating": None,
    }
