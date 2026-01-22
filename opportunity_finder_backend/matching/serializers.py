from rest_framework import serializers

from matching.models import Match


class OpportunitySummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    organization = serializers.CharField()
    source_url = serializers.URLField()
    deadline = serializers.DateField(allow_null=True)
    op_type = serializers.CharField(source="op_type.name")
    domain = serializers.CharField(source="domain.name")
    specialization = serializers.CharField(source="specialization.name")
    work_mode = serializers.CharField()
    employment_type = serializers.CharField()
    experience_level = serializers.CharField()
    location = serializers.SerializerMethodField()

    def get_location(self, obj):
        if not obj.location:
            return None
        if obj.location.parent:
            return f"{obj.location.name}, {obj.location.parent.name}"
        return obj.location.name


class MatchListSerializer(serializers.ModelSerializer):
    opportunity = OpportunitySummarySerializer(read_only=True)

    class Meta:
        model = Match
        fields = [
            "id",
            "opportunity",
            "match_score",
            "status",
            "created_at",
            "updated_at",
        ]


class MatchDetailSerializer(serializers.ModelSerializer):
    opportunity = OpportunitySummarySerializer(read_only=True)

    class Meta:
        model = Match
        fields = [
            "id",
            "opportunity",
            "match_score",
            "justification",
            "status",
            "stage1_passed",
            "stage2_score",
            "viewed_at",
            "saved_at",
            "created_at",
            "updated_at",
        ]
