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
                system="You are a professional career counselor helping job seekers write compelling cover letters.",
                context="cover_letter",
                user=user_profile.user,
            )

            return self._clean_generated_content(result.text)

        except AITransientError as e:
            raise e  # Let caller handle retries
        except Exception as e:
            raise AIPermanentError(f"Cover letter generation failed: {str(e)}")

    def _build_generation_prompt(self, user_profile, opportunity, existing_letter=None) -> str:
        """Build the AI prompt for cover letter generation."""

        # User contact information
        user_name = user_profile.full_name or user_profile.user.get_full_name() or user_profile.user.username
        user_email = user_profile.user.email or ""
        user_phone = self._get_user_phone(user_profile) or "[Phone number not provided]"
        user_address = self._get_user_address(user_profile) or "[Address not provided]"

        # User profile data
        academic_info = self._format_academic_info(user_profile.academic_info)
        skills = ", ".join(user_profile.skills) if user_profile.skills else "various technical skills"
        experience = self._format_experience(user_profile.experience) if hasattr(user_profile, 'experience') and user_profile.experience else "relevant professional experience"

        # Job details
        job_title = opportunity.title
        organization = opportunity.organization or "the organization"
        job_description = opportunity.description_en or "the position requirements"

        # Current date
        from datetime import datetime
        current_date = datetime.now().strftime("%B %d, %Y")

        # Build prompt with specific contact information
        prompt = f"""Write a professional, compelling cover letter for a job application.

CANDIDATE CONTACT INFORMATION (USE THESE EXACT VALUES):
- Full Name: {user_name}
- Email Address: {user_email}
- Phone Number: {user_phone}
- Address: {user_address}

JOB DETAILS (USE THESE EXACT VALUES):
- Position Title: {job_title}
- Organization Name: {organization}
- Job Description: {job_description[:500]}...

CANDIDATE BACKGROUND:
- Academic: {academic_info}
- Skills: {skills}
- Experience: {experience}

CURRENT DATE: {current_date}

CRITICAL INSTRUCTIONS:
- You MUST use the EXACT contact information, names, and organization details provided above
- DO NOT invent or use placeholder text like [Your Name], [Organization Name], [Your Address], etc.
- For any missing information, either omit it gracefully or use a professional fallback
- Write a complete, properly formatted business letter
- Include the candidate's contact information at the top
- Use the current date provided
- Create an appropriate subject line
- Use "Dear Hiring Manager," or similar professional greeting
- Write 3-4 paragraphs highlighting relevant qualifications
- End with a professional closing using the candidate's actual name

FORMAT REQUIREMENTS:
1. Candidate's full contact information at top
2. Current date
3. Organization name/address (professional format)
4. Subject line with position title
5. Professional salutation
6. Body paragraphs
7. Professional sign-off

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

    def _get_user_phone(self, user_profile) -> str:
        """Extract phone number from user profile if available."""
        # Check if phone is stored in the profile JSON fields
        if hasattr(user_profile, 'contact_info') and user_profile.contact_info:
            return user_profile.contact_info.get('phone', '')

        # Check academic_info for contact details (sometimes stored there)
        if user_profile.academic_info and isinstance(user_profile.academic_info, dict):
            contact = user_profile.academic_info.get('contact', {})
            if isinstance(contact, dict):
                return contact.get('phone', '')

        return ""

    def _get_user_address(self, user_profile) -> str:
        """Extract address from user profile if available."""
        # Check if address is stored in the profile JSON fields
        if hasattr(user_profile, 'contact_info') and user_profile.contact_info:
            address = user_profile.contact_info.get('address', '')
            if address:
                return address

        # Check academic_info for contact details
        if user_profile.academic_info and isinstance(user_profile.academic_info, dict):
            contact = user_profile.academic_info.get('contact', {})
            if isinstance(contact, dict):
                address = contact.get('address', '')
                if address:
                    return address

        return ""

    def _clean_generated_content(self, content: str) -> str:
        """Clean and format the generated cover letter."""
        # Remove any AI artifacts, ensure proper formatting
        content = content.strip()

        # Remove any remaining placeholder-like text
        content = content.replace('[Embassy Address - if known, otherwise omit or use a general address', '')
        content = content.replace('[Use a professional placeholder or omit if not available]', '')
        content = content.replace('[Use a professional format or omit if not available]', '')
        content = content.replace('[truncated for prompt length]', '')
        content = content.replace('[Phone number not provided]', '')
        content = content.replace('[Address not provided]', '')
        content = content.replace('[Organization Address Placeholder, e.g., 1-2-3 Kasumigaseki, Chiyoda-ku, Tokyo, Japan]', '')

        # Clean up any double brackets or awkward formatting
        content = content.replace('[[', '[').replace(']]', ']')
        content = content.replace('[ ', '').replace(' ]', '')

        # Ensure proper spacing after cleaning
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line:  # Only keep non-empty lines
                cleaned_lines.append(line)

        content = '\n\n'.join(cleaned_lines)

        # The AI should now generate proper content with actual names and contact info

        return content

    def should_regenerate(self, letter: CoverLetter, user_profile) -> bool:
        """
        Check if a cover letter should be regenerated based on profile changes.
        """
        # Simple check: if profile was updated after letter was created
        return user_profile.updated_at > letter.created_at
