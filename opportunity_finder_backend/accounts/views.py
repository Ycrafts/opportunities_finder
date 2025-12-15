from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .serializers import (
    EmailTokenObtainPairSerializer,
    LogoutSerializer,
    MeSerializer,
    RegisterSerializer,
)


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
