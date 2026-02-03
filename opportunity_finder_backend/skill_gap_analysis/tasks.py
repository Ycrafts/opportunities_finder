from celery import shared_task

from django.utils import timezone

from opportunities.models import Opportunity
from profiles.models import UserProfile

from matching.models import Match

from ai.errors import sanitize_ai_error_message
from .models import SkillGapAnalysis
from .services.skill_gap_analyzer import SkillGapAnalyzer


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    priority=9,
    queue="priority",
)
def analyze_skill_gaps_task(self=None, analysis_id: int = 0) -> dict:
    """
    Asynchronous task to perform skill gap analysis.

    Args:
        analysis_id: ID of the SkillGapAnalysis record to process

    Returns:
        Dict with processing results
    """
    try:
        # Get the analysis record
        analysis = SkillGapAnalysis.objects.select_related(
            "user", "opportunity", "user__profile"
        ).get(id=analysis_id)

        # Check if already completed
        if analysis.status == SkillGapAnalysis.Status.COMPLETED:
            return {"status": "already_completed", "analysis_id": analysis_id}

        # Update status to generating
        analysis.status = SkillGapAnalysis.Status.GENERATING
        analysis.save(update_fields=["status"])

        # Get user profile
        try:
            user_profile = UserProfile.objects.get(user=analysis.user)
        except UserProfile.DoesNotExist:
            analysis.status = SkillGapAnalysis.Status.FAILED
            analysis.error_message = "User profile not found"
            analysis.save()
            return {"status": "failed", "error": "User profile not found"}

        # Get opportunity
        opportunity = analysis.opportunity

        # Guardrail: if match score is too low, return a lightweight summary
        low_fit_threshold = 3.5
        match_score = Match.objects.filter(
            user=analysis.user,
            opportunity=analysis.opportunity
        ).values_list("match_score", flat=True).first()

        if match_score is None:
            analysis.status = SkillGapAnalysis.Status.COMPLETED
            analysis.missing_skills = []
            analysis.skill_gaps = {}
            analysis.recommended_actions = []
            analysis.alternative_suggestions = {
                "summary": (
                    "This opportunity hasn't been matched to your profile yet. "
                    "We can only provide a high-level summary until a match is established."
                ),
                "reason": "no_match",
            }
            analysis.confidence_score = 0.2
            analysis.estimated_time_months = None
            analysis.completed_at = timezone.now()
            analysis.save()
            return {
                "status": "completed_no_match",
                "analysis_id": analysis_id,
            }

        if match_score < low_fit_threshold:
            analysis.status = SkillGapAnalysis.Status.COMPLETED
            analysis.missing_skills = []
            analysis.skill_gaps = {}
            analysis.recommended_actions = []
            analysis.alternative_suggestions = {
                "summary": (
                    "Your current profile appears far from this role's requirements. "
                    "Consider focusing on foundational skills or adjacent roles first."
                ),
                "reason": "low_match_score",
                "match_score": match_score,
            }
            analysis.confidence_score = 0.2
            analysis.estimated_time_months = None
            analysis.completed_at = timezone.now()
            analysis.save()
            return {
                "status": "completed_low_fit",
                "analysis_id": analysis_id,
                "match_score": match_score,
            }

        # Perform analysis
        analyzer = SkillGapAnalyzer()
        analysis_result = analyzer.analyze_skill_gaps(user_profile, opportunity)

        # Check for errors in analysis
        if "error" in analysis_result:
            analysis.status = SkillGapAnalysis.Status.FAILED
            analysis.error_message = sanitize_ai_error_message(analysis_result["error"])
            analysis.save()
            return {"status": "failed", "error": analysis.error_message}

        # Update analysis record with results
        analysis.status = SkillGapAnalysis.Status.COMPLETED
        analysis.missing_skills = analysis_result["missing_skills"]
        analysis.skill_gaps = analysis_result["skill_gaps"]
        analysis.recommended_actions = analysis_result["recommended_actions"]
        analysis.alternative_suggestions = analysis_result["alternative_suggestions"]
        analysis.confidence_score = analysis_result["confidence_score"]
        analysis.estimated_time_months = analysis_result["estimated_time_months"]
        analysis.completed_at = timezone.now()
        analysis.save()

        return {
            "status": "completed",
            "analysis_id": analysis_id,
            "confidence_score": analysis.confidence_score,
            "missing_skills_count": len(analysis.missing_skills),
            "recommendations_count": len(analysis.recommended_actions),
        }

    except SkillGapAnalysis.DoesNotExist:
        return {"status": "failed", "error": f"Analysis {analysis_id} not found"}

    except Exception as e:
        # Update analysis status on failure
        try:
            analysis.status = SkillGapAnalysis.Status.FAILED
            analysis.error_message = sanitize_ai_error_message(e)
            analysis.save()
        except Exception:
            pass  # If we can't save the error, just log it

        return {"status": "failed", "error": sanitize_ai_error_message(e)}
