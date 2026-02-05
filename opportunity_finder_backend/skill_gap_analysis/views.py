from datetime import timedelta

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.feature_gating import enforce_standard_daily_limit

from .models import SkillGapAnalysis
from .serializers import (
    SkillGapAnalysisCreateSerializer,
    SkillGapAnalysisDetailSerializer,
    SkillGapAnalysisListSerializer,
)
from .tasks import analyze_skill_gaps_task


class SkillGapAnalysisListView(generics.ListAPIView):
    """
    List user's skill gap analyses.

    GET: List all skill gap analyses for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SkillGapAnalysisListSerializer

    def get_queryset(self):
        return SkillGapAnalysis.objects.filter(
            user=self.request.user
        ).select_related("opportunity")


class SkillGapAnalysisDetailView(generics.RetrieveAPIView):
    """
    Get detailed skill gap analysis results.

    GET: Retrieve detailed analysis results
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SkillGapAnalysisDetailSerializer

    def get_queryset(self):
        return SkillGapAnalysis.objects.filter(
            user=self.request.user
        ).select_related("opportunity")


class SkillGapAnalysisCreateView(generics.CreateAPIView):
    """
    Create and trigger skill gap analysis for a specific opportunity.

    POST: Start analysis for an opportunity
    Body: {"opportunity_id": 123}
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SkillGapAnalysisCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        opportunity_id = serializer.validated_data["opportunity_id"]
        user = request.user

        limit_response = enforce_standard_daily_limit(
            user=user,
            model=SkillGapAnalysis,
            feature_label="skill gap analysis",
        )
        if limit_response is not None:
            return limit_response

        # Validate opportunity exists and user can access it
        try:
            from opportunities.models import Opportunity
            opportunity = Opportunity.objects.get(id=opportunity_id)
        except Opportunity.DoesNotExist:
            return Response(
                {"error": "Opportunity not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user has a profile
        try:
            from profiles.models import UserProfile
            user_profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "User profile not found. Please complete your profile first."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if analysis already exists
        existing_analysis = SkillGapAnalysis.objects.filter(
            user=user,
            opportunity=opportunity
        ).first()

        if existing_analysis:
            if existing_analysis.is_completed():
                # Return existing completed analysis
                response_serializer = SkillGapAnalysisDetailSerializer(existing_analysis)
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            elif existing_analysis.is_generating():
                # Analysis in progress
                return Response(
                    {
                        "message": "Analysis already in progress for this opportunity.",
                        "analysis_id": existing_analysis.id,
                        "status": existing_analysis.status
                    },
                    status=status.HTTP_409_CONFLICT
                )

        # Rate limiting: Check recent analyses (max 5 per hour)
        recent_analyses = SkillGapAnalysis.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).count()

        if recent_analyses >= 5:
            return Response(
                {"error": "Too many analyses requested. Please wait before requesting another analysis."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Create new analysis record
        analysis = SkillGapAnalysis.objects.create(
            user=user,
            opportunity=opportunity,
            status=SkillGapAnalysis.Status.GENERATING
        )

        from django.conf import settings

        if getattr(settings, "CELERY_ENABLED", True):
            # Queue the analysis task
            task = analyze_skill_gaps_task.delay(analysis.id)

            # Store task ID
            analysis.task_id = task.id
            analysis.save(update_fields=["task_id"])

            # Return the analysis record
            response_serializer = SkillGapAnalysisDetailSerializer(analysis)
            return Response(
                {
                    **response_serializer.data,
                    "message": "Skill gap analysis started. Results will be available shortly.",
                    "task_id": task.id
                },
                status=status.HTTP_202_ACCEPTED
            )

        result = analyze_skill_gaps_task(analysis.id)
        analysis.refresh_from_db()
        response_serializer = SkillGapAnalysisDetailSerializer(analysis)
        return Response(
            {
                **response_serializer.data,
                "message": "Skill gap analysis completed.",
                "result": result,
            },
            status=status.HTTP_201_CREATED,
        )
