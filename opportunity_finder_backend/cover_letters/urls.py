from django.urls import path

from .views import (
    CoverLetterListView,
    CoverLetterDetailView,
    CoverLetterGenerateView,
    CoverLetterRegenerateView,
)

urlpatterns = [
    # Cover letter CRUD
    path("", CoverLetterListView.as_view(), name="cover-letter-list"),
    path("<int:pk>/", CoverLetterDetailView.as_view(), name="cover-letter-detail"),

    # Cover letter generation
    path("generate/", CoverLetterGenerateView.as_view(), name="cover-letter-generate"),
    path("<int:letter_id>/regenerate/", CoverLetterRegenerateView.as_view(), name="cover-letter-regenerate"),
]
