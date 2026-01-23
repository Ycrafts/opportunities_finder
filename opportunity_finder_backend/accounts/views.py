import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, permissions, status
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
)
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


class LogoutAllView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        blacklist_user_tokens(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


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
