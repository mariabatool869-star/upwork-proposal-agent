"""
Slack notifier — sends a message to your Slack channel when a proposal draft is ready.
Uses a free Slack Incoming Webhook (no paid Slack app required).
"""

import logging

import requests

import config

logger = logging.getLogger(__name__)


def notify_proposal_drafted(job, score, draft_link):
    """
    Send a Slack notification when a new proposal draft is created.

    Includes job title, budget, score, and link to the Gmail draft.
    """
    if not config.SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not set — skipping Slack notification.")
        return False

    title = job.get("title", "Unknown Job")
    budget = job.get("budget_display") or job.get("budget", "Not specified")
    url = job.get("url", "")

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "New Upwork Proposal Draft", "emoji": True},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Job:*\n{title}"},
                {"type": "mrkdwn", "text": f"*Budget:*\n{budget}"},
                {"type": "mrkdwn", "text": f"*Match Score:*\n{score}/10"},
            ],
        },
    ]

    if url:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Upwork Job:*\n<{url}|View Job>"},
            }
        )

    blocks.append(
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Gmail Draft:*\n<{draft_link}|Open Draft in Gmail>",
            },
        }
    )

    blocks.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Review the draft in Gmail, then copy it to Upwork when ready.",
                }
            ],
        }
    )

    payload = {
        "text": f"New proposal draft: {title} ({budget}) — Score {score}/10",
        "blocks": blocks,
    }

    try:
        response = requests.post(config.SLACK_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Slack notification sent.")
        return True
    except requests.RequestException as exc:
        logger.error(f"Slack notification failed: {exc}")
        return False


def notify_error(message):
    """Send an error alert to Slack (optional — for critical failures)."""
    if not config.SLACK_WEBHOOK_URL:
        return False

    payload = {
        "text": f":warning: Upwork Automation Error\n{message}",
    }

    try:
        requests.post(config.SLACK_WEBHOOK_URL, json=payload, timeout=10)
        return True
    except requests.RequestException:
        return False
