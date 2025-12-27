from typing import Optional

from ai.errors import AITransientError, AIPermanentError
from ai.router import get_provider

from ..models import CoverLetter


class CoverLetterGenerator:
    """
    Service for generating personalized cover letters using AI.
    """

    def __init__(self):
        self.ai_provider = get_provider()

    def generate_cover_letter(
        self,
        user_profile,
        opportunity,
        existing_letter: Optional[CoverLetter] = None
    ) -> str:
        """
        Generate a personalized cover letter for a job application.

        Args:
            user_profile: UserProfile instance with user data
            opportunity: Opportunity instance with job details
            existing_letter: If regenerating, reference the previous version

        Returns:
            Generated cover letter text
        """
        prompt = self._build_generation_prompt(user_profile, opportunity, existing_letter)

        try:
            result = self.ai_provider.generate_text(
                prompt=prompt,
                model=None,  # Use default model
                temperature=0.7,  # Slightly creative for natural writing
                system="You are a professional career counselor helping job seekers write compelling cover letters."
            )

            return self._clean_generated_content(result.text)

        except AITransientError as e:
            raise e  # Let caller handle retries
        except Exception as e:
            raise AIPermanentError(f"Cover letter generation failed: {str(e)}")

    def _build_generation_prompt(self, user_profile, opportunity, existing_letter=None) -> str:
        """Build the AI prompt for cover letter generation."""

        # User profile data
        user_name = user_profile.full_name or "the applicant"
        academic_info = self._format_academic_info(user_profile.academic_info)
        skills = ", ".join(user_profile.skills) if user_profile.skills else "various technical skills"
        experience = self._format_experience(user_profile.experience) if hasattr(user_profile, 'experience') and user_profile.experience else "relevant professional experience"

        # Job details
        job_title = opportunity.title
        organization = opportunity.organization or "the organization"
        job_description = opportunity.description_en or "the position requirements"

        # Build prompt
        prompt = f"""Write a professional, compelling cover letter for {user_name} applying for the {job_title} position at {organization}.

CANDIDATE BACKGROUND:
- Academic: {academic_info}
- Skills: {skills}
- Experience: {experience}

JOB DETAILS:
Title: {job_title}
Organization: {organization}
Description: {job_description}

REQUIREMENTS:
- Write a formal, professional cover letter (250-400 words)
- Highlight relevant skills and experience that match the job
- Show enthusiasm for the role and company
- Use proper business letter format with greeting and closing
- Be specific and personalized, not generic
- Demonstrate knowledge of the role and company
- Keep it concise but impactful

COVER LETTER:"""

        if existing_letter:
            prompt += f"\n\nREFERENCE PREVIOUS VERSION (improve upon this):\n{existing_letter.generated_content[:500]}..."

        return prompt

    def _format_academic_info(self, academic_info: dict) -> str:
        """Format academic information for the prompt."""
        if not academic_info:
            return "relevant educational background"

        parts = []
        degrees = academic_info.get("degrees", [])
        for degree in degrees[:2]:  # Limit to most recent 2
            degree_name = degree.get("degree", "")
            institution = degree.get("institution", "")
            year = degree.get("year", "")
            if degree_name and institution:
                parts.append(f"{degree_name} from {institution} ({year})" if year else f"{degree_name} from {institution}")

        return "; ".join(parts) if parts else "relevant educational background"

    def _format_experience(self, experience_list: list) -> str:
        """Format experience information for the prompt."""
        if not experience_list:
            return "professional experience in the field"

        # Get most recent 2-3 experiences
        recent_exp = experience_list[:3]
        formatted = []
        for exp in recent_exp:
            title = exp.get("title", "")
            company = exp.get("company", "")
            if title and company:
                formatted.append(f"{title} at {company}")

        return "; ".join(formatted) if formatted else "professional experience in the field"

    def _clean_generated_content(self, content: str) -> str:
        """Clean and format the generated cover letter."""
        # Remove any AI artifacts, ensure proper formatting
        content = content.strip()

        # Ensure it starts with a proper greeting
        if not content.startswith("Dear"):
            content = "Dear Hiring Manager,\n\n" + content

        # Ensure it ends properly
        if not content.endswith(("Sincerely,", "Best regards,", "Regards,")):
            content += "\n\nSincerely,\n[The Applicant's Name]"

        return content

    def should_regenerate(self, letter: CoverLetter, user_profile) -> bool:
        """
        Check if a cover letter should be regenerated based on profile changes.
        """
        # Simple check: if profile was updated after letter was created
        return user_profile.updated_at > letter.created_at
