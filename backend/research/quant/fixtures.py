import math
from datetime import date, timedelta

from .calendar import get_xnys_calendar, session_close_utc


def make_fixture_payload() -> dict:
    calendar = get_xnys_calendar(date(2024, 1, 2), date(2024, 9, 30), forecast_sessions=5)
    sessions = list(calendar.sessions_in_range("2024-01-02", "2024-09-30"))[:180]
    if len(sessions) != 180:
        raise RuntimeError("The installed XNYS calendar cannot build the fixed fixture range.")

    observations = []
    cumulative_split = 1.0
    for index, session in enumerate(sessions):
        split_ratio = 2.0 if index == 90 else 1.0
        cumulative_split *= split_ratio
        split_neutral_close = 80.0 + (0.075 * index) + (1.25 * math.sin(index / 8.0))
        raw_close = split_neutral_close / cumulative_split
        close_at = session_close_utc(calendar, session.date().isoformat())
        observations.append(
            {
                "session": session.date().isoformat(),
                "close": raw_close,
                "available_at": (close_at + timedelta(minutes=45)).isoformat(),
                "split_ratio": split_ratio,
                "cash_dividend": 0.35 if index in {42, 132} else 0.0,
            }
        )

    return {
        "schema_version": 1,
        "name": "Synthetic pipeline fixture",
        "instrument_id": "xnys-jpm",
        "data_kind": "synthetic_fixture",
        "source_id": "SYNTHETIC: deterministic local fixture",
        "license_reference": "SYNTHETIC: generated for local tests; no market-data license",
        "availability_evidence": "SYNTHETIC: generated at close plus 45 minutes",
        "adjustment_basis": "raw_with_causal_splits",
        "calendar": "XNYS",
        "corporate_actions_complete": True,
        "issue_lag_minutes": 60,
        "observations": observations,
    }
