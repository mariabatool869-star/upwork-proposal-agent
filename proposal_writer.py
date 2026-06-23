"""
Proposal writer — generates professional proposals.
ALWAYS returns a proposal, never crashes.
"""
import logging

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

genai = None
HAS_GEMINI = False

try:
    import google.generativeai as genai
    from config import GEMINI_API_KEY

    if GEMINI_API_KEY and GEMINI_API_KEY.startswith("AIza"):
        genai.configure(api_key=GEMINI_API_KEY)
        HAS_GEMINI = True
        logger.info("✅ Gemini AI is ready")
    else:
        logger.info("ℹ️ Using fallback proposals (no Gemini key)")
except ImportError:
    logger.info("ℹ️ Using fallback proposals (Gemini not installed)")
except Exception as exc:
    logger.info("ℹ️ Using fallback proposals (%s)", exc)


def generate_proposal(job_data, profile):
    """
    Generate a proposal — ALWAYS returns a proposal.
    Never crashes, even if Gemini fails.
    """
    try:
        # Try Gemini if available
        if HAS_GEMINI:
            try:
                proposal = _generate_with_gemini(job_data, profile)
                if proposal and len(proposal) > 20:
                    logger.info(f"✅ Gemini proposal generated")
                    return proposal
            except Exception as e:
                logger.warning(f"Gemini failed: {e}")
        
        # Always fallback to professional proposal
        return _generate_fallback_proposal(job_data, profile)
        
    except Exception as e:
        logger.error(f"Proposal error: {e}")
        return _generate_emergency_proposal(job_data)


def _generate_with_gemini(job_data, profile):
    """Generate proposal using Gemini AI."""
    if genai is None:
        return None

    title = job_data.get('title', 'the position')
    description = job_data.get('description', '')
    budget = job_data.get('budget', 'negotiable')
    
    name = profile.get("name", "Maria")
    rate = profile.get("rate", "$50/hour")
    skills = ", ".join(profile.get("skills", ["Python", "AI", "Automation"])[:4])
    bio = profile.get("bio", "Senior developer with 13 years of experience")
    
    prompt = f"""
Write a short, professional proposal for this freelance job.

JOB:
- Title: {title}
- Description: {description[:300]}
- Budget: {budget}

MY PROFILE:
- Name: {name}
- Rate: {rate}
- Skills: {skills}
- Bio: {bio}

RULES:
- 3-4 sentences
- Professional tone
- Mention relevant skills
- End with call to action
- No markdown

Proposal:"""
    
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    response = model.generate_content(prompt)
    
    if response and response.text:
        return response.text.strip()
    return None


def _generate_fallback_proposal(job_data, profile):
    """Professional proposal without AI."""
    title = job_data.get('title', 'the position')
    name = profile.get("name", "Maria")
    rate = profile.get("rate", "$50/hour")
    skills = ", ".join(profile.get("skills", ["Python", "AI", "Automation"])[:3])
    
    return f"""Hi,

I'm {name}, a senior developer with expertise in {skills}. 

I can deliver excellent results for your {title} project. I have extensive experience building similar solutions and am available immediately.

Let's discuss your requirements. I'm available at {rate}.

Best regards,
{name}"""


def _generate_emergency_proposal(job_data):
    """Emergency proposal (always works)."""
    title = job_data.get('title', 'the position')
    return f"""Hi,

I'm interested in your {title} project. I have the skills and experience to deliver quality work.

Let's connect to discuss how I can help.

Best regards,
Maria"""


def write_proposal(job_data, profile):
    """Main function — always returns a proposal."""
    proposal = generate_proposal(job_data, profile)
    if not proposal or len(proposal) < 10:
        proposal = _generate_emergency_proposal(job_data)
    return proposal