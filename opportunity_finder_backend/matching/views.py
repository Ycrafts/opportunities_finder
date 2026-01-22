from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from matching.models import Match
from matching.serializers import MatchDetailSerializer, MatchListSerializer


class MatchListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MatchListSerializer

    def get_queryset(self):
        queryset = (
            Match.objects.filter(user=self.request.user)
            .select_related(
                "opportunity",
                "opportunity__op_type",
                "opportunity__domain",
                "opportunity__specialization",
                "opportunity__location",
                "opportunity__location__parent",
            )
        )
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset


class MatchDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MatchDetailSerializer

    def get_queryset(self):
        return (
            Match.objects.filter(user=self.request.user)
            .select_related(
                "opportunity",
                "opportunity__op_type",
                "opportunity__domain",
                "opportunity__specialization",
                "opportunity__location",
                "opportunity__location__parent",
            )
        )
