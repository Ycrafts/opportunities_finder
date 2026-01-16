from django.db.models import Q
from rest_framework import generics, permissions

from .models import Domain, Location, Opportunity, OpportunityType, Specialization
from .serializers import (
    DomainSerializer,
    LocationSerializer,
    OpportunitySerializer,
    OpportunityTypeSerializer,
    SpecializationSerializer,
)


class OpportunityListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OpportunitySerializer

    def get_queryset(self):
        qs = Opportunity.objects.all().select_related(
            "op_type",
            "domain",
            "domain__opportunity_type",
            "specialization",
            "specialization__domain",
            "location",
            "location__parent",
        )

        # Basic search
        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description_en__icontains=q) | Q(organization__icontains=q))

        # Filters by ids
        op_type = self.request.query_params.get("op_type")
        if op_type:
            qs = qs.filter(op_type_id=op_type)

        domain = self.request.query_params.get("domain")
        if domain:
            qs = qs.filter(domain_id=domain)

        specialization = self.request.query_params.get("specialization")
        if specialization:
            qs = qs.filter(specialization_id=specialization)

        location = self.request.query_params.get("location")
        if location:
            qs = qs.filter(location_id=location)

        is_remote = self.request.query_params.get("is_remote")
        if is_remote in {"true", "false", "1", "0"}:
            qs = qs.filter(is_remote=is_remote in {"true", "1"})

        work_mode = self.request.query_params.get("work_mode")
        if work_mode:
            qs = qs.filter(work_mode=work_mode)

        experience_level = self.request.query_params.get("experience_level")
        if experience_level:
            qs = qs.filter(experience_level=experience_level)

        status_ = self.request.query_params.get("status")
        if status_:
            qs = qs.filter(status=status_)

        return qs.order_by("-published_at", "-created_at")


class OpportunityDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OpportunitySerializer
    queryset = Opportunity.objects.all().select_related(
        "op_type",
        "domain",
        "domain__opportunity_type",
        "specialization",
        "specialization__domain",
        "location",
        "location__parent",
    )


# Taxonomy list views for match preferences
# These endpoints disable pagination since taxonomy lists are typically small
class OpportunityTypeListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OpportunityTypeSerializer
    queryset = OpportunityType.objects.all().order_by("name")
    pagination_class = None


class DomainListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DomainSerializer
    queryset = Domain.objects.select_related("opportunity_type").all().order_by("name")
    pagination_class = None


class SpecializationListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SpecializationSerializer
    queryset = Specialization.objects.select_related("domain__opportunity_type").all().order_by("name")
    pagination_class = None


class LocationListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LocationSerializer
    queryset = Location.objects.select_related("parent").all().order_by("name")
    pagination_class = None
