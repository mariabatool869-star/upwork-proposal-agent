"""
Job scorer — rates jobs 1-10 against your profile skills and budget.
"""
import logging
import re

from config import MIN_BUDGET_FIXED, MIN_BUDGET_HOURLY, PROFILE, SCORE_THRESHOLD

logger = logging.getLogger(__name__)


def score_job(job):
    """
    Score job 1-10. Returns (score, matched_skills, skip_reason).
    skip_reason is set only for budget filters — not low score (main handles that).
    """
    title = job.get("title", "")
    description = job.get("description", "")
    combined = f"{title} {description}".lower()

    if not combined.strip() or len(combined.strip()) < 10:
        return 1, [], None

    matched = []
    skill_score = 0.0

    for skill in PROFILE.get("primary_skills", []):
        if re.search(re.escape(skill.lower()), combined):
            matched.append(skill)
            skill_score += 2.0

    for skill in PROFILE.get("skills", []):
        s = skill.lower()
        if s in combined and skill not in matched:
            matched.append(skill)
            skill_score += 1.0

    skill_score = min(skill_score, 10.0)

    bonus = sum(
        0.3 for kw in (
            "automation", "ai", "api", "python", "n8n", "integration",
            "saas", "chatbot", "workflow", "agent",
        )
        if kw in combined
    )

    penalty = sum(
        1.5 for kw in (
            "wordpress only", "logo design", "data entry only", "video editing",
        )
        if kw in combined
    )

    final_score = max(1, min(10, round(skill_score + bonus - penalty)))

    skip_reason = _check_budget(job)
    if skip_reason:
        logger.info(f"Budget filter: {skip_reason}")
        return max(1, int(final_score * 0.5)), matched, skip_reason

    logger.info(
        f"Score: {final_score}/10 | Matched: {', '.join(matched[:5]) or 'none'}"
    )
    return final_score, matched, None


def _check_budget(job):
    budget = job.get("budget")
    if budget is None:
        return None
    btype = job.get("budget_type")
    if btype == "hourly" and budget < MIN_BUDGET_HOURLY:
        return f"Hourly ${budget}/hr below minimum ${MIN_BUDGET_HOURLY}/hr"
    if btype == "fixed" and budget < MIN_BUDGET_FIXED:
        return f"Fixed ${budget} below minimum ${MIN_BUDGET_FIXED}"
    return None


def should_process(score, skip_reason):
    if skip_reason:
        return False
    return score >= SCORE_THRESHOLD
