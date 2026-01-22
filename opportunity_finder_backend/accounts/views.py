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
    RegisterSerializer,
)


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
