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


class MarketDataUnavailable(Exception):
    pass


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
    previous = ""
    for bar in bars:
        session = date.fromisoformat(bar["time"])
        if not exchange_calendar().is_session(session.isoformat()) or bar["time"] <= previous:
            raise MarketDataUnavailable("The provider returned invalid or duplicate market sessions.")
        values = [bar[key] for key in ("open", "high", "low", "close", "volume")]
        if not all(math.isfinite(value) for value in values):
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


def get_market_response(instrument, span, mode):
    if mode == "market" and not getattr(settings, "CADRISYN_MARKET_DATA_ENABLED", False):
        raise MarketDataUnavailable("Market data is not enabled. Choose the explicitly labelled demo dataset.")
    key = f"workspace:v1:{mode}:{instrument.id}"
    snapshot = cache.get(key)
    if snapshot is None:
        try:
            bars = demo_bars(instrument) if mode == "demo" else fetch_market_bars(instrument)
            validate_bars(bars)
        except MarketDataUnavailable:
            raise
        except Exception as error:
            raise MarketDataUnavailable("The daily-data provider is unavailable. No demo data was substituted.") from error
        fetched_at = datetime.now(timezone.utc).isoformat()
        identity = json.dumps({"instrument": instrument.id, "mode": mode, "bars": bars}, sort_keys=True, separators=(",", ":"))
        snapshot_id = hashlib.sha256(identity.encode()).hexdigest()
        payload = {"bars": bars, "fetched_at": fetched_at}
        record, _ = MarketSnapshot.objects.get_or_create(
            id=snapshot_id,
            defaults={"instrument_id": instrument.id, "data_mode": mode, "payload": payload},
        )
        snapshot = {**record.payload, "fetched_at": fetched_at, "snapshot_id": record.id}
        cache.set(key, snapshot, timeout=300 if mode == "market" else 3600)

    bars = snapshot["bars"]
    as_of = bars[-1]["time"]
    lookback = {"1m": 31, "3m": 93, "6m": 186, "1y": 366, "2y": 732}[span]
    cutoff = (date.fromisoformat(as_of) - timedelta(days=lookback)).isoformat()
    visible = [bar for bar in bars if bar["time"] >= cutoff]
    indicators = calculate_indicators(bars)
    indicators = {name: [point for point in points if point["time"] >= cutoff] for name, points in indicators.items()}
    state, freshness = ("unknown", "stale") if mode == "demo" else market_state_and_freshness(as_of, datetime.now(timezone.utc))
    provenance = {
        "data_mode": "demo" if mode == "demo" else "delayed",
        "source_id": "cadrisyn-synthetic-v1" if mode == "demo" else "yahoo-personal-research",
        "source_label": "Synthetic demonstration dataset" if mode == "demo" else "Yahoo Finance via yfinance",
        "as_of": as_of,
        "fetched_at": snapshot["fetched_at"],
        "price_basis": "synthetic" if mode == "demo" else "split_and_dividend_adjusted",
        "freshness_state": freshness,
        "market_state": state,
        "delay_seconds": None,
        "snapshot_id": snapshot["snapshot_id"],
        "disclaimer": (
            "Synthetic prices for interface demonstration. These are not observed market prices or investment results."
            if mode == "demo" else
            "Daily historical observations for explicitly enabled personal research. Delay is not guaranteed. Not a real-time feed or redistribution entitlement."
        ),
    }
    return {"instrument": instrument.to_dict(), "bars": visible, "indicators": indicators, "provenance": provenance}
