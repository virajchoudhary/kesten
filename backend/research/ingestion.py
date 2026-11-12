import csv
import hashlib
import io
import json
import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit

from .quant.dataset import canonical_json, parse_dataset
from .quant.errors import DatasetError
from .quant.types import Dataset

_CSV_HEADER = ("session", "close", "available_at", "split_ratio", "cash_dividend")
_METADATA_KEYS = set(
    "schema_version name instrument_id data_kind source_id license_reference "
    "availability_evidence adjustment_basis calendar corporate_actions_complete "
    "issue_lag_minutes".split()
)
_SOURCE_KEYS = set(
    "schema_version source_id source_url acquired_at csv_sha256 terms_url terms_sha256 "
    "availability_sha256 review_reference permissions".split()
)
_PERMISSION_KEYS = set(
    "storage private_research backup internal_transfer redistribution".split()
)
_AWARE_ISO_TIMESTAMP = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MAX_CSV_BYTES = 2_000_000
_MAX_TERMS_BYTES = 1_000_000
_MAX_AVAILABILITY_BYTES = 2_000_000
_MAX_ROWS = 1500


@dataclass(frozen=True, slots=True)
class PreparedIntake:
    dataset: Dataset
    receipt_json: str
    version: str
    csv_bytes: bytes
    terms_bytes: bytes
    availability_bytes: bytes


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise DatasetError(message)


def strict_json_loads(raw: bytes, *, max_bytes: int = 2_000_000) -> Any:
    _check(type(raw) is bytes, "JSON input must be bytes.")
    _check(type(max_bytes) is int and max_bytes >= 0, "JSON byte limit must be non-negative.")
    _check(len(raw) <= max_bytes, "JSON input exceeds its byte limit.")
    try:
        parsed = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object_members,
            parse_constant=_reject_nonfinite_constant,
            parse_float=_finite_json_float,
        )
        _validate_unicode(parsed)
        return parsed
    except DatasetError:
        raise
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise DatasetError("JSON input must be valid UTF-8 JSON.") from exc


def prepare_csv_intake(
    *,
    csv_bytes: bytes,
    metadata: dict,
    source_record: dict,
    terms_bytes: bytes,
    availability_bytes: bytes,
    now: datetime,
) -> PreparedIntake:
    _require_aware_datetime(now, "Import time")
    _check(type(metadata) is dict, "metadata must be an object.")
    _check("observations" not in metadata, "metadata must not contain observations.")
    _require_exact_keys(metadata, _METADATA_KEYS, "metadata")

    _require_bounded_bytes(csv_bytes, _MAX_CSV_BYTES, "CSV")
    _require_bounded_bytes(terms_bytes, _MAX_TERMS_BYTES, "Terms")
    _check(bool(terms_bytes.strip()), "Terms snapshot must not be empty.")
    _require_bounded_bytes(availability_bytes, _MAX_AVAILABILITY_BYTES, "Availability evidence")
    source, acquired_at = _normalize_source_record(source_record)
    try:
        now_utc = now.astimezone(UTC)
    except (OverflowError, ValueError) as exc:
        raise DatasetError("Import time must be representable in UTC.") from exc
    _check(acquired_at <= now_utc, "source_record acquired_at cannot be in the future.")

    for field, blob in (
        ("csv_sha256", csv_bytes),
        ("terms_sha256", terms_bytes),
        ("availability_sha256", availability_bytes),
    ):
        _check(
            source[field] == hashlib.sha256(blob).hexdigest(),
            f"source_record {field} does not match the supplied bytes.",
        )

    payload = dict(metadata)
    payload["observations"] = _read_csv_observations(csv_bytes)
    try:
        dataset = parse_dataset(payload, now=now)
    except UnicodeError as exc:
        raise DatasetError("metadata must contain valid Unicode text.") from exc
    _check(
        source["source_id"] == dataset.payload["source_id"],
        "source_record source_id must match metadata source_id.",
    )
    observations = dataset.payload["observations"]
    for index, row in enumerate(observations):
        row_available_at = _parse_aware_iso(
            row["available_at"], f"Observation {index} available_at"
        )
        _check(
            acquired_at >= row_available_at,
            "source_record acquired_at cannot precede published observations.",
        )

    availability = strict_json_loads(
        availability_bytes, max_bytes=_MAX_AVAILABILITY_BYTES
    )
    _validate_availability(availability, dataset, source["source_id"])
    receipt = {
        "schema_version": 1,
        "adapter_id": "canonical-daily-close-csv-v1",
        "dataset_version": dataset.version,
        "data_kind": dataset.data_kind,
        "source": source,
        "source_attestation": "operator_attested",
        "observation_count": len(observations),
        "first_session": observations[0]["session"],
        "last_session": observations[-1]["session"],
        "independently_verified_source": False,
        "limitation": (
            "Source metadata and rights are operator attestations. Hashes prove byte identity, "
            "not entitlement or point-in-time authenticity; upstream source truth is not "
            "independently verified."
        ),
    }
    receipt_json = canonical_json(receipt)
    try:
        version = hashlib.sha256(receipt_json.encode("utf-8")).hexdigest()
    except UnicodeError as exc:
        raise DatasetError("Receipt cannot be represented as UTF-8.") from exc
    return PreparedIntake(
        dataset=dataset,
        receipt_json=receipt_json,
        version=version,
        csv_bytes=csv_bytes,
        terms_bytes=terms_bytes,
        availability_bytes=availability_bytes,
    )


def _unique_object_members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise DatasetError("JSON object member names must be unique.")
        result[key] = value
    return result


def _validate_unicode(value: Any) -> None:
    if isinstance(value, str):
        value.encode("utf-8")
    elif isinstance(value, list):
        for item in value:
            _validate_unicode(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            _validate_unicode(key)
            _validate_unicode(item)


def _reject_nonfinite_constant(value: str) -> None:
    raise DatasetError(f"JSON constant {value} is not permitted.")


def _finite_json_float(value: str) -> float:
    try:
        parsed = float(value)
    except OverflowError as exc:
        raise DatasetError("JSON numbers must be finite.") from exc
    _check(math.isfinite(parsed), "JSON numbers must be finite.")
    return parsed


def _require_bounded_bytes(value: bytes, max_bytes: int, label: str) -> None:
    _check(type(value) is bytes, f"{label} input must be bytes.")
    _check(len(value) <= max_bytes, f"{label} input exceeds its byte limit.")


def _require_exact_keys(value: Any, expected: set[str], label: str) -> None:
    _check(type(value) is dict, f"{label} must be an object.")
    _check(expected == value.keys(), f"{label} has invalid keys.")


def _required_text(value: Any, label: str, *, max_length: int | None = None) -> str:
    _check(isinstance(value, str), f"{label} must be a string.")
    normalized = value.strip()
    _check(bool(normalized) and "\x00" not in normalized, f"{label} must be non-empty.")
    try:
        normalized.encode("utf-8")
    except UnicodeError as exc:
        raise DatasetError(f"{label} must contain valid Unicode text.") from exc
    _check(max_length is None or len(normalized) <= max_length, f"{label} is too long.")
    return normalized


def _normalize_source_record(source_record: dict) -> tuple[dict, datetime]:
    _require_exact_keys(source_record, _SOURCE_KEYS, "source_record")
    _check(
        type(source_record["schema_version"]) is int and source_record["schema_version"] == 1,
        "source_record schema_version must be the integer 1.",
    )
    source_id = _required_text(
        source_record["source_id"], "source_record source_id", max_length=128
    )
    acquired_at = _parse_aware_iso(source_record["acquired_at"], "source_record acquired_at")
    permissions = source_record["permissions"]
    _require_exact_keys(permissions, _PERMISSION_KEYS, "source_record permissions")
    _check(
        all(type(value) is bool for value in permissions.values()),
        "source_record permissions values must be booleans.",
    )
    _check(
        all(
            permissions[key]
            for key in ("storage", "private_research", "backup", "internal_transfer")
        ),
        "source_record permissions must allow the four internal uses.",
    )

    hashes = {}
    for field in ("csv_sha256", "terms_sha256", "availability_sha256"):
        value = source_record[field]
        _check(
            isinstance(value, str) and _SHA256.fullmatch(value),
            f"source_record {field} must be a lowercase SHA-256 digest.",
        )
        hashes[field] = value
    review_reference = _required_text(
        source_record["review_reference"], "source_record review_reference", max_length=1024
    )
    _validate_reference_url(review_reference, "source_record review_reference")
    normalized = {
        "schema_version": 1,
        "source_id": source_id,
        "source_url": _public_https_url(source_record["source_url"], "source_record source_url"),
        "acquired_at": acquired_at.isoformat(),
        **hashes,
        "terms_url": _public_https_url(source_record["terms_url"], "source_record terms_url"),
        "review_reference": review_reference,
        "permissions": dict(permissions),
    }
    return normalized, acquired_at


def _public_https_url(value: Any, label: str) -> str:
    normalized = _required_text(value, label)
    _check(
        not any(character.isspace() for character in normalized),
        f"{label} must be an HTTPS URL.",
    )
    try:
        parts = urlsplit(normalized)
        host = parts.hostname
        has_credentials = parts.username is not None or parts.password is not None
        parts.port
    except ValueError as exc:
        raise DatasetError(f"{label} must be a public HTTPS URL.") from exc
    if (
        parts.scheme != "https"
        or not host
        or has_credentials
        or "?" in normalized
        or "#" in normalized
    ):
        raise DatasetError(f"{label} must be a public HTTPS URL without credentials or query data.")
    return normalized


def _validate_reference_url(value: str, label: str) -> None:
    if "://" in value:
        _public_https_url(value, label)


def _parse_aware_iso(value: Any, label: str) -> datetime:
    text = _required_text(value, label)
    _check(
        bool(_AWARE_ISO_TIMESTAMP.fullmatch(text)),
        f"{label} must be a timezone-aware ISO timestamp.",
    )
    parse_text = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(parse_text)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("timestamp has no UTC offset")
        return parsed.astimezone(UTC)
    except (OverflowError, ValueError) as exc:
        raise DatasetError(f"{label} must be a timezone-aware ISO timestamp.") from exc


def _require_aware_datetime(value: Any, label: str) -> None:
    try:
        aware = (
            isinstance(value, datetime)
            and value.tzinfo is not None
            and value.utcoffset() is not None
        )
    except Exception as exc:
        raise DatasetError(f"{label} must be timezone-aware.") from exc
    _check(aware, f"{label} must be timezone-aware.")


def _read_csv_observations(csv_bytes: bytes) -> list[dict]:
    try:
        text = csv_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DatasetError("CSV must be valid UTF-8.") from exc
    try:
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        _check(
            next(reader, None) == list(_CSV_HEADER),
            "CSV header must be session,close,available_at,split_ratio,cash_dividend.",
        )
        observations = []
        for index, fields in enumerate(reader):
            _check(
                len(fields) == len(_CSV_HEADER),
                f"CSV row {index + 2} must contain exactly five fields.",
            )
            _check(
                all(field.strip() for field in fields),
                f"CSV row {index + 2} must supply all five fields.",
            )
            _check(len(observations) < _MAX_ROWS, "CSV cannot contain more than 1500 observations.")
            try:
                close, split_ratio, cash_dividend = map(float, (fields[1], fields[3], fields[4]))
            except (OverflowError, ValueError) as exc:
                raise DatasetError(
                    f"CSV row {index + 2} has a non-numeric price or action."
                ) from exc
            observations.append(
                {
                    "session": fields[0],
                    "close": close,
                    "available_at": fields[2],
                    "split_ratio": split_ratio,
                    "cash_dividend": cash_dividend,
                }
            )
        return observations
    except csv.Error as exc:
        raise DatasetError("CSV is malformed.") from exc


def _validate_availability(value: Any, dataset: Dataset, source_id: str) -> None:
    _require_exact_keys(
        value,
        {"schema_version", "source_id", "observations"},
        "availability evidence",
    )
    _check(
        type(value["schema_version"]) is int and value["schema_version"] == 1,
        "availability evidence schema_version must be the integer 1.",
    )
    _check(
        value["source_id"] == source_id,
        "availability evidence source_id must match source_record source_id.",
    )
    evidence_rows = value["observations"]
    observations = dataset.payload["observations"]
    _check(
        type(evidence_rows) is list and len(evidence_rows) == len(observations),
        "availability evidence must match the dataset observation count.",
    )
    for index, (evidence, observation) in enumerate(zip(evidence_rows, observations)):
        _require_exact_keys(
            evidence,
            {"session", "available_at", "reference", "observation_sha256"},
            f"availability observation {index}",
        )
        _check(
            evidence["session"] == observation["session"],
            f"availability observation {index} session does not match.",
        )
        evidence_time = _parse_aware_iso(
            evidence["available_at"], f"availability observation {index} available_at"
        )
        _check(
            evidence_time
            == _parse_aware_iso(
                observation["available_at"], f"dataset observation {index} available_at"
            ),
            f"availability observation {index} available_at does not match.",
        )
        reference = _required_text(
            evidence["reference"], f"availability observation {index} reference", max_length=1024
        )
        _validate_reference_url(reference, f"availability observation {index} reference")
        expected_hash = hashlib.sha256(canonical_json(observation).encode("utf-8")).hexdigest()
        _check(
            evidence["observation_sha256"] == expected_hash,
            f"availability observation {index} observation_sha256 does not match.",
        )
