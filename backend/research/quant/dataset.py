import hashlib
import json
import math
import re
from datetime import UTC, date, datetime, timedelta
from typing import Any

from workspace.instruments import BY_ID

from .calendar import get_xnys_calendar, session_close_utc, session_open_utc
from .errors import DatasetError
from .features import split_neutral_prices
from .types import Dataset

_ROOT_KEYS = {
    "schema_version",
    "name",
    "instrument_id",
    "data_kind",
    "source_id",
    "license_reference",
    "availability_evidence",
    "adjustment_basis",
    "calendar",
    "corporate_actions_complete",
    "issue_lag_minutes",
    "observations",
}
_OBSERVATION_KEYS = {
    "session",
    "close",
    "available_at",
    "split_ratio",
    "cash_dividend",
}
_AWARE_ISO_TIMESTAMP = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
_SYNTHETIC_LABEL = re.compile(
    r"(?:^|[^a-z0-9])(?:synthetic|fixture|demo|mock(?:ed)?|simulated|generated)(?:$|[^a-z0-9])",
    re.IGNORECASE,
)
_SYNTHETIC_WORD = re.compile(r"\bsynthetic\b", re.IGNORECASE)


def parse_dataset(payload: Any, *, now: datetime) -> Dataset:
    _require_aware_datetime(now, "Import time")
    now_utc = now.astimezone(UTC)
    _require_exact_keys(payload, _ROOT_KEYS, "Dataset")

    if type(payload["schema_version"]) is not int or payload["schema_version"] != 1:
        raise DatasetError("schema_version must be the integer 1.")
    name = _bounded_string(payload["name"], "name", 120)
    instrument_id = _bounded_string(payload["instrument_id"], "instrument_id", 32)
    data_kind = payload["data_kind"]
    if not isinstance(data_kind, str) or data_kind not in {"synthetic_fixture", "historical"}:
        raise DatasetError("data_kind must be synthetic_fixture or historical.")
    source_id = _bounded_string(payload["source_id"], "source_id", 128)
    license_reference = _bounded_string(payload["license_reference"], "license_reference", 512)
    availability_evidence = _bounded_string(
        payload["availability_evidence"], "availability_evidence", 1024
    )
    if payload["adjustment_basis"] != "raw_with_causal_splits":
        raise DatasetError("adjustment_basis must be raw_with_causal_splits.")
    if payload["calendar"] != "XNYS":
        raise DatasetError("calendar must be XNYS.")
    if payload["corporate_actions_complete"] is not True:
        raise DatasetError("corporate_actions_complete must be true.")
    if type(payload["issue_lag_minutes"]) is not int or payload["issue_lag_minutes"] != 60:
        raise DatasetError("issue_lag_minutes must be the integer 60.")
    instrument = BY_ID.get(instrument_id)
    if instrument is None or instrument.exchange != "XNYS":
        raise DatasetError("instrument_id must identify a curated XNYS instrument.")

    if data_kind == "synthetic_fixture":
        if not _SYNTHETIC_WORD.search(source_id) or not _SYNTHETIC_WORD.search(
            license_reference
        ):
            raise DatasetError(
                "Synthetic fixtures must label both source and license as SYNTHETIC."
            )
    elif any(
        _SYNTHETIC_LABEL.search(value)
        for value in (name, source_id, license_reference, availability_evidence)
    ):
        raise DatasetError("Historical dataset labels contain a known synthetic marker.")

    raw_observations = payload["observations"]
    if type(raw_observations) is not list or not 120 <= len(raw_observations) <= 1500:
        raise DatasetError("observations must contain between 120 and 1500 rows.")

    observations = []
    sessions = []
    previous_session = None
    previous_available_at = None
    for index, raw_observation in enumerate(raw_observations):
        _require_exact_keys(raw_observation, _OBSERVATION_KEYS, f"Observation {index}")
        session_text, session_date = _parse_session(raw_observation["session"], index)
        if previous_session is not None and session_date <= previous_session:
            raise DatasetError("Observation sessions must be strictly increasing.")
        previous_session = session_date
        sessions.append(session_date)

        close = _finite_number(raw_observation["close"], f"Observation {index} close")
        if close <= 0:
            raise DatasetError(f"Observation {index} close must be positive.")
        split_ratio = _finite_number(
            raw_observation["split_ratio"], f"Observation {index} split_ratio"
        )
        if split_ratio <= 0:
            raise DatasetError(f"Observation {index} split_ratio must be positive.")
        cash_dividend = _finite_number(
            raw_observation["cash_dividend"], f"Observation {index} cash_dividend"
        )
        if cash_dividend < 0:
            raise DatasetError(f"Observation {index} cash_dividend cannot be negative.")
        available_at = _parse_iso_timestamp(raw_observation["available_at"], index)
        if previous_available_at is not None and available_at <= previous_available_at:
            raise DatasetError("Observation availability timestamps must be strictly increasing.")
        previous_available_at = available_at
        observations.append(
            {
                "session": session_text,
                "close": close,
                "available_at": available_at.isoformat(),
                "split_ratio": split_ratio,
                "cash_dividend": cash_dividend,
            }
        )

    if observations[0]["split_ratio"] != 1.0:
        raise DatasetError("The first split_ratio must be 1.0 to define initial-share units.")

    calendar = get_xnys_calendar(sessions[0], sessions[-1], forecast_sessions=1)
    session_texts = [session.isoformat() for session in sessions]
    try:
        expected_sessions = [
            session.date().isoformat()
            for session in calendar.sessions_in_range(session_texts[0], session_texts[-1])
        ]
    except Exception as exc:
        raise DatasetError("Observation range is not covered by the XNYS calendar.") from exc
    if expected_sessions != session_texts:
        raise DatasetError("Observations must be contiguous XNYS trading sessions.")

    for index, observation in enumerate(observations):
        session = observation["session"]
        close_at = session_close_utc(calendar, session)
        cutoff = close_at + timedelta(minutes=60)
        available_at = datetime.fromisoformat(observation["available_at"])
        if available_at < close_at or available_at > cutoff:
            raise DatasetError(
                f"Observation {index} availability must fall between the close "
                "and 60-minute cutoff."
            )
        if available_at > now_utc:
            raise DatasetError(f"Observation {index} is not yet available at import time.")
        if cutoff > now_utc:
            raise DatasetError(f"Observation {index} information cutoff is in the future.")
        try:
            following_session = calendar.next_session(session)
        except Exception as exc:
            raise DatasetError("The XNYS calendar does not cover the next scheduled open.") from exc
        if cutoff >= session_open_utc(calendar, following_session):
            raise DatasetError("The fixed 60-minute information cutoff reaches the next open.")

    split_neutral_prices(observations)

    normalized = {
        "schema_version": 1,
        "name": name,
        "instrument_id": instrument_id,
        "data_kind": data_kind,
        "source_id": source_id,
        "license_reference": license_reference,
        "availability_evidence": availability_evidence,
        "adjustment_basis": "raw_with_causal_splits",
        "calendar": "XNYS",
        "corporate_actions_complete": True,
        "issue_lag_minutes": 60,
        "observations": observations,
    }
    canonical = _canonical_json(normalized)
    version = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return Dataset(
        payload=normalized,
        version=version,
        instrument_id=instrument_id,
        data_kind=data_kind,
    )


def canonical_json(value: Any) -> str:
    return _canonical_json(value)


def _require_exact_keys(value: Any, expected: set[str], label: str) -> None:
    if type(value) is not dict:
        raise DatasetError(f"{label} must be an object.")
    actual = set(value)
    missing = expected - actual
    extra = actual - expected
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing {', '.join(sorted(missing))}")
        if extra:
            details.append(f"unexpected {', '.join(sorted(str(key) for key in extra))}")
        raise DatasetError(f"{label} has invalid keys: {'; '.join(details)}.")


def _bounded_string(value: Any, field: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise DatasetError(f"{field} must be a string.")
    normalized = value.strip()
    if not normalized or len(normalized) > max_length:
        raise DatasetError(f"{field} must contain 1 to {max_length} characters.")
    if "\x00" in normalized:
        raise DatasetError(f"{field} cannot contain a NUL character.")
    return normalized


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DatasetError(f"{label} must be a finite JSON number.")
    try:
        normalized = float(value)
    except (OverflowError, ValueError) as exc:
        raise DatasetError(f"{label} must be a finite JSON number.") from exc
    if not math.isfinite(normalized):
        raise DatasetError(f"{label} must be a finite JSON number.")
    return normalized


def _parse_session(value: Any, index: int) -> tuple[str, date]:
    if not isinstance(value, str):
        raise DatasetError(f"Observation {index} session must be an ISO date.")
    try:
        session = date.fromisoformat(value)
    except ValueError as exc:
        raise DatasetError(f"Observation {index} session must be an ISO date.") from exc
    if session.isoformat() != value:
        raise DatasetError(f"Observation {index} session must use YYYY-MM-DD format.")
    return value, session


def _parse_iso_timestamp(value: Any, index: int) -> datetime:
    if not isinstance(value, str) or not _AWARE_ISO_TIMESTAMP.fullmatch(value):
        raise DatasetError(
            f"Observation {index} available_at must be a timezone-aware ISO timestamp."
        )
    parse_value = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        timestamp = datetime.fromisoformat(parse_value)
    except ValueError as exc:
        raise DatasetError(
            f"Observation {index} available_at must be a timezone-aware ISO timestamp."
        ) from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise DatasetError(f"Observation {index} available_at must include a timezone.")
    return timestamp.astimezone(UTC)


def _require_aware_datetime(value: Any, label: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise DatasetError(f"{label} must be timezone-aware.")


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError, OverflowError) as exc:
        raise DatasetError("Dataset cannot be represented as canonical JSON.") from exc
