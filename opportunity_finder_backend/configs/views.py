from rest_framework import generics, permissions
from rest_framework.response import Response

from .models import MatchConfig
from .serializers import MatchConfigReadSerializer, MatchConfigWriteSerializer


class MyConfigView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in {"PUT", "PATCH"}:
            return MatchConfigWriteSerializer
        return MatchConfigReadSerializer

    def get_object(self) -> MatchConfig:
        config, _ = MatchConfig.objects.get_or_create(user=self.request.user)
        return config

    def update(self, request, *args, **kwargs):
        """
        Accept IDs for writable relationship fields, but return nested objects (same as GET)
        for frontend convenience.
        """
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        write_serializer = MatchConfigWriteSerializer(
            instance, data=request.data, partial=partial, context=self.get_serializer_context()
        )
        write_serializer.is_valid(raise_exception=True)
        self.perform_update(write_serializer)

        read_serializer = MatchConfigReadSerializer(
            instance, context=self.get_serializer_context()
        )
        return Response(read_serializer.data)
