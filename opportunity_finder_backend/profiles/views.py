from rest_framework import generics, permissions
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from .models import UserProfile
from .serializers import UserProfileSerializer, UserProfileUpdateSerializer


class MyProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_serializer_class(self):
        if self.request.method in {"PUT", "PATCH"}:
            return UserProfileUpdateSerializer
        return UserProfileSerializer

    def get_object(self) -> UserProfile:
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
