import hashlib
import json
import math
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache

from django.conf import settings
from django.core.cache import cache

from .indicators import calculate_indicators
from .instruments import INSTRUMENTS
from .models import MarketSnapshot
from .providers import MarketDataUnavailable, PROVIDERS


MAX_STUDY_HISTORY_BARS = 1000


@lru_cache(maxsize=1)
def exchange_calendar():
    import exchange_calendars

    return exchange_calendars.get_calendar("XNYS", start="2023-01-01", end="2030-12-31")


def session_dates(start, end):
    return [session.date() for session in exchange_calendar().sessions_in_range(start, end)]


def demo_bars(instrument):
    dates = session_dates("2024-01-02", "2026-10-30")
    position = next(index for index, item in enumerate(INSTRUMENTS) if item.id == instrument.id)
    price = 90.0 + position * 18
    bars = []
    for index, session in enumerate(dates):
        change = 0.0005 + math.sin(index * 0.37 + position) * 0.009 + math.cos(index * 0.071 + position) * 0.004
        opening = price * (1 + math.sin(index + position) * 0.0015)
        closing = opening * (1 + change)
        bars.append({
            "time": session.isoformat(),
            "open": round(opening, 4),
            "high": round(max(opening, closing) * 1.004, 4),
            "low": round(min(opening, closing) * 0.996, 4),
            "close": round(closing, 4),
            "volume": float(1_000_000 + (index * 7919 + position * 104729) % 8_000_000),
        })
        price = closing
    return bars


def validate_bars(bars):
    if not isinstance(bars, list) or not 1 <= len(bars) <= MAX_STUDY_HISTORY_BARS:
        raise MarketDataUnavailable("The provider returned an invalid daily history size.")
    previous = ""
    for bar in bars:
        if not isinstance(bar, dict) or not isinstance(bar.get("time"), str):
            raise MarketDataUnavailable("The provider returned an invalid daily bar.")
        try:
            session = date.fromisoformat(bar["time"])
            values = [bar[key] for key in ("open", "high", "low", "close", "volume")]
        except (KeyError, TypeError, ValueError) as error:
            raise MarketDataUnavailable("The provider returned an invalid daily bar.") from error
        if not exchange_calendar().is_session(session.isoformat()) or bar["time"] <= previous:
            raise MarketDataUnavailable("The provider returned invalid or duplicate market sessions.")
        if not all(isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value) for value in values):
            raise MarketDataUnavailable("The provider returned non-finite prices.")
        if min(values[:4]) <= 0 or bar["volume"] < 0:
            raise MarketDataUnavailable("The provider returned invalid prices or volume.")
        if bar["low"] > min(bar["open"], bar["close"]) or bar["high"] < max(bar["open"], bar["close"]):
            raise MarketDataUnavailable("The provider returned inconsistent OHLC prices.")
        previous = bar["time"]
    if not bars:
        raise MarketDataUnavailable("No daily bars are available for this instrument.")


def fetch_market_bars(instrument):
    import yfinance

    history = yfinance.Ticker(instrument.symbol).history(
        period="2y", interval="1d", auto_adjust=True, actions=False, timeout=10, raise_errors=True
    )
    if history.empty:
        raise MarketDataUnavailable("The provider returned no daily history.")
    now = datetime.now(timezone.utc)
    calendar = exchange_calendar()
    bars = []
    for stamp, row in history.iterrows():
        session = stamp.date().isoformat()
        if not calendar.is_session(session):
            continue
        if calendar.session_close(session).to_pydatetime() > now:
            continue
        bars.append({
            "time": session,
            "open": float(row["Open"]), "high": float(row["High"]),
            "low": float(row["Low"]), "close": float(row["Close"]),
            "volume": float(row["Volume"]),
        })
    return bars


def market_state_and_freshness(as_of, now):
    calendar = exchange_calendar()
    market_state = "open" if calendar.is_open_on_minute(now.replace(second=0, microsecond=0)) else "closed"
    recent = calendar.sessions_in_range((now.date() - timedelta(days=10)).isoformat(), now.date().isoformat())
    grace = timedelta(hours=settings.CADRISYN_EOD_GRACE_HOURS)
    completed = [session for session in recent if calendar.session_close(session).to_pydatetime() + grace <= now]
    if not completed:
        return market_state, "unavailable"
    expected = completed[-1].date().isoformat()
    return market_state, "current" if as_of >= expected else "stale"


def snapshot_identity(instrument, policy, bars):
    identity = json.dumps({"instrument": instrument.id, "source": policy.source_id, "price_basis": policy.price_basis, "bars": bars}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(identity.encode()).hexdigest()


def get_market_response(instrument, span, mode):
    policy = PROVIDERS[mode]
    policy.authorize()
    key = f"workspace:v2:{policy.source_id}:{policy.price_basis}:{instrument.id}"
    snapshot = cache.get(key)
    if snapshot is None:
        try:
            bars = demo_bars(instrument) if mode == "demo" else fetch_market_bars(instrument)
            validate_bars(bars)
            if mode == "market" and exchange_calendar().session_close(bars[-1]["time"]).to_pydatetime() > datetime.now(timezone.utc):
                raise MarketDataUnavailable("The provider returned an incomplete or future daily session.")
        except MarketDataUnavailable:
            raise
        except Exception as error:
            raise MarketDataUnavailable("The daily-data provider is unavailable. No demo data was substituted.") from error
        fetched_at = datetime.now(timezone.utc).isoformat()
        snapshot_id = snapshot_identity(instrument, policy, bars)
        payload = {"bars": bars, "fetched_at": fetched_at, "source_id": policy.source_id, "price_basis": policy.price_basis}
        record, _ = MarketSnapshot.objects.get_or_create(
            id=snapshot_id,
            defaults={"instrument_id": instrument.id, "data_mode": mode, "payload": payload},
        )
        snapshot = {**record.payload, "fetched_at": fetched_at, "snapshot_id": record.id}
        cache.set(key, snapshot, timeout=policy.ttl_seconds)

    try:
        if snapshot["source_id"] != policy.source_id or snapshot["price_basis"] != policy.price_basis:
            raise ValueError("Source policy mismatch")
        validate_bars(snapshot["bars"])
        if snapshot["snapshot_id"] != snapshot_identity(instrument, policy, snapshot["bars"]):
            raise ValueError("Content identity mismatch")
        datetime.fromisoformat(snapshot["fetched_at"])
    except (KeyError, TypeError, ValueError, MarketDataUnavailable) as error:
        raise MarketDataUnavailable("The cached dataset failed validation. No substitute data was returned.") from error

    bars = snapshot["bars"]
    as_of = bars[-1]["time"]
    lookback = {"1m": 31, "3m": 93, "6m": 186, "1y": 366, "2y": 732}[span]
    cutoff = (date.fromisoformat(as_of) - timedelta(days=lookback)).isoformat()
    visible = [bar for bar in bars if bar["time"] >= cutoff]
    indicators = calculate_indicators(bars)
    indicators = {name: [point for point in points if point["time"] >= cutoff] for name, points in indicators.items()}
    study_history = [
        {"time": bar["time"], "close": bar["close"]}
        for bar in bars[-MAX_STUDY_HISTORY_BARS:]
    ]
    state, freshness = ("unknown", "stale") if mode == "demo" else market_state_and_freshness(as_of, datetime.now(timezone.utc))
    provenance = {
        "data_mode": policy.data_mode,
        "source_id": policy.source_id,
        "source_label": policy.label,
        "as_of": as_of,
        "fetched_at": snapshot["fetched_at"],
        "price_basis": policy.price_basis,
        "freshness_state": freshness,
        "market_state": state,
        "delay_seconds": None,
        "snapshot_id": snapshot["snapshot_id"],
        "disclaimer": policy.disclaimer,
    }
    return {
        "instrument": instrument.to_dict(),
        "bars": visible,
        "study_history": study_history,
        "indicators": indicators,
        "provenance": provenance,
    }
