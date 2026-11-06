from django.urls import path

from .views import DatasetsView, RunsView, RunView

urlpatterns = [
    path("datasets/", DatasetsView.as_view()),
    path("runs/", RunsView.as_view()),
    path("runs/<uuid:run_id>/", RunView.as_view()),
]
