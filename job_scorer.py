"""
Job scorer — rates jobs 1-10 against your profile skills and budget preferences.
"""

import logging
import re

import config

logger = logging.getLogger(__name__)


def score_job(job):
    """
    Score a job from 1-10 based on skill match, budget, and keyword relevance.

    Returns:
        score (int 1-10),
        matched_skills (list of strings),
        skip_reason (str or None if job passes filters)
    """
    title = job.get("title", "")
    description = job.get("description", "")
    combined = f"{title} {description}".lower()

    matched_skills = []
    skill_score = 0.0

    # --- Primary skills (worth 2 points each, max ~10) ---
    for skill in config.PROFILE["primary_skills"]:
        pattern = re.compile(re.escape(skill.lower()))
        if pattern.search(combined):
            matched_skills.append(skill)
            skill_score += 2.0

    # --- Secondary skills from full profile (worth 1 point each) ---
    for skill in config.PROFILE["skills"]:
        skill_lower = skill.lower()
        if skill_lower in combined and skill not in matched_skills:
            matched_skills.append(skill)
            skill_score += 1.0

    # Cap skill contribution at 10
    skill_score = min(skill_score, 10.0)

    # --- Budget filter ---
    skip_reason = _check_budget(job)
    if skip_reason:
        logger.info(f"Budget filter: {skip_reason}")
        return max(1, int(skill_score * 0.5)), matched_skills, skip_reason

    # --- Negative keywords (reduce score) ---
    negative_keywords = [
        "wordpress only",
        "shopify theme",
        "logo design",
        "video editing",
        "data entry only",
        "virtual assistant only",
        "translation only",
        "no agencies",
    ]
    penalty = sum(1.5 for kw in negative_keywords if kw in combined)

    # --- Positive signals ---
    bonus = 0.0
    positive_signals = [
        "automation",
        "ai",
        "api",
        "python",
        "n8n",
        "integration",
        "saas",
        "webhook",
        "chatbot",
        "long-term",
        "ongoing",
    ]
    for signal in positive_signals:
        if signal in combined:
            bonus += 0.3

    raw_score = skill_score + bonus - penalty
    final_score = max(1, min(10, round(raw_score)))

    logger.info(
        f"Score: {final_score}/10 | Matched: {', '.join(matched_skills[:5]) or 'none'}"
    )
    return final_score, matched_skills, None


def _check_budget(job):
    """Return skip reason if budget is too low, else None."""
    budget_type = job.get("budget_type", "unknown")
    budget_value = job.get("budget_value")

    if budget_value is None:
        return None  # Unknown budget — don't skip, let scoring decide

    if budget_type == "hourly" and budget_value < config.MIN_BUDGET_HOURLY:
        return (
            f"Hourly rate ${budget_value}/hr below minimum "
            f"${config.MIN_BUDGET_HOURLY}/hr"
        )

    if budget_type == "fixed" and budget_value < config.MIN_BUDGET_FIXED:
        return (
            f"Fixed budget ${budget_value} below minimum "
            f"${config.MIN_BUDGET_FIXED}"
        )

    return None


def should_process(score, skip_reason):
    """Decide if we should write a proposal for this job."""
    if skip_reason:
        return False
    return score >= config.SCORE_THRESHOLD
