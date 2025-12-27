from rest_framework import serializers

from .models import CVExtractionSession


class CVUploadSerializer(serializers.Serializer):
    """Serializer for CV file upload."""
    cv_file = serializers.FileField(required=True)

    def validate_cv_file(self, value):
        """Validate uploaded file."""
        if not value:
            raise serializers.ValidationError("CV file is required.")

        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size must be less than 10MB.")

        # Check file type
        allowed_types = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        if hasattr(value, 'content_type') and value.content_type not in allowed_types:
            # Also check file extension as fallback
            filename = value.name.lower()
            if not (filename.endswith('.pdf') or filename.endswith('.docx')):
                raise serializers.ValidationError("Only PDF and DOCX files are supported.")

        return value


class CVExtractionResultSerializer(serializers.ModelSerializer):
    """Serializer for CV extraction results."""

    extracted_profile_data = serializers.SerializerMethodField()

    class Meta:
        model = CVExtractionSession
        fields = [
            'id',
            'file_name',
            'file_size',
            'extracted_text',
            'academic_info',
            'skills',
            'interests',
            'languages',
            'experience',
            'confidence_score',
            'status',
            'error_message',
            'created_at',
            'extracted_at',
            'extracted_profile_data',
        ]
        read_only_fields = [
            'id',
            'file_name',
            'file_size',
            'extracted_text',
            'academic_info',
            'skills',
            'interests',
            'languages',
            'experience',
            'confidence_score',
            'status',
            'error_message',
            'created_at',
            'extracted_at',
            'extracted_profile_data',
        ]

    def get_extracted_profile_data(self, obj):
        """Return data in UserProfile-compatible format."""
        return obj.get_extracted_profile_data()


class CVExtractionSessionSerializer(serializers.ModelSerializer):
    """Full serializer for CV extraction sessions."""

    class Meta:
        model = CVExtractionSession
        fields = [
            'id',
            'cv_file',
            'file_name',
            'file_size',
            'extracted_text',
            'academic_info',
            'skills',
            'interests',
            'languages',
            'experience',
            'status',
            'confidence_score',
            'error_message',
            'created_at',
            'updated_at',
            'extracted_at',
        ]
        read_only_fields = [
            'id',
            'file_name',
            'file_size',
            'extracted_text',
            'academic_info',
            'skills',
            'interests',
            'languages',
            'experience',
            'status',
            'confidence_score',
            'error_message',
            'created_at',
            'updated_at',
            'extracted_at',
        ]
