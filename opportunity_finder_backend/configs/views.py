from django.db import transaction

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

        # One-time onboarding backfill:
        # After the user sets preferences for the first time AND has a matching profile snapshot,
        # backfill matches against recent opportunities (defaults to MATCHING_BACKFILL_DAYS=5).
        try:
            from matching.tasks import backfill_recent_opportunities_for_user
            from profiles.models import UserProfile

            with transaction.atomic():
                profile = UserProfile.objects.select_for_update().filter(user=request.user).first()
                if profile and (profile.matching_profile_json or {}):
                    flags = dict(((profile.matching_profile_json or {}).get("flags")) or {})
                    if not flags.get("onboarding_backfill_done"):
                        backfill_recent_opportunities_for_user.delay(request.user.id)
                        flags["onboarding_backfill_done"] = True
                        profile.matching_profile_json = {
                            **(profile.matching_profile_json or {}),
                            "flags": flags,
                        }
                        profile.save(update_fields=["matching_profile_json"])
        except Exception:
            # Never block config updates if backfill scheduling fails.
            pass

        read_serializer = MatchConfigReadSerializer(
            instance, context=self.get_serializer_context()
        )
        return Response(read_serializer.data)
