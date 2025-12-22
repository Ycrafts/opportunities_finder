from rest_framework import serializers

from .models import Domain, Location, Opportunity, OpportunityType, Specialization


class OpportunityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpportunityType
        fields = ("id", "name")


class DomainSerializer(serializers.ModelSerializer):
    opportunity_type = OpportunityTypeSerializer(read_only=True)

    class Meta:
        model = Domain
        fields = ("id", "name", "opportunity_type")


class SpecializationSerializer(serializers.ModelSerializer):
    domain = DomainSerializer(read_only=True)

    class Meta:
        model = Specialization
        fields = ("id", "name", "domain")


class LocationSerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField()

    def get_parent(self, obj):
        if not obj.parent_id:
            return None
        return {"id": obj.parent_id, "name": obj.parent.name}

    class Meta:
        model = Location
        fields = ("id", "name", "parent")


class OpportunitySerializer(serializers.ModelSerializer):
    op_type = OpportunityTypeSerializer(read_only=True)
    domain = DomainSerializer(read_only=True)
    specialization = SpecializationSerializer(read_only=True)
    location = LocationSerializer(read_only=True)

    class Meta:
        model = Opportunity
        fields = (
            "id",
            "title",
            "organization",
            "description_en",
            "source_url",
            "op_type",
            "domain",
            "specialization",
            "location",
            "work_mode",
            "is_remote",
            "employment_type",
            "experience_level",
            "min_compensation",
            "max_compensation",
            "deadline",
            "status",
            "metadata",
            "published_at",
            "created_at",
            "updated_at",
        )

