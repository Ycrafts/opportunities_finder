from django.urls import path

from .views import (
    DomainListView,
    LocationListView,
    OpportunityDetailView,
    OpportunityListView,
    OpportunityTypeListView,
    SpecializationListView,
)


urlpatterns = [
    path("", OpportunityListView.as_view(), name="opportunity-list"),
    path("<int:pk>/", OpportunityDetailView.as_view(), name="opportunity-detail"),
    # Taxonomy endpoints for match preferences
    path("taxonomy/opportunity-types/", OpportunityTypeListView.as_view(), name="opportunity-type-list"),
    path("taxonomy/domains/", DomainListView.as_view(), name="domain-list"),
    path("taxonomy/specializations/", SpecializationListView.as_view(), name="specialization-list"),
    path("taxonomy/locations/", LocationListView.as_view(), name="location-list"),
]


