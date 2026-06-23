"""
Upwork Proposal Automation — main agent.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from config import (
    DATA_DIR,
    LOG_DIR,
    MY_NAME,
    PROCESSED_EMAILS_FILE,
    PROFILE,
    SCORE_THRESHOLD,
    STATUS_DRAFTED,
    STATUS_SKIPPED,
)
from gmail_reader import create_draft, fetch_vollna_emails, get_gmail_service
from job_parser import parse_vollna_email
from job_scorer import score_job
from proposal_writer import write_proposal
from sheets_logger import ensure_headers, get_sheets_service, log_job
from slack_notifier import notify_proposal_drafted

LOG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "agent.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def load_processed():
    if PROCESSED_EMAILS_FILE.exists():
        try:
            data = json.loads(PROCESSED_EMAILS_FILE.read_text())
            return set(data if isinstance(data, list) else data.get("ids", []))
        except (json.JSONDecodeError, OSError):
            pass
    return set()


def save_processed(processed):
    PROCESSED_EMAILS_FILE.write_text(json.dumps(list(processed), indent=2))


def main():
    logger.info("=" * 60)
    logger.info("Starting Upwork proposal automation run")
    logger.info("=" * 60)

    stats = {"new": 0, "drafted": 0, "skipped": 0, "errors": 0}

    try:
        gmail = get_gmail_service()
        logger.info("Connected to Gmail")

        sheet = get_sheets_service()
        if sheet:
            ensure_headers(sheet)
            logger.info("Connected to Google Sheets")
        else:
            logger.warning("Google Sheets not available — check GOOGLE_SHEETS_ID in .env")

        emails = fetch_vollna_emails(gmail, max_results=20)
        processed = load_processed()

        profile = {
            "name": MY_NAME,
            "rate": PROFILE.get("rate", "$50/hour"),
            "skills": PROFILE.get("skills", []),
            "bio": PROFILE.get("bio", ""),
        }

        for email_data in emails:
            email_id = email_data.get("id", "")
            subject = email_data.get("subject", "")

            if email_id in processed:
                logger.debug(f"Already processed: {subject}")
                continue

            logger.info(f"Processing email: {subject}")
            jobs = parse_vollna_email(email_data)

            if not jobs:
                logger.warning(f"No jobs extracted from: {subject}")
                continue

            email_had_error = False
            for job in jobs:
                stats["new"] += 1
                score, matched_skills, skip_reason = score_job(job)

                row = {
                    "timestamp": datetime.now().isoformat(),
                    "title": job.get("title"),
                    "description": job.get("description"),
                    "budget": job.get("budget_display") or job.get("budget"),
                    "budget_type": job.get("budget_type"),
                    "url": job.get("url"),
                    "score": score,
                    "matched_skills": matched_skills,
                    "proposal": "",
                }

                if skip_reason or score < SCORE_THRESHOLD:
                    row["status"] = STATUS_SKIPPED
                    logger.info(
                        f"Skipping: {job['title']} — "
                        f"{skip_reason or f'Score {score} below threshold {SCORE_THRESHOLD}'}"
                    )
                    stats["skipped"] += 1
                    if sheet:
                        log_job(sheet, row)
                    continue

                try:
                    proposal = write_proposal(job, profile)
                    row["proposal"] = proposal
                    row["status"] = STATUS_DRAFTED

                    draft_subject = f"Upwork Proposal: {job['title'][:100]}"
                    draft_id, draft_link = create_draft(gmail, draft_subject, proposal)

                    if draft_id:
                        stats["drafted"] += 1
                        notify_proposal_drafted(
                            {
                                "title": job["title"],
                                "budget": row["budget"],
                                "url": job.get("url", ""),
                            },
                            score,
                            draft_link,
                        )
                        logger.info(f"Draft created: {job['title']}")
                    else:
                        row["status"] = "Error"
                        stats["errors"] += 1
                        email_had_error = True

                    if sheet:
                        log_job(sheet, row)

                except Exception as exc:
                    logger.error(f"Error on {job.get('title')}: {exc}")
                    stats["errors"] += 1
                    email_had_error = True

            if not email_had_error:
                processed.add(email_id)

        save_processed(processed)
        logger.info(
            f"Run complete — Jobs: {stats['new']}, Drafted: {stats['drafted']}, "
            f"Skipped: {stats['skipped']}, Errors: {stats['errors']}"
        )
        sheet_id = os.getenv("GOOGLE_SHEETS_ID", "")
        if sheet_id:
            logger.info(
                "Rows saved to Google Sheets — refresh your Streamlit dashboard to see updates."
            )

    except Exception as exc:
        logger.error(f"Run failed: {exc}")


if __name__ == "__main__":
    main()
