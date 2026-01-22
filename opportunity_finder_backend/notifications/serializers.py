from rest_framework import serializers

from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""

    # Include related match and opportunity info
    match_details = serializers.SerializerMethodField()
    opportunity_id = serializers.IntegerField(source='match.opportunity.id', read_only=True)
    opportunity_title = serializers.CharField(source='match.opportunity.title', read_only=True)
    organization = serializers.CharField(source='match.opportunity.organization', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'channel', 'status', 'subject', 'message',
            'sent_at', 'delivered_at', 'viewed_at', 'saved_at',
            'created_at', 'match_details', 'opportunity_id', 'opportunity_title', 'organization'
        ]
        read_only_fields = ['id', 'sent_at', 'delivered_at', 'created_at']

    def get_match_details(self, obj):
        """Include basic match information."""
        match = obj.match
        return {
            'id': match.id,
            'score': match.match_score,
            'justification': match.justification,
            'stage1_passed': match.stage1_passed,
            'stage2_score': match.stage2_score,
        }
