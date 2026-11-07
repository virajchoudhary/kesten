from django.urls import path

from .views import (DatasetsView, RunsView, RunView, ResearchHistoryView, ResearchReplayView, ResearchExportView, ResearchCompareView)

urlpatterns = [
    path("datasets/", DatasetsView.as_view()),
    path("history/", ResearchHistoryView.as_view()),
    path("runs/", RunsView.as_view()),
    path("runs/<uuid:run_id>/", RunView.as_view()),
    path("runs/<uuid:run_id>/replay/", ResearchReplayView.as_view()),
    path("runs/<uuid:run_id>/export/", ResearchExportView.as_view()),
    path("runs/<uuid:run_id>/compare/<uuid:other_id>/", ResearchCompareView.as_view()),
]
