from datetime import UTC, date, datetime, timedelta

from .errors import DatasetError


def get_xnys_calendar(
    first_session: date,
    last_session: date,
    *,
    forecast_sessions: int = 0,
):
    try:
        import exchange_calendars

        end = last_session + timedelta(days=max(14, forecast_sessions * 3 + 3))
        return exchange_calendars.get_calendar(
            "XNYS",
            start=first_session.isoformat(),
            end=end.isoformat(),
        )
    except Exception as exc:
        raise DatasetError("The XNYS exchange calendar is unavailable for this range.") from exc


def session_close_utc(calendar, session: str) -> datetime:
    try:
        value = calendar.session_close(session)
    except Exception as exc:
        raise DatasetError(f"Could not read the XNYS close for session {session}.") from exc
    return _as_utc_datetime(value)


def session_open_utc(calendar, session) -> datetime:
    try:
        value = calendar.session_open(session)
    except Exception as exc:
        raise DatasetError("Could not read the next XNYS session open.") from exc
    return _as_utc_datetime(value)


def next_session(calendar, session: str) -> str:
    try:
        value = calendar.next_session(session)
    except Exception as exc:
        raise DatasetError("The XNYS calendar does not cover the forecast horizon.") from exc
    return value.date().isoformat()


def _as_utc_datetime(value) -> datetime:
    if hasattr(value, "to_pydatetime"):
        value = value.to_pydatetime()
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise DatasetError("The XNYS calendar returned a naive timestamp.")
    return value.astimezone(UTC)
