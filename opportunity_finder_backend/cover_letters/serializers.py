from rest_framework import serializers

from .models import CoverLetter


class CoverLetterSerializer(serializers.ModelSerializer):
    """Serializer for cover letter CRUD operations."""

    opportunity_title = serializers.CharField(source="opportunity.title", read_only=True)
    opportunity_organization = serializers.CharField(source="opportunity.organization", read_only=True)
    final_content = serializers.SerializerMethodField()

    class Meta:
        model = CoverLetter
        fields = [
            "id",
            "opportunity",
            "opportunity_title",
            "opportunity_organization",
            "generated_content",
            "edited_content",
            "final_content",
            "status",
            "version",
            "task_id",
            "error_message",
            "created_at",
            "updated_at",
            "finalized_at",
        ]
        read_only_fields = [
            "id",
            "generated_content",  # Only set during generation
            "version",
            "task_id",
            "error_message",
            "created_at",
            "updated_at",
            "finalized_at",
        ]

    def get_final_content(self, obj):
        return obj.final_content


class CoverLetterGenerationSerializer(serializers.Serializer):
    """Serializer for cover letter generation requests."""

    opportunity_id = serializers.IntegerField(required=True)

    def validate_opportunity_id(self, value):
        """Validate that the opportunity exists and is a job."""
        from opportunities.models import Opportunity, OpportunityType

        try:
            opportunity = Opportunity.objects.get(id=value)
            # Check if it's a job opportunity (not scholarship)
            if opportunity.op_type.name != "JOB":
                raise serializers.ValidationError("Cover letters can only be generated for job opportunities.")
            return value
        except Opportunity.DoesNotExist:
            raise serializers.ValidationError("Opportunity not found.")


class CoverLetterUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating cover letter content."""

    class Meta:
        model = CoverLetter
        fields = ["edited_content", "status"]

    def update(self, instance, validated_data):
        """Handle status updates and finalization."""
        edited_content = validated_data.get("edited_content")
        status = validated_data.get("status")

        if edited_content is not None:
            instance.edited_content = edited_content
            if edited_content.strip() and instance.status == CoverLetter.Status.GENERATED:
                instance.status = CoverLetter.Status.EDITED

        if status == CoverLetter.Status.FINALIZED and not instance.finalized_at:
            from django.utils import timezone
            instance.finalized_at = timezone.now()

        instance.save()
        return instance


class CoverLetterListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing cover letters."""

    opportunity_title = serializers.CharField(source="opportunity.title", read_only=True)
    opportunity_organization = serializers.CharField(source="opportunity.organization", read_only=True)
    is_edited = serializers.SerializerMethodField()

    class Meta:
        model = CoverLetter
        fields = [
            "id",
            "opportunity",
            "opportunity_title",
            "opportunity_organization",
            "status",
            "version",
            "is_edited",
            "created_at",
            "updated_at",
        ]

    def get_is_edited(self, obj):
        return obj.is_edited
