"""Private immutable datasets and bounded, replayable baseline evaluations."""

import hashlib
import importlib.metadata
import json
import sys
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import ResearchDataset, ResearchIntakeReceipt, ResearchRun


class ResearchConflict(ValueError):
    pass


class DatasetUnavailable(ValueError):
    pass


def dataset_info(dataset):
    payload = dataset.payload
    observations = payload["observations"]
    return {
        "id": dataset.id,
        "name": payload["name"],
        "instrument_id": payload["instrument_id"],
        "data_kind": payload["data_kind"],
        "version": dataset.version,
        "source_id": payload["source_id"],
        "license_reference": payload["license_reference"],
        "availability_evidence": payload["availability_evidence"],
        "adjustment_basis": payload["adjustment_basis"],
        "calendar": payload["calendar"],
        "observation_count": len(observations),
        "first_session": observations[0]["session"],
        "last_session": observations[-1]["session"],
        "created_at": dataset.created_at,
    }


def dataset_provenance(dataset, *, owner):
    from .intake_replay import verify_intake
    from .quant import DatasetError, parse_dataset

    if dataset.owner_id != owner.pk or not owner.is_active:
        raise DatasetUnavailable("The research dataset is unavailable.")
    try:
        parsed = parse_dataset(dataset.payload, now=timezone.now())
    except DatasetError as error:
        raise DatasetUnavailable("The dataset does not meet the research protocol.") from error
    if parsed.version != dataset.version:
        raise DatasetUnavailable("The immutable dataset failed its content check.")
    result = {
        "dataset": dataset_info(dataset),
        "point_in_time_qualification": "not_independently_verified",
        "independently_verified_source": False,
        "intake": {"status": "not_archived"},
    }
    receipt = dataset.intake_receipts.select_related("dataset").order_by("-created_at", "-id").first()
    if receipt is None:
        return result
    try:
        verify_intake(receipt, owner=owner)
    except DatasetUnavailable:
        result["intake"] = {"status": "failed", "receipt_id": str(receipt.id)}
        return result
    source = receipt.evidence["source"]
    result["intake"] = {
        "status": "verified", "receipt_id": str(receipt.id), "receipt_version": receipt.version,
        "source_attestation": "operator_attested",
        "source_id": source["source_id"], "source_url": source["source_url"],
        "terms_url": source["terms_url"], "acquired_at": source["acquired_at"],
        "review_reference": source["review_reference"],
        "artifact_sha256": {key: source[f"{key}_sha256"] for key in ("csv", "terms", "availability")},
        "declared_permissions": source["permissions"],
    }
    return result


def import_dataset(payload, *, owner, operator, synthetic_bootstrap=False, intake=None):
    from .quant import parse_dataset

    parsed = parse_dataset(payload, now=timezone.now())
    if parsed.data_kind == "historical" and intake is None:
        raise DatasetUnavailable("Historical imports require source-linked CSV intake evidence.")
    if intake is not None:
        from .ingestion import PreparedIntake

        if not isinstance(intake, PreparedIntake) or intake.dataset.version != parsed.version:
            raise DatasetUnavailable("The intake evidence does not identify this dataset.")
    if synthetic_bootstrap and (not settings.DEBUG or parsed.data_kind != "synthetic_fixture"):
        raise DatasetUnavailable("Fixture bootstrap requires development and synthetic data.")
    with transaction.atomic():
        actors = {
            actor.pk: actor for actor in get_user_model().objects.select_for_update().filter(
                pk__in=sorted({owner.pk, operator.pk})
            ).order_by("pk")
        }
        current_owner = actors.get(owner.pk)
        current_operator = actors.get(operator.pk)
        if not current_owner or not current_owner.is_active or not current_operator or not current_operator.is_active:
            raise DatasetUnavailable("Active owner and operator accounts are required.")
        if not synthetic_bootstrap and not current_operator.is_staff:
            raise DatasetUnavailable("An active staff operator must attest the import rights.")
        dataset, created = ResearchDataset.objects.get_or_create(
            owner=current_owner,
            version=parsed.version,
            defaults={
                "payload": json.loads(json.dumps(parsed.payload, allow_nan=False)),
                "approved_by": current_operator,
            },
        )
        if intake is not None:
            evidence = json.loads(intake.receipt_json)
            receipt, receipt_created = ResearchIntakeReceipt.objects.get_or_create(
                dataset=dataset,
                version=intake.version,
                defaults={
                    "approved_by": current_operator,
                    "evidence": evidence,
                    "csv_content": intake.csv_bytes,
                    "terms_content": intake.terms_bytes,
                    "availability_content": intake.availability_bytes,
                },
            )
            if not receipt_created and (
                receipt.evidence != evidence
                or bytes(receipt.csv_content) != intake.csv_bytes
                or bytes(receipt.terms_content) != intake.terms_bytes
                or bytes(receipt.availability_content) != intake.availability_bytes
            ):
                raise DatasetUnavailable("The archived intake evidence failed its content check.")
        return dataset, created


@lru_cache(maxsize=1)
def runtime_manifest():
    """Capture the loaded engine's execution environment once per process."""
    directory = Path(__file__).parent / "quant"
    digest = hashlib.sha256()
    for path in sorted(directory.glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    lock = Path(settings.BASE_DIR) / "requirements-workspace.lock.txt"
    return {
        "python": sys.version.split()[0],
        "engine_source_sha256": digest.hexdigest(),
        "dependency_lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest(),
        "dependencies": {
            name: importlib.metadata.version(name) for name in ("exchange_calendars", "pandas", "numpy", "tzdata")
        },
        "random_seed": None,
        "deterministic": True,
    }


def _check_replay(run, dataset_id, horizon):
    if run.dataset_id != dataset_id or run.horizon_sessions != horizon:
        raise ResearchConflict("This request key already belongs to different research inputs.")
    return run, False


def run_evaluation(*, owner, dataset, horizon, idempotency_key):
    from .quant import DatasetError, evaluate, parse_dataset

    if dataset.owner_id != owner.pk or not owner.is_active:
        raise DatasetUnavailable("The research dataset is unavailable.")
    if type(horizon) is not int or horizon not in (1, 5):
        raise DatasetUnavailable("Choose a one-session or five-session horizon.")
    previous = ResearchRun.objects.filter(owner=owner, idempotency_key=idempotency_key).first()
    if previous:
        return _check_replay(previous, dataset.id, horizon)
    started = timezone.now()
    try:
        parsed = parse_dataset(dataset.payload, now=started)
        if parsed.version != dataset.version:
            raise DatasetUnavailable("The immutable dataset failed its content check.")
        if parsed.data_kind == "historical":
            from .intake_replay import verify_intake

            receipt = dataset.intake_receipts.select_related("dataset").order_by("-created_at", "-id").first()
            if receipt is None:
                raise DatasetUnavailable("Historical evaluation requires archived source intake evidence.")
            verify_intake(receipt, owner=owner)
        result = evaluate(parsed, horizon=horizon)
        # Never persist a partial or non-JSON numerical result.
        json.dumps(result, allow_nan=False)
    except DatasetError as error:
        raise DatasetUnavailable("The dataset does not meet the research protocol.") from error
    runtime = runtime_manifest()
    completed = timezone.now()
    with transaction.atomic():
        current_owner = get_user_model().objects.select_for_update().get(pk=owner.pk)
        if not current_owner.is_active:
            raise DatasetUnavailable("The account is no longer active.")
        run, created = ResearchRun.objects.get_or_create(
            owner=current_owner,
            idempotency_key=idempotency_key,
            defaults={
                "dataset": dataset, "horizon_sessions": horizon, "result": result,
                "runtime": runtime, "started_at": started, "completed_at": completed,
            },
        )
        return (run, True) if created else _check_replay(run, dataset.id, horizon)


def run_info(run):
    payload = run.dataset.payload
    return {
        "id": run.id, "dataset_id": run.dataset_id, "dataset_version": run.dataset.version,
        "name": payload["name"], "data_kind": payload["data_kind"],
        "instrument_id": payload["instrument_id"], "horizon_sessions": run.horizon_sessions,
        "created_at": run.created_at, "started_at": run.started_at, "completed_at": run.completed_at,
        "attempts": 1, "status": "succeeded", "result": run.result,
        "runtime": run.runtime, "error_code": None,
    }


def validate_synthetic_export(run):
    from .quant import parse_dataset

    try:
        parsed = parse_dataset(run.dataset.payload, now=timezone.now())
    except (KeyError, TypeError, ValueError) as error:
        raise DatasetUnavailable("The saved run is not eligible for export.") from error

    result = run.result
    if (
        parsed.version != run.dataset.version
        or type(result) is not dict
        or result.get("dataset_version") != run.dataset.version
        or parsed.data_kind != "synthetic_fixture"
        or result.get("data_kind") != "synthetic_fixture"
        or result.get("evidence_kind") != "synthetic_pipeline_check"
        or result.get("empirical_performance_established") is not False
        or type(result.get("target")) is not dict
        or result["target"].get("horizon_sessions") != run.horizon_sessions
    ):
        raise DatasetUnavailable("The saved run is not eligible for export.")
