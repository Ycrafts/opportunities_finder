from datetime import timedelta

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.feature_gating import enforce_standard_daily_limit

from .models import CoverLetter
from .serializers import (
    CoverLetterSerializer,
    CoverLetterGenerationSerializer,
    CoverLetterUpdateSerializer,
    CoverLetterListSerializer,
)
from .services.cover_letter_generator import CoverLetterGenerator


class CoverLetterListView(generics.ListAPIView):
    """
    List user's cover letters.

    GET: List all cover letters for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CoverLetterListSerializer

    def get_queryset(self):
        return CoverLetter.objects.filter(user=self.request.user).select_related("opportunity")


class CoverLetterDetailView(generics.RetrieveUpdateAPIView):
    """
    View and edit a specific cover letter.

    GET: Retrieve cover letter details
    PUT/PATCH: Update cover letter content and status
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CoverLetterSerializer

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return CoverLetterUpdateSerializer
        return CoverLetterSerializer

    def get_queryset(self):
        return CoverLetter.objects.filter(user=self.request.user).select_related("opportunity")


class CoverLetterGenerateView(generics.CreateAPIView):
    """
    Generate a new cover letter for a job opportunity.

    POST: Generate AI-powered cover letter
    Body: {"opportunity_id": 123}
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CoverLetterGenerationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        opportunity_id = serializer.validated_data["opportunity_id"]
        user = request.user

        limit_response = enforce_standard_daily_limit(
            user=user,
            model=CoverLetter,
            feature_label="cover letter generation",
            queryset_filter=lambda qs: qs.filter(
                status__in=[
                    CoverLetter.Status.GENERATED,
                    CoverLetter.Status.EDITED,
                    CoverLetter.Status.FINALIZED,
                ]
            ),
        )
        if limit_response is not None:
            return limit_response

        # Get user profile
        try:
            from profiles.models import UserProfile
            user_profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "User profile not found. Please complete your profile first."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get opportunity
        try:
            from opportunities.models import Opportunity
            opportunity = Opportunity.objects.get(id=opportunity_id)
        except Opportunity.DoesNotExist:
            return Response(
                {"error": "Opportunity not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if there's already a cover letter being generated for this opportunity
        generating_letter = CoverLetter.objects.filter(
            user=user,
            opportunity=opportunity,
            status=CoverLetter.Status.GENERATING
        ).first()

        if generating_letter:
            return Response(
                {"error": "A cover letter is already being generated for this opportunity. Please wait for it to complete."},
                status=status.HTTP_409_CONFLICT
            )

        # Rate limiting: Check if user has generated too many letters recently
        recent_generations = CoverLetter.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timedelta(minutes=5)
        ).count()

        if recent_generations >= 3:  # Max 3 generations per 5 minutes
            return Response(
                {"error": "Too many cover letter generations. Please wait a few minutes before generating another."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Check if user already has completed cover letters for this opportunity
        existing_letter = CoverLetter.objects.filter(
            user=user,
            opportunity=opportunity
        ).exclude(status=CoverLetter.Status.GENERATING).order_by("-version").first()

        # Determine version number
        version = (existing_letter.version + 1) if existing_letter else 1

        # Create cover letter record in GENERATING status
        cover_letter = CoverLetter.objects.create(
            user=user,
            opportunity=opportunity,
            version=version,
            status=CoverLetter.Status.GENERATING
        )

        from django.conf import settings

        if getattr(settings, "CELERY_ENABLED", True):
            # Queue async generation task
            from .tasks import generate_cover_letter_task
            task = generate_cover_letter_task.delay(
                user_id=user.id,
                opportunity_id=opportunity.id,
                version=version,
                existing_letter_id=existing_letter.id if existing_letter else None
            )

            # Store task ID for tracking (optional)
            cover_letter.task_id = task.id
            cover_letter.save(update_fields=['task_id'])

            # Return the cover letter in generating status
            response_serializer = CoverLetterSerializer(cover_letter)
            return Response(response_serializer.data, status=status.HTTP_202_ACCEPTED)

        generator = CoverLetterGenerator()
        try:
            generated_content = generator.generate_cover_letter(
                user_profile=user_profile,
                opportunity=opportunity,
                existing_letter=existing_letter,
            )
            cover_letter.generated_content = generated_content
            cover_letter.status = CoverLetter.Status.GENERATED
            cover_letter.save(update_fields=["generated_content", "status"])
        except Exception as e:
            cover_letter.status = CoverLetter.Status.FAILED
            cover_letter.error_message = str(e)
            cover_letter.save(update_fields=["status", "error_message"])
            return Response({"error": "Failed to generate cover letter."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_serializer = CoverLetterSerializer(cover_letter)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class CoverLetterRegenerateView(generics.CreateAPIView):
    """
    Regenerate an existing cover letter with updated profile data.

    POST: Create new version of existing cover letter
    """
    permission_classes = [IsAuthenticated]

    def create(self, request, letter_id, *args, **kwargs):
        try:
            letter = CoverLetter.objects.get(id=letter_id, user=request.user)
        except CoverLetter.DoesNotExist:
            return Response(
                {"error": "Cover letter not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if there's already a regeneration in progress for this opportunity
        generating_letter = CoverLetter.objects.filter(
            user=request.user,
            opportunity=letter.opportunity,
            status=CoverLetter.Status.GENERATING
        ).first()

        if generating_letter:
            return Response(
                {"error": "A cover letter is already being generated for this opportunity. Please wait for it to complete."},
                status=status.HTTP_409_CONFLICT
            )

        # Rate limiting: Check if user has generated too many letters recently
        recent_generations = CoverLetter.objects.filter(
            user=request.user,
            created_at__gte=timezone.now() - timedelta(minutes=5)
        ).count()

        if recent_generations >= 3:  # Max 3 generations per 5 minutes
            return Response(
                {"error": "Too many cover letter generations. Please wait a few minutes before generating another."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Get user profile
        try:
            from profiles.models import UserProfile
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "User profile not found."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if regeneration is needed
        generator = CoverLetterGenerator()
        if not generator.should_regenerate(letter, user_profile):
            return Response(
                {"error": "Profile hasn't been updated since last generation."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create new version in GENERATING status
        new_letter = CoverLetter.objects.create(
            user=request.user,
            opportunity=letter.opportunity,
            version=letter.version + 1,
            status=CoverLetter.Status.GENERATING
        )

        from django.conf import settings

        if getattr(settings, "CELERY_ENABLED", True):
            # Queue async regeneration task
            from .tasks import generate_cover_letter_task
            task = generate_cover_letter_task.delay(
                user_id=request.user.id,
                opportunity_id=letter.opportunity.id,
                version=new_letter.version,
                existing_letter_id=letter.id
            )

            # Store task ID
            new_letter.task_id = task.id
            new_letter.save(update_fields=['task_id'])

            response_serializer = CoverLetterSerializer(new_letter)
            return Response(response_serializer.data, status=status.HTTP_202_ACCEPTED)

        try:
            generated_content = generator.generate_cover_letter(
                user_profile=user_profile,
                opportunity=letter.opportunity,
                existing_letter=letter,
            )
            new_letter.generated_content = generated_content
            new_letter.status = CoverLetter.Status.GENERATED
            new_letter.save(update_fields=["generated_content", "status"])
        except Exception as e:
            new_letter.status = CoverLetter.Status.FAILED
            new_letter.error_message = str(e)
            new_letter.save(update_fields=["status", "error_message"])
            return Response({"error": "Failed to generate cover letter."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_serializer = CoverLetterSerializer(new_letter)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
