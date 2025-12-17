from rest_framework import serializers

from .models import MatchConfig


class OpportunityTypeNestedSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


class DomainNestedSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    opportunity_type = serializers.SerializerMethodField(read_only=True)

    def get_opportunity_type(self, obj):
        if not getattr(obj, "opportunity_type_id", None):
            return None
        return {"id": obj.opportunity_type_id, "name": obj.opportunity_type.name}


class SpecializationNestedSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    domain = DomainNestedSerializer(read_only=True)


class LocationNestedSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    parent = serializers.SerializerMethodField()

    def get_parent(self, obj):
        if not obj.parent_id:
            return None
        return {"id": obj.parent_id, "name": obj.parent.name}


class MatchConfigWriteSerializer(serializers.ModelSerializer):
    """
    Writable serializer: relationship fields are PK lists.
    """

    class Meta:
        model = MatchConfig
        fields = (
            "threshold_score",
            "notification_frequency",
            "notify_via_telegram",
            "notify_via_email",
            "notify_via_web_push",
            "telegram_frequency",
            "email_frequency",
            "web_push_frequency",
            "max_alerts_per_day",
            "quiet_hours_start",
            "quiet_hours_end",
            "work_mode",
            "employment_type",
            "experience_level",
            "min_compensation",
            "max_compensation",
            "deadline_after",
            "deadline_before",
            "preferred_opportunity_types",
            "muted_opportunity_types",
            "preferred_domains",
            "preferred_specializations",
            "preferred_locations",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class MatchConfigReadSerializer(serializers.ModelSerializer):
    """
    Read serializer: relationship fields are nested objects for frontend convenience.
    """

    preferred_opportunity_types = OpportunityTypeNestedSerializer(many=True, read_only=True)
    muted_opportunity_types = OpportunityTypeNestedSerializer(many=True, read_only=True)
    preferred_domains = DomainNestedSerializer(many=True, read_only=True)
    preferred_specializations = SpecializationNestedSerializer(many=True, read_only=True)
    preferred_locations = LocationNestedSerializer(many=True, read_only=True)

    class Meta:
        model = MatchConfig
        fields = MatchConfigWriteSerializer.Meta.fields
        read_only_fields = fields

