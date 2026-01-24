import logging
from datetime import timedelta

from django.conf import settings
from django.db.models import Count
from django.db.models.functions import TruncWeek
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .serializers import (
    EmailTokenObtainPairSerializer,
    DeleteAccountSerializer,
    LogoutSerializer,
    MeSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    SubscriptionUpgradeRequestCreateSerializer,
    SubscriptionUpgradeRequestReviewSerializer,
    SubscriptionUpgradeRequestSerializer,
)
from .models import SubscriptionLevel, SubscriptionUpgradeRequest
from notifications.providers.brevo import get_brevo_client

logger = logging.getLogger(__name__)
User = get_user_model()


def blacklist_user_tokens(user):
    tokens = OutstandingToken.objects.filter(user=user)
    for token in tokens:
        BlacklistedToken.objects.get_or_create(token=token)


class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        # UX rule: authenticated users should not create additional accounts while logged in.
        if request.user and request.user.is_authenticated:
            return Response(
                {"detail": "You are already authenticated."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)


class EmailTokenObtainPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmailTokenObtainPairSerializer
    # SimpleJWT's TokenObtainPairView sets authentication_classes=().
    # We override it so request.user is populated when a Bearer token is sent.
    authentication_classes = [JWTAuthentication]

    def post(self, request, *args, **kwargs):
        # UX rule: authenticated users should not "log in" again while already logged in.
        if request.user and request.user.is_authenticated:
            return Response(
                {"detail": "You are already authenticated."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().post(request, *args, **kwargs)


class MeView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MeSerializer

    def get_object(self):
        return self.request.user


class LogoutView(generics.GenericAPIView):
    """
    Blacklists the provided refresh token.

    Requires `rest_framework_simplejwt.token_blacklist` in INSTALLED_APPS.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh = serializer.validated_data["refresh"]
        try:
            token = RefreshToken(refresh)
            token.blacklist()
        except TokenError:
            return Response(
                {"refresh": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionUpgradeRequestListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SubscriptionUpgradeRequest.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SubscriptionUpgradeRequestCreateSerializer
        return SubscriptionUpgradeRequestSerializer

    def create(self, request, *args, **kwargs):
        if request.user.subscription_level == SubscriptionLevel.PREMIUM:
            return Response(
                {"error": "You already have premium access."},
                status=status.HTTP_409_CONFLICT,
            )
        if SubscriptionUpgradeRequest.objects.filter(
            user=request.user,
            status=SubscriptionUpgradeRequest.Status.PENDING,
        ).exists():
            return Response(
                {"error": "You already have a pending upgrade request."},
                status=status.HTTP_409_CONFLICT,
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SubscriptionUpgradeRequestAdminListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = SubscriptionUpgradeRequestSerializer
    queryset = SubscriptionUpgradeRequest.objects.select_related("user")


class SubscriptionUpgradeRequestReviewView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = SubscriptionUpgradeRequestReviewSerializer
    queryset = SubscriptionUpgradeRequest.objects.select_related("user")

    def perform_update(self, serializer):
        upgrade_request = serializer.save(
            reviewed_by=self.request.user,
            reviewed_at=timezone.now(),
        )
        if upgrade_request.status == SubscriptionUpgradeRequest.Status.APPROVED:
            upgrade_request.user.subscription_level = SubscriptionLevel.PREMIUM
            upgrade_request.user.save(update_fields=["subscription_level"])


class LogoutAllView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        blacklist_user_tokens(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from cover_letters.models import CoverLetter
        from matching.models import Match
        from opportunities.models import Opportunity

        now = timezone.now()
        last_7_days = now - timedelta(days=7)
        last_30_days = now - timedelta(days=30)
        last_8_weeks = now - timedelta(weeks=8)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        new_opportunities_7_days = Opportunity.objects.filter(created_at__gte=last_7_days).count()
        new_opportunities_30_days = Opportunity.objects.filter(created_at__gte=last_30_days).count()

        weekly_opportunities = (
            Opportunity.objects.filter(created_at__gte=last_8_weeks)
            .annotate(week=TruncWeek("created_at"))
            .values("week")
            .annotate(count=Count("id"))
            .order_by("week")
        )
        opportunities_weekly = [
            {
                "week_start": item["week"].date().isoformat() if item["week"] else None,
                "count": item["count"],
            }
            for item in weekly_opportunities
        ]

        popular_domains = (
            Opportunity.objects.filter(
                status=Opportunity.Status.ACTIVE,
                op_type__name="JOB",
            )
            .values("domain__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )
        popular_domains_list = [
            {"name": item["domain__name"], "count": item["count"]}
            for item in popular_domains
        ]

        matches_total = Match.objects.filter(user=request.user).count()
        matches_last_7_days = Match.objects.filter(
            user=request.user,
            created_at__gte=last_7_days,
        ).count()

        active_matches = Match.objects.filter(
            user=request.user,
            status=Match.MatchStatus.ACTIVE,
        ).count()

        cover_letters_monthly_count = CoverLetter.objects.filter(
            user=request.user,
            created_at__gte=month_start,
        ).count()

        cover_letters_monthly_limit = None
        if request.user.subscription_level != SubscriptionLevel.PREMIUM:
            cover_letters_monthly_limit = 30

        return Response(
            {
                "new_opportunities_last_7_days": new_opportunities_7_days,
                "new_opportunities_last_30_days": new_opportunities_30_days,
                "opportunities_weekly": opportunities_weekly,
                "popular_domains": popular_domains_list,
                "matches_total": matches_total,
                "matches_last_7_days": matches_last_7_days,
                "active_matches": active_matches,
                "cover_letters_monthly_count": cover_letters_monthly_count,
                "cover_letters_monthly_limit": cover_letters_monthly_limit,
            }
        )


class PasswordChangeView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetRequestView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            token = PasswordResetTokenGenerator().make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000").rstrip("/")
            reset_link = f"{frontend_url}/reset-password?uid={uid}&token={token}"

            subject = "Reset your Findra password"
            message = (
                "We received a request to reset your password.\n\n"
                f"Reset link: {reset_link}\n\n"
                "If you did not request this, you can ignore this email."
            )

            try:
                brevo_client = get_brevo_client()
                if brevo_client:
                    brevo_client.send_email(
                        to_email=user.email,
                        subject=subject,
                        text=message,
                    )
                else:
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@findra.com"),
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
            except Exception:
                logger.exception("Password reset email failed for %s", user.email)

        return Response(
            {"message": "If an account exists for that email, a reset link has been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.filter(id=user_id, is_active=True).first()
        except Exception:
            user = None

        if not user or not PasswordResetTokenGenerator().check_token(user, token):
            return Response(
                {"detail": "Invalid or expired reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class DeleteAccountView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DeleteAccountSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        blacklist_user_tokens(user)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
