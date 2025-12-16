from rest_framework import serializers

from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    cv_file = serializers.FileField(read_only=True)
    # Make request/Swagger explicit (JSONFields should be object/array, not "string")
    academic_info = serializers.DictField(required=False)
    skills = serializers.ListField(child=serializers.CharField(), required=False)
    interests = serializers.ListField(child=serializers.CharField(), required=False)
    languages = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = UserProfile
        fields = (
            "full_name",
            "telegram_id",
            "cv_file",
            "cv_text",
            "academic_info",
            "skills",
            "interests",
            "languages",
            "matching_doc_version",
            "matching_profile_json",
            "matching_profile_text",
            "matching_profile_updated_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "cv_file",
            "matching_doc_version",
            "matching_profile_json",
            "matching_profile_text",
            "matching_profile_updated_at",
            "created_at",
            "updated_at",
        )


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Request serializer (PATCH/PUT) so Swagger shows cv_file as a real file upload.
    """

    cv_file = serializers.FileField(required=False, allow_null=True)
    academic_info = serializers.DictField(required=False)
    skills = serializers.ListField(child=serializers.CharField(), required=False)
    interests = serializers.ListField(child=serializers.CharField(), required=False)
    languages = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = UserProfile
        fields = (
            "full_name",
            "telegram_id",
            "cv_file",
            "cv_text",
            "academic_info",
            "skills",
            "interests",
            "languages",
        )


