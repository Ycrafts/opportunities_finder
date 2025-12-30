from rest_framework import serializers

from .models import SkillGapAnalysis


class SkillGapAnalysisCreateSerializer(serializers.Serializer):
    """Serializer for creating skill gap analysis requests."""

    opportunity_id = serializers.IntegerField(
        required=True,
        help_text="ID of the opportunity to analyze"
    )


class SkillGapAnalysisDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for skill gap analysis results."""

    opportunity_title = serializers.CharField(
        source="opportunity.title",
        read_only=True
    )
    opportunity_organization = serializers.CharField(
        source="opportunity.organization",
        read_only=True
    )

    class Meta:
        model = SkillGapAnalysis
        fields = [
            "id",
            "user",
            "opportunity",
            "opportunity_title",
            "opportunity_organization",
            "status",
            "missing_skills",
            "skill_gaps",
            "recommended_actions",
            "alternative_suggestions",
            "confidence_score",
            "estimated_time_months",
            "error_message",
            "created_at",
            "updated_at",
            "completed_at",
        ]
        read_only_fields = [
            "id", "user", "status", "missing_skills", "skill_gaps",
            "recommended_actions", "alternative_suggestions",
            "confidence_score", "estimated_time_months", "error_message",
            "created_at", "updated_at", "completed_at"
        ]


class SkillGapAnalysisListSerializer(serializers.ModelSerializer):
    """List serializer for skill gap analyses."""

    opportunity_title = serializers.CharField(
        source="opportunity.title",
        read_only=True
    )
    opportunity_organization = serializers.CharField(
        source="opportunity.organization",
        read_only=True
    )

    class Meta:
        model = SkillGapAnalysis
        fields = [
            "id",
            "opportunity_title",
            "opportunity_organization",
            "status",
            "confidence_score",
            "estimated_time_months",
            "created_at",
            "completed_at",
        ]
