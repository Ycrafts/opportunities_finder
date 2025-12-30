from django.urls import path

from .views import (
    SkillGapAnalysisCreateView,
    SkillGapAnalysisDetailView,
    SkillGapAnalysisListView,
)

app_name = 'skill_gap_analysis'

urlpatterns = [
    # Skill gap analysis CRUD
    path("", SkillGapAnalysisListView.as_view(), name="skill-gap-analysis-list"),
    path("analyze/", SkillGapAnalysisCreateView.as_view(), name="skill-gap-analysis-create"),
    path("<int:pk>/", SkillGapAnalysisDetailView.as_view(), name="skill-gap-analysis-detail"),
]
