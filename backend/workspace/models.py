from django.conf import settings
from django.db import models


class WatchlistEntry(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    instrument_id = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "instrument_id"], name="workspace_watchlist_owner_instrument")
        ]


class MarketSnapshot(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    instrument_id = models.CharField(max_length=32, db_index=True)
    data_mode = models.CharField(max_length=16)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
