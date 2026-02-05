from django.utils import timezone
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.feature_gating import enforce_standard_daily_limit

from .models import CVExtractionSession
from .serializers import CVUploadSerializer, CVExtractionResultSerializer, CVExtractionSessionSerializer
from .services.cv_extractor import CVExtractionService


class CVUploadView(generics.CreateAPIView):
    """
    Upload CV file and initiate AI extraction.

    POST: Upload CV file
    Query param: sync=true for synchronous processing (development)
    Returns: Extraction session with results (sync) or initial info (async)
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = CVUploadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cv_file = serializer.validated_data['cv_file']
        user = request.user
        sync_processing = request.query_params.get('sync', '').lower() == 'true'

        limit_response = enforce_standard_daily_limit(
            user=user,
            model=CVExtractionSession,
            feature_label="CV extraction",
            queryset_filter=lambda qs: qs.filter(status=CVExtractionSession.Status.COMPLETED),
        )
        if limit_response is not None:
            return limit_response

        # Create extraction session
        session = CVExtractionSession.objects.create(
            user=user,
            cv_file=cv_file,
            file_name=cv_file.name,
            file_size=cv_file.size,
            status=CVExtractionSession.Status.UPLOADED
        )

        from django.conf import settings

        if sync_processing or not getattr(settings, "CELERY_ENABLED", True):
            # Process synchronously for development/testing
            service = CVExtractionService()
            try:
                service.process_cv_extraction(session)
            except Exception as e:
                # If sync processing fails, mark as failed
                session.status = CVExtractionSession.Status.FAILED
                session.error_message = str(e)
                session.save()
        else:
            # Start extraction asynchronously
            from .tasks import process_cv_extraction
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Triggering async CV extraction task for session {session.id}")
            try:
                task_result = process_cv_extraction.delay(session.id)
                logger.info(f"CV extraction task queued with task_id: {task_result.id}")
            except Exception as e:
                logger.error(f"Failed to queue CV extraction task: {str(e)}", exc_info=True)
                raise

        # Return session info (with results if sync)
        if sync_processing or not getattr(settings, "CELERY_ENABLED", True):
            response_serializer = CVExtractionResultSerializer(session)
        else:
            response_serializer = CVExtractionSessionSerializer(session)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class CVExtractionDetailView(generics.RetrieveUpdateAPIView):
    """
    Get and update CV extraction results.

    GET: Retrieve extraction session with results
    PUT/PATCH: Update extracted data before applying to profile
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CVExtractionResultSerializer

    def get_queryset(self):
        return CVExtractionSession.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        """Allow editing of extracted data."""
        session = self.get_object()

        # Only allow updates if completed or failed
        if session.status not in [CVExtractionSession.Status.COMPLETED, CVExtractionSession.Status.FAILED]:
            return Response(
                {"error": "Cannot edit extraction data until processing is complete."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update the fields that can be edited
        allowed_fields = ['academic_info', 'skills', 'interests', 'languages', 'experience']
        for field in allowed_fields:
            if field in request.data:
                setattr(session, field, request.data[field])

        session.save()
        serializer = self.get_serializer(session)
        return Response(serializer.data)


class CVExtractionListView(generics.ListAPIView):
    """
    List user's CV extraction sessions.

    GET: List all extraction sessions for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CVExtractionSessionSerializer

    def get_queryset(self):
        return CVExtractionSession.objects.filter(user=self.request.user)


class CVExtractionStatusView(generics.RetrieveAPIView):
    """
    Get extraction status for polling.

    GET: Check if extraction is complete
    Returns: Simple status response for frontend polling
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CVExtractionSessionSerializer

    def get_queryset(self):
        return CVExtractionSession.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        session = self.get_object()
        return Response({
            'status': session.status,
            'is_complete': session.status == CVExtractionSession.Status.COMPLETED,
            'is_failed': session.status == CVExtractionSession.Status.FAILED,
            'error_message': session.error_message if session.status == CVExtractionSession.Status.FAILED else None,
        })


class ApplyExtractionToProfileView(generics.UpdateAPIView):
    """
    Apply extracted CV data to user profile.

    PUT/PATCH: Apply extraction results to user's profile
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CVExtractionResultSerializer

    def get_queryset(self):
        return CVExtractionSession.objects.filter(
            user=self.request.user,
            status=CVExtractionSession.Status.COMPLETED
        )

    def update(self, request, *args, **kwargs):
        session = self.get_object()

        # Get user's profile
        from profiles.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=request.user)

        was_ready = bool((profile.matching_profile_text or "").strip())

        # Apply extracted data to profile
        extracted_data = session.get_extracted_profile_data()

        # Update profile fields (only non-empty ones)
        for field, value in extracted_data.items():
            if value:  # Only update if we have extracted data
                setattr(profile, field, value)

        if session.extracted_text:
            profile.cv_text = session.extracted_text

        if session.cv_file:
            profile.cv_file = session.cv_file

        profile.save()

        is_ready = bool((profile.matching_profile_text or "").strip())
        if is_ready and not was_ready:
            from matching.models import Match
            from django.conf import settings

            if not Match.objects.filter(user=profile.user).exists():
                if getattr(settings, "CELERY_ENABLED", True):
                    from matching.tasks import backfill_recent_opportunities_for_user

                    backfill_recent_opportunities_for_user.apply_async(
                        args=[profile.user_id],
                        countdown=30,
                    )
                else:
                    from matching.services.matcher import OpportunityMatcher

                    matcher = OpportunityMatcher()
                    matcher.match_recent_opportunities_for_user(user_id=profile.user_id)

        return Response({
            "message": "CV data successfully applied to profile",
            "profile_updated": True
        })
