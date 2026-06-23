"""
Proposal writer using Google Gemini API (AQ. key format).
"""
import logging
import os
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')


def generate_proposal(job_data, profile):
    """
    Generate a proposal using Gemini API with AQ. format key.
    """
    try:
        if not GEMINI_API_KEY:
            logger.warning("No Gemini API key found")
            return _generate_fallback_proposal(job_data, profile)

        # Extract job details
        title = job_data.get('title', 'the position')
        description = job_data.get('description', '')
        budget = job_data.get('budget', 'negotiable')

        name = profile.get("name", "Maria")
        rate = profile.get("rate", "$50/hour")
        skills = ", ".join(profile.get("skills", ["Python", "AI", "Automation"])[:4])

        prompt = f"""
You are a professional freelance proposal writer. Write a short, compelling proposal for this job.

JOB:
- Title: {title}
- Description: {description}
- Budget: {budget}

MY PROFILE:
- Name: {name}
- Rate: {rate}
- Skills: {skills}

3-4 sentences only. Professional tone. End with call to action.
"""

        # Use the native Gemini endpoint with x-goog-api-key header
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent"

        headers = {
            "x-goog-api-key": GEMINI_API_KEY,  # ✅ Use header, not query param
            "Content-Type": "application/json"
        }

        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            proposal = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            if proposal:
                logger.info("✅ Gemini proposal generated")
                return proposal.strip()
        else:
            logger.error(f"Gemini API error: {response.status_code} - {response.text}")

    except Exception as e:
        logger.error(f"Gemini error: {e}")

    return _generate_fallback_proposal(job_data, profile)


def _generate_fallback_proposal(job_data, profile):
    """Fallback proposal."""
    title = job_data.get('title', 'the position')
    name = profile.get("name", "Maria")
    rate = profile.get("rate", "$50/hour")
    skills = ", ".join(profile.get("skills", ["Python", "AI", "Automation"])[:3])

    return f"""Hi,

I'm {name}, a senior developer with expertise in {skills}.

I can deliver excellent results for your {title} project. I'm available at {rate}.

Let's discuss your requirements.

Best regards,
{name}"""


def write_proposal(job_data, profile):
    """Main function."""
    proposal = generate_proposal(job_data, profile)
    if not proposal or len(proposal) < 10:
        proposal = _generate_fallback_proposal(job_data, profile)
    return proposal