from django.urls import path

from matching.views import MatchDetailView, MatchListView

app_name = "matching"

urlpatterns = [
    path("", MatchListView.as_view(), name="match-list"),
    path("<int:pk>/", MatchDetailView.as_view(), name="match-detail"),
]
