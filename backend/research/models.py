import uuid
from typing import ClassVar

from django.conf import settings
from django.db import models


class ResearchDataset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="approved_research_datasets"
    )
    version = models.CharField(max_length=64)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering: ClassVar = ["-created_at", "id"]
        constraints: ClassVar = [models.UniqueConstraint(fields=["owner", "version"], name="research_dataset_owner_version")]


class ResearchRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    dataset = models.ForeignKey(ResearchDataset, on_delete=models.PROTECT)
    idempotency_key = models.UUIDField()
    horizon_sessions = models.PositiveSmallIntegerField()
    result = models.JSONField()
    runtime = models.JSONField()
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering: ClassVar = ["-created_at", "id"]
        constraints: ClassVar = [
            models.UniqueConstraint(fields=["owner", "idempotency_key"], name="research_run_owner_key"),
            models.CheckConstraint(condition=models.Q(horizon_sessions__in=[1, 5]), name="research_run_supported_horizon"),
        ]
