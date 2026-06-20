"""
Upwork Proposal Automation — main orchestrator.

Runs every 30 minutes (configurable), checks Gmail for Vollna alerts,
scores jobs, writes proposals with Gemini, saves Gmail drafts,
logs to Google Sheets, and notifies Slack.

Usage:
    python main.py                  # Run once (process new emails)
    python main.py --loop           # Run continuously every 30 minutes
    python main.py --url JOB_URL    # Manual test with a job URL
    python main.py --url JOB_URL --title "Job Title" --budget "$50/hr"
"""

import argparse
import json
import logging
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

import config
from gmail_reader import create_draft, fetch_vollna_emails, get_gmail_service
from job_parser import parse_manual_url, parse_vollna_email
from job_scorer import score_job, should_process
from proposal_writer import generate_proposal
from sheets_logger import ensure_headers, get_sheets_service, log_job
from slack_notifier import notify_error, notify_proposal_drafted

# Load .env file from project folder
load_dotenv(config.BASE_DIR / ".env")

# Re-read config values that come from env (after dotenv load)
import importlib
importlib.reload(config)


def setup_logging():
    """Create logs folder and configure file + console logging."""
    config.LOG_DIR.mkdir(exist_ok=True)
    config.DATA_DIR.mkdir(exist_ok=True)

    log_file = config.LOG_DIR / f"run_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("main")


def load_processed_ids():
    """Load set of already-processed Gmail message IDs."""
    if config.PROCESSED_EMAILS_FILE.exists():
        try:
            data = json.loads(config.PROCESSED_EMAILS_FILE.read_text())
            return set(data.get("ids", []))
        except (json.JSONDecodeError, OSError):
            return set()
    return set()


def save_processed_id(email_id, processed_ids):
    """Mark an email as processed so we don't handle it again."""
    processed_ids.add(email_id)
    config.PROCESSED_EMAILS_FILE.write_text(
        json.dumps({"ids": list(processed_ids)}, indent=2)
    )


def process_job(job, gmail_service, sheets_service, logger, force=False):
    """
    Score one job and optionally write a proposal draft.

    force=True skips the score threshold (for manual testing).
    """
    score, matched_skills, skip_reason = score_job(job)

    if not force and not should_process(score, skip_reason):
        status = "skipped"
        reason = skip_reason or f"Score {score} below threshold {config.SCORE_THRESHOLD}"
        logger.info(f"Skipping: {job['title']} — {reason}")
        log_job(sheets_service, job, score, status, proposal="", matched_skills=matched_skills)
        return status

    # --- Generate proposal ---
    try:
        proposal = generate_proposal(job, matched_skills)
    except Exception as exc:
        logger.error(f"Proposal generation failed: {exc}")
        log_job(sheets_service, job, score, "error", matched_skills=matched_skills)
        notify_error(f"Proposal failed for '{job['title']}': {exc}")
        return "error"

    # --- Save Gmail draft ---
    draft_subject = f"Upwork Proposal: {job['title'][:100]}"
    try:
        draft_id, draft_link = create_draft(gmail_service, draft_subject, proposal)
    except Exception as exc:
        logger.error(f"Gmail draft creation failed: {exc}")
        log_job(sheets_service, job, score, "error", proposal=proposal, matched_skills=matched_skills)
        notify_error(f"Draft failed for '{job['title']}': {exc}")
        return "error"

    # --- Log and notify ---
    log_job(sheets_service, job, score, "drafted", proposal=proposal, matched_skills=matched_skills)
    notify_proposal_drafted(job, score, draft_link)

    logger.info(f"Done: {job['title']} — draft saved, Slack notified.")
    return "drafted"


def run_once(logger):
    """Check Gmail once and process all new Vollna emails."""
    logger.info("=" * 60)
    logger.info("Starting Upwork proposal automation run")
    logger.info("=" * 60)

    processed_ids = load_processed_ids()
    stats = {"drafted": 0, "skipped": 0, "error": 0, "new": 0}

    try:
        gmail_service = get_gmail_service()
        sheets_service = get_sheets_service()
        ensure_headers(sheets_service)
    except Exception as exc:
        logger.error(f"Failed to connect to Google APIs: {exc}")
        notify_error(f"Google API connection failed: {exc}")
        return stats

    try:
        emails = fetch_vollna_emails(gmail_service)
    except Exception as exc:
        logger.error(f"Failed to fetch emails: {exc}")
        notify_error(f"Gmail fetch failed: {exc}")
        return stats

    for email_data in emails:
        email_id = email_data.get("id")

        if email_id in processed_ids:
            logger.debug(f"Already processed: {email_id}")
            continue

        stats["new"] += 1
        logger.info(f"Processing email: {email_data.get('subject', '')}")

        try:
            jobs = parse_vollna_email(email_data)
            email_had_error = False
            for job in jobs:
                status = process_job(job, gmail_service, sheets_service, logger)
                stats[status] = stats.get(status, 0) + 1
                if status == "error":
                    email_had_error = True
        except Exception as exc:
            logger.error(f"Error processing email {email_id}: {exc}")
            logger.debug(traceback.format_exc())
            stats["error"] += 1
            notify_error(f"Email processing error: {exc}")
            email_had_error = True
        finally:
            # Only mark as processed if no errors — failed jobs will retry next run
            if email_id and not email_had_error:
                save_processed_id(email_id, processed_ids)
            elif email_id and email_had_error:
                logger.info(
                    f"Email {email_id} had errors — will retry on next run"
                )

    logger.info(
        f"Run complete — New: {stats['new']}, "
        f"Drafted: {stats['drafted']}, Skipped: {stats['skipped']}, "
        f"Errors: {stats['error']}"
    )
    return stats


def run_manual_test(url, title, budget, description, logger):
    """Process a single job URL manually (for testing without an email)."""
    logger.info(f"Manual test mode — URL: {url}")

    job = parse_manual_url(url, title=title, budget=budget, description=description)

    try:
        gmail_service = get_gmail_service()
        sheets_service = get_sheets_service()
        ensure_headers(sheets_service)
    except Exception as exc:
        logger.error(f"Google API connection failed: {exc}")
        return

    status = process_job(job, gmail_service, sheets_service, logger, force=True)
    logger.info(f"Manual test result: {status}")


def run_loop(logger):
    """Run continuously, checking Gmail every POLL_INTERVAL_MINUTES."""
    interval_seconds = config.POLL_INTERVAL_MINUTES * 60
    logger.info(
        f"Starting background loop — checking every {config.POLL_INTERVAL_MINUTES} minutes"
    )
    logger.info("Press Ctrl+C to stop.")

    while True:
        try:
            run_once(logger)
        except Exception as exc:
            logger.error(f"Unexpected error in loop: {exc}")
            logger.debug(traceback.format_exc())
            notify_error(f"Loop error: {exc}")

        logger.info(f"Sleeping {config.POLL_INTERVAL_MINUTES} minutes until next check...")
        time.sleep(interval_seconds)


def main():
    parser = argparse.ArgumentParser(
        description="Upwork Proposal Automation — Vollna alerts to Gmail drafts"
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuously every 30 minutes (background service mode)",
    )
    parser.add_argument(
        "--url",
        type=str,
        help="Manual test: process a single Upwork job URL",
    )
    parser.add_argument("--title", type=str, help="Job title (with --url)")
    parser.add_argument("--budget", type=str, help="Job budget (with --url)")
    parser.add_argument(
        "--reprocess",
        action="store_true",
        help="Clear processed email history and re-check all Vollna emails",
    )

    parser.add_argument(
        "--description",
        type=str,
        help="Job description text (with --url, for better scoring)",
    )

    args = parser.parse_args()
    logger = setup_logging()

    if args.reprocess and config.PROCESSED_EMAILS_FILE.exists():
        config.PROCESSED_EMAILS_FILE.unlink()
        logger.info("Cleared processed email history — will re-check all emails.")

    # Quick config validation
    missing = []
    if not config.GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if not config.GOOGLE_SHEETS_ID:
        missing.append("GOOGLE_SHEETS_ID")
    if missing:
        logger.warning(f"Missing env vars: {', '.join(missing)} — some features will not work.")

    if args.url:
        run_manual_test(args.url, args.title, args.budget, args.description, logger)
    elif args.loop:
        run_loop(logger)
    else:
        run_once(logger)


if __name__ == "__main__":
    main()
