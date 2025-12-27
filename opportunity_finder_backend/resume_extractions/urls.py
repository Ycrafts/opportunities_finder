from django.urls import path

from .views import (
    CVUploadView,
    CVExtractionDetailView,
    CVExtractionListView,
    CVExtractionStatusView,
    ApplyExtractionToProfileView,
)

urlpatterns = [
    # CV upload and extraction
    path("upload/", CVUploadView.as_view(), name="cv-upload"),
    path("sessions/", CVExtractionListView.as_view(), name="cv-sessions"),
    path("sessions/<int:pk>/", CVExtractionDetailView.as_view(), name="cv-extraction-detail"),
    path("sessions/<int:pk>/status/", CVExtractionStatusView.as_view(), name="cv-extraction-status"),
    path("sessions/<int:pk>/apply/", ApplyExtractionToProfileView.as_view(), name="apply-extraction"),
]
