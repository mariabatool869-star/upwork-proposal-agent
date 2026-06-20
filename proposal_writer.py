"""
Proposal writer — uses Google Gemini (free tier) to generate Upwork proposals.
Follows the Nick Saraev formula: Hook → Proof → Offer → Soft CTA (55-75 words).
"""

import logging
import re
import time

import google.generativeai as genai

import config

logger = logging.getLogger(__name__)


def _build_prompt(job, matched_skills):
    """Build the Gemini prompt for a job proposal."""
    top_skill = matched_skills[0] if matched_skills else "AI and automation"
    client_name = job.get("client_name", "there")
    title = job.get("title", "this project")
    description_snippet = (job.get("description") or "")[:800]

    return f"""Write an Upwork job proposal for this freelancer.

FREELANCER PROFILE:
- Title: {config.PROFILE['title']}
- Rate: $30/hour (always mention this)
- Experience: 10+ years
- Bio: {config.PROFILE['bio']}
- Key achievements: {'; '.join(config.PROFILE['experience_highlights'])}
- Skills: {', '.join(config.PROFILE['skills'][:12])}

JOB DETAILS:
- Title: {title}
- Budget: {job.get('budget', 'Not specified')}
- Description: {description_snippet}
- Most relevant skill for this job: {top_skill}

PROPOSAL RULES (Nick Saraev formula — follow exactly):
1. Start with "Hi {client_name}," (use "Hi there," if no name)
2. HOOK: One sentence showing relevant senior experience (mention 10+ years and $30/hour)
3. PROOF: One specific proof point from the achievements list (pick the most relevant)
4. OFFER: One sentence on what you'll deliver for THIS job specifically
5. CTA: Soft call to action — ask when they're free to discuss
6. End with "Best,\\n{config.MY_NAME}"
7. Total length: 55-75 words (strict — count carefully)
8. Tone: Confident, professional, concise — no fluff or buzzwords
9. Do NOT use bullet points
10. Do NOT mention Upwork platform mechanics (connects, badges, etc.)

Write ONLY the proposal text, nothing else."""


def _clean_proposal(text):
    """Remove markdown wrappers and extra whitespace from Gemini output."""
    proposal = text.strip()
    proposal = re.sub(r"^```.*?\n", "", proposal)
    proposal = re.sub(r"\n```$", "", proposal)
    return proposal.strip()


def _is_rate_limit_error(exc):
    """Check if an exception is a Gemini quota / rate-limit error."""
    msg = str(exc).lower()
    return "429" in msg or "quota" in msg or "rate" in msg


def generate_proposal(job, matched_skills):
    """
    Generate a 55-75 word proposal for the given job.

    Tries multiple free-tier Gemini models with automatic retry on rate limits.
    """
    if not config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")

    if not config.GEMINI_API_KEY.startswith("AIza"):
        logger.warning(
            "Your GEMINI_API_KEY may be the wrong type. "
            "Get a free key from https://aistudio.google.com/apikey — it should start with 'AIza'."
        )

    genai.configure(api_key=config.GEMINI_API_KEY)
    prompt = _build_prompt(job, matched_skills)
    models = [m.strip() for m in config.GEMINI_MODELS if m.strip()]
    last_error = None

    for model_name in models:
        for attempt in range(3):
            try:
                logger.info(f"Generating proposal with Gemini ({model_name})...")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                proposal = _clean_proposal(response.text)

                word_count = len(proposal.split())
                logger.info(f"Proposal generated ({word_count} words) using {model_name}")

                if word_count < 40 or word_count > 100:
                    logger.warning(
                        f"Proposal word count ({word_count}) outside target 55-75"
                    )

                return proposal

            except Exception as exc:
                last_error = exc
                if _is_rate_limit_error(exc):
                    wait = 30 * (attempt + 1)
                    logger.warning(
                        f"Gemini rate limit on {model_name} — waiting {wait}s before retry..."
                    )
                    time.sleep(wait)
                    continue

                logger.warning(f"Gemini error on {model_name}: {exc}")
                break  # Try next model

    raise RuntimeError(
        f"All Gemini models failed. Last error: {last_error}. "
        "Check your API key at https://aistudio.google.com/apikey "
        "(free key should start with AIza)."
    )
