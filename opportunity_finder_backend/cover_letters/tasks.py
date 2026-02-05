from celery import shared_task

from ai.errors import sanitize_ai_error_message

from .models import CoverLetter
from .services.cover_letter_generator import CoverLetterGenerator


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3}, priority=9)
def generate_cover_letter_task(self, user_id: int, opportunity_id: int, version: int = 1, existing_letter_id: int | None = None) -> dict:
    """
    Async task to generate a cover letter using AI.
    """
    try:
        # Get user profile
        from profiles.models import UserProfile
        user_profile = UserProfile.objects.get(user_id=user_id)

        # Get opportunity
        from opportunities.models import Opportunity
        opportunity = Opportunity.objects.get(id=opportunity_id)

        # Get existing letter if regenerating
        existing_letter = None
        if existing_letter_id:
            existing_letter = CoverLetter.objects.get(id=existing_letter_id)

        # Generate cover letter
        generator = CoverLetterGenerator()
        generated_content = generator.generate_cover_letter(
            user_profile=user_profile,
            opportunity=opportunity,
            existing_letter=existing_letter
        )

        # Update the existing GENERATING cover letter record
        cover_letter = CoverLetter.objects.get(
            user_id=user_id,
            opportunity_id=opportunity_id,
            version=version
        )

        # Update with generated content
        cover_letter.generated_content = generated_content
        cover_letter.status = CoverLetter.Status.GENERATED
        cover_letter.save()

        return {
            "success": True,
            "cover_letter_id": cover_letter.id,
            "status": "completed"
        }

    except Exception as e:
        # If we have partial data, mark as failed
        try:
            CoverLetter.objects.filter(
                user_id=user_id,
                opportunity_id=opportunity_id,
                version=version
            ).update(
                status=CoverLetter.Status.FAILED,
                error_message=sanitize_ai_error_message(e)
            )
        except:
            pass  # Ignore if record doesn't exist yet

        raise  # Re-raise for Celery retry logic
