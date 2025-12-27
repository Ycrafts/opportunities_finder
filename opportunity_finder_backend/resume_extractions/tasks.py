from celery import shared_task

from .models import CVExtractionSession
from .services.cv_extractor import CVExtractionService


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def process_cv_extraction(self, session_id: int) -> dict:
    """
    Async task to process CV extraction for a session.
    """
    try:
        session = CVExtractionSession.objects.get(id=session_id)
        service = CVExtractionService()

        # Process the extraction
        service.process_cv_extraction(session)

        return {
            "session_id": session_id,
            "status": "completed",
            "confidence_score": session.confidence_score
        }

    except Exception as e:
        # Mark session as failed
        CVExtractionSession.objects.filter(id=session_id).update(
            status=CVExtractionSession.Status.FAILED,
            error_message=str(e)
        )
        raise  # Re-raise for Celery retry logic
