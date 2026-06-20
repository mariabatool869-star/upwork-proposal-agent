"""
Job parser — extracts job title, budget, URL, and description from Vollna emails.
"""

import logging
import re
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Common Upwork job URL patterns
UPWORK_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?upwork\.com/(?:jobs|ab/jobs/search)/[^\s\"'<>]+",
    re.IGNORECASE,
)

# Budget patterns: "$50/hr", "$30-50/hr", "$500", "$1,000-$5,000", "Hourly: $30"
BUDGET_PATTERNS = [
    re.compile(r"\$\s*([\d,]+(?:\.\d{2})?)\s*[-–]\s*\$\s*([\d,]+(?:\.\d{2})?)\s*/?\s*hr", re.I),
    re.compile(r"\$\s*([\d,]+(?:\.\d{2})?)\s*/?\s*hr", re.I),
    re.compile(r"hourly[:\s]+\$\s*([\d,]+(?:\.\d{2})?)", re.I),
    re.compile(r"\$\s*([\d,]+(?:\.\d{2})?)\s*[-–]\s*\$\s*([\d,]+(?:\.\d{2})?)(?!\s*/?\s*hr)", re.I),
    re.compile(r"\$\s*([\d,]+(?:\.\d{2})?)(?!\s*/?\s*hr)", re.I),
    re.compile(r"budget[:\s]+\$\s*([\d,]+(?:\.\d{2})?)", re.I),
]


def parse_vollna_email(email_data):
    """
    Parse a Vollna alert email into one or more structured job dicts.

    Some Vollna emails contain multiple jobs — we extract each Upwork link.

    Input: dict from gmail_reader with body_html, body_text, subject
    Output: list of job dicts
    """
    html = email_data.get("body_html", "")
    text = email_data.get("body_text", "")
    subject = email_data.get("subject", "")
    email_id = email_data.get("id")

    content = html if html.strip() else text
    soup = BeautifulSoup(content, "lxml") if html.strip() else None

    jobs = _extract_all_jobs(soup, content, text, subject, email_id)

    if not jobs:
        # Fallback: single job from whole email
        jobs = [_build_job(email_id, subject, "Not specified", "unknown", "", text, "there")]

    for job in jobs:
        logger.info(
            f"Parsed job: {job['title']} | Budget: {job['budget']} | "
            f"URL: {job['url'][:60] if job['url'] else 'N/A'}..."
        )

    return jobs


def _unwrap_tracking_url(href):
    """
    Extract the real Upwork URL from email tracking wrappers.
    Vollna emails often use awstrack.me links with the real URL embedded inside.
    """
    href = unquote(href)

    # Direct Upwork link
    match = UPWORK_URL_PATTERN.search(href)
    if match:
        return _clean_url(match.group(0))

    # Upwork URL embedded inside a tracking link (common in Vollna emails)
    embedded = re.search(
        r"(https?://(?:www\.)?upwork\.com/[^\s\"'<>]+)",
        href,
        re.IGNORECASE,
    )
    if embedded:
        return _clean_url(unquote(embedded.group(1)))

    # Vollna redirect links that may contain the job path
    if "vollna.com" in href:
        match = UPWORK_URL_PATTERN.search(href)
        if match:
            return _clean_url(match.group(0))

    return ""


def _extract_all_jobs(soup, content, text, subject, email_id):
    """Find every Upwork job link in the email and build a job dict for each."""
    jobs = []
    seen_urls = set()

    if soup:
        for a in soup.find_all("a", href=True):
            href = unquote(a["href"])
            url = _unwrap_tracking_url(href)
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            title = a.get_text(strip=True) or subject
            if len(title) < 5:
                title = _extract_title(soup, text, subject)

            # Look for budget text near this link (within parent block)
            block_text = ""
            parent = a.parent
            for _ in range(3):
                if parent:
                    block_text = parent.get_text(" ", strip=True)
                    parent = parent.parent

            budget, budget_type = _extract_budget(None, block_text + " " + text)
            description = block_text or _extract_description(soup, text)

            jobs.append(
                _build_job(email_id, title, budget, budget_type, url, description, "there")
            )

    # Also scan raw content for URLs not in <a> tags
    for match in UPWORK_URL_PATTERN.finditer(content):
        url = _clean_url(unquote(match.group(0)))
        if url in seen_urls:
            continue
        seen_urls.add(url)
        budget, budget_type = _extract_budget(soup, text + " " + subject)
        jobs.append(
            _build_job(
                email_id,
                _extract_title(soup, text, subject),
                budget,
                budget_type,
                url,
                _extract_description(soup, text),
                "there",
            )
        )

    # Fallback: unwrap tracking URLs from raw HTML when no direct upwork.com links found
    if not jobs:
        for tracking_match in re.finditer(r'https?://[^\s"\'<>]+', content):
            url = _unwrap_tracking_url(tracking_match.group(0))
            if url and url not in seen_urls:
                seen_urls.add(url)
                budget, budget_type = _extract_budget(soup, text + " " + subject)
                jobs.append(
                    _build_job(
                        email_id,
                        _extract_title(soup, text, subject),
                        budget,
                        budget_type,
                        url,
                        _extract_description(soup, text),
                        "there",
                    )
                )

    return jobs


def _build_job(email_id, title, budget, budget_type, url, description, client_name):
    """Assemble a job dict with computed budget fields."""
    return {
        "email_id": email_id,
        "title": title,
        "budget": budget,
        "budget_display": budget,
        "budget_type": budget_type,
        "budget_value": _budget_to_number(budget, budget_type),
        "url": url,
        "description": description,
        "client_name": client_name or "there",
    }


def parse_manual_url(url, title=None, budget=None, description=None):
    """
    Build a job dict from a manual URL (for testing without an email).
    """
    return {
        "email_id": f"manual-{hash(url)}",
        "title": title or "Manual Test Job",
        "budget": budget or "Not specified",
        "budget_display": budget or "Not specified",
        "budget_type": "unknown",
        "budget_value": None,
        "url": url,
        "description": description or f"Manual test job at {url}",
        "client_name": "there",
    }


def _extract_title(soup, text, subject):
    """Get job title from email — usually the first prominent link or heading."""
    if soup:
        # Vollna often puts job title in <a> tags linking to Upwork
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "upwork.com" in href and a.get_text(strip=True):
                title = a.get_text(strip=True)
                if len(title) > 5:
                    return title

        # Try headings
        for tag in ("h1", "h2", "h3", "strong", "b"):
            el = soup.find(tag)
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)

    # Fall back to subject line — strip common prefixes
    clean_subject = re.sub(r"^(new job|job alert|vollna)[:\s-]*", "", subject, flags=re.I).strip()
    if clean_subject:
        return clean_subject

    # Last resort: first non-empty line of plain text
    for line in text.splitlines():
        line = line.strip()
        if line and len(line) > 5 and "unsubscribe" not in line.lower():
            return line[:200]

    return subject or "Unknown Job"


def _extract_url(soup, content):
    """Find the Upwork job URL in the email."""
    if soup:
        for a in soup.find_all("a", href=True):
            href = unquote(a["href"])
            # Follow redirect wrappers sometimes used in emails
            if "upwork.com" in href:
                return _clean_url(href)
            # Some emails wrap links through tracking URLs
            upwork_match = UPWORK_URL_PATTERN.search(href)
            if upwork_match:
                return _clean_url(upwork_match.group(0))

    match = UPWORK_URL_PATTERN.search(content)
    if match:
        return _clean_url(match.group(0))

    return ""


def _clean_url(url):
    """Remove tracking params and normalize Upwork URL."""
    parsed = urlparse(url)
    if "upwork.com" in parsed.netloc:
        # Keep path, drop most query params
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    return url


def _extract_budget(soup, text):
    """Extract budget string and determine if hourly or fixed."""
    search_text = text
    if soup:
        search_text = soup.get_text(" ", strip=True) + " " + text

    for pattern in BUDGET_PATTERNS:
        match = pattern.search(search_text)
        if match:
            groups = [g for g in match.groups() if g]
            if "/hr" in match.group(0).lower() or "hourly" in match.group(0).lower():
                if len(groups) >= 2:
                    budget = f"${groups[0]}-${groups[1]}/hr"
                else:
                    budget = f"${groups[0]}/hr"
                return budget, "hourly"
            else:
                if len(groups) >= 2:
                    budget = f"${groups[0]}-${groups[1]}"
                else:
                    budget = f"${groups[0]}"
                # If text mentions hourly nearby, treat as hourly
                context = search_text[max(0, match.start() - 30) : match.end() + 30].lower()
                if "hr" in context or "hourly" in context:
                    return budget + "/hr", "hourly"
                return budget, "fixed"

    return "Not specified", "unknown"


def _budget_to_number(budget_str, budget_type):
    """Convert budget string to a numeric value for filtering (uses lower bound)."""
    if not budget_str or budget_str == "Not specified":
        return None
    numbers = re.findall(r"[\d,]+(?:\.\d{2})?", budget_str.replace(",", ""))
    if not numbers:
        return None
    try:
        return float(numbers[0].replace(",", ""))
    except ValueError:
        return None


def _extract_description(soup, text):
    """Get job description snippet for scoring and proposal writing."""
    if soup:
        # Remove scripts, styles, and nav/footer noise
        for tag in soup(["script", "style", "footer", "header"]):
            tag.decompose()
        desc = soup.get_text("\n", strip=True)
    else:
        desc = text

    # Remove very short lines and unsubscribe boilerplate
    lines = [
        ln.strip()
        for ln in desc.splitlines()
        if len(ln.strip()) > 20
        and "unsubscribe" not in ln.lower()
        and "vollna" not in ln.lower()
    ]
    return "\n".join(lines[:30])[:3000]


def _extract_client_name(soup, text):
    """Try to find client name — often not in Vollna emails."""
    # Upwork alerts rarely include client name; return None to use "there"
    match = re.search(r"(?:client|posted by|hirer)[:\s]+([A-Z][a-z]+)", text, re.I)
    if match:
        return match.group(1)
    return None
