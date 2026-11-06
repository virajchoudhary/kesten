from django.urls import path

from .views import (
    BarsView,
    InstrumentsView,
    SessionView,
    WatchlistItemView,
    WatchlistView,
)

urlpatterns = [
    path("session/", SessionView.as_view()),
    path("instruments/", InstrumentsView.as_view()),
    path("instruments/<str:instrument_id>/bars/", BarsView.as_view()),
    path("watchlist/", WatchlistView.as_view()),
    path("watchlist/<str:instrument_id>/", WatchlistItemView.as_view()),
]
