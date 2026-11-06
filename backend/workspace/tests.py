import math
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, SimpleTestCase, TestCase, override_settings
from redis.exceptions import ConnectionError as RedisConnectionError

from .indicators import calculate_indicators
from .instruments import INSTRUMENTS
from .market_data import (
    MarketDataUnavailable,
    demo_bars,
    market_state_and_freshness,
    validate_bars,
)
from .models import MarketSnapshot, WatchlistEntry


class IndicatorTests(SimpleTestCase):
    def test_wilder_smoothing_matches_hand_computed_alternating_fixture(self):
        closes = [100.0 + index % 2 for index in range(15)] + [101.0, 99.0]
        bars = [{"time": str(index), "close": close} for index, close in enumerate(closes)]
        values = [point["value"] for point in calculate_indicators(bars)["rsi14"]]
        self.assertEqual(values, [50.0, 53.571429, 46.428571])

    def test_hand_computed_averages_and_monotone_rsi(self):
        bars = [{"time": str(index), "close": float(index + 1)} for index in range(60)]
        result = calculate_indicators(bars)
        self.assertEqual(result["sma20"][0]["value"], 10.5)
        self.assertEqual(result["sma50"][0]["value"], 25.5)
        self.assertEqual(result["rsi14"][0]["value"], 100)
        self.assertEqual(len(result["rsi14"]), 46)

    def test_flat_market_is_neutral_and_no_lookahead(self):
        bars = [{"time": str(index), "close": 100.0} for index in range(60)]
        earlier = calculate_indicators(bars[:40])
        bars[-1]["close"] = 10000.0
        later = calculate_indicators(bars)
        self.assertEqual(earlier["rsi14"][-1]["value"], 50)
        for name, points in earlier.items():
            self.assertEqual(points, later[name][:len(points)])

    def test_synthetic_fixture_uses_sessions_and_consistent_prices(self):
        bars = demo_bars(INSTRUMENTS[0])
        self.assertEqual(bars, demo_bars(INSTRUMENTS[0]))
        self.assertNotIn("2025-12-25", {bar["time"] for bar in bars})
        validate_bars(bars)

    def test_nonfinite_duplicate_and_invalid_ohlc_are_rejected(self):
        bar = {"time": "2025-01-02", "open": 100, "high": 102, "low": 99, "close": 101, "volume": 10}
        for bars in ([{**bar, "close": math.nan}], [bar, bar], [{**bar, "low": 101}]):
            with self.assertRaises(MarketDataUnavailable):
                validate_bars(bars)

    def test_eod_freshness_respects_holiday_and_delivery_grace(self):
        now = datetime(2025, 12, 26, 14, 0, tzinfo=timezone.utc)
        state, freshness = market_state_and_freshness("2025-12-24", now)
        self.assertEqual(state, "closed")
        self.assertEqual(freshness, "current")
        self.assertEqual(market_state_and_freshness("2025-12-23", now)[1], "stale")

    def test_freshness_delivery_window_is_configurable(self):
        now = datetime(2025, 1, 3, 22, tzinfo=timezone.utc)
        with override_settings(CADRISYN_EOD_GRACE_HOURS=4):
            self.assertEqual(market_state_and_freshness("2025-01-02", now)[1], "current")
        with override_settings(CADRISYN_EOD_GRACE_HOURS=0):
            self.assertEqual(market_state_and_freshness("2025-01-02", now)[1], "stale")


class WorkspaceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user("analyst", password="fixture-password-927!")
        self.other = get_user_model().objects.create_user("colleague", password="fixture-password-418!")
        self.client.force_login(self.user)

    def test_search_requires_authentication_and_validates_query(self):
        anonymous = Client()
        self.assertEqual(anonymous.get("/api/v1/instruments/").status_code, 403)
        result = self.client.get("/api/v1/instruments/", {"query": "apple"})
        self.assertEqual(result.json()["items"][0]["id"], "xnas-aapl")
        self.assertEqual(result.json()["items"][0]["currency"], "USD")
        self.assertEqual(self.client.get("/api/v1/instruments/", {"query": "x" * 81}).status_code, 400)

    def test_watchlist_is_private_persistent_and_idempotent(self):
        url = "/api/v1/watchlist/"
        self.assertEqual(self.client.post(url, {"instrument_id": "xnas-aapl"}, content_type="application/json").status_code, 201)
        self.assertEqual(self.client.post(url, {"instrument_id": "xnas-aapl"}, content_type="application/json").status_code, 200)
        self.assertEqual(WatchlistEntry.objects.filter(owner=self.user).count(), 1)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).json()["items"], [])
        self.client.delete(url + "xnas-aapl/")
        self.assertEqual(WatchlistEntry.objects.filter(owner=self.user).count(), 1)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(url).json()["items"][0]["symbol"], "AAPL")
        self.client.delete(url + "xnas-aapl/")
        self.assertEqual(self.client.get(url).json()["items"], [])

    def test_unknown_instruments_and_bad_modes_are_rejected(self):
        self.assertEqual(self.client.post("/api/v1/watchlist/", {"instrument_id": "../../private"}, content_type="application/json").status_code, 400)
        self.assertEqual(self.client.get("/api/v1/instruments/unknown/bars/").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/instruments/xnas-aapl/bars/?mode=live").status_code, 400)

    def test_cache_outage_returns_unavailable_without_provider_work(self):
        for operation in ("get", "set"):
            with self.subTest(operation=operation):
                with patch(f"workspace.market_data.cache.{operation}", side_effect=RedisConnectionError("private cache host")), patch("workspace.market_data.fetch_market_bars") as provider:
                    response = self.client.get("/api/v1/instruments/xnas-aapl/bars/")
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json()["code"], "cache_unavailable")
                self.assertNotIn("private cache host", response.content.decode())
                provider.assert_not_called()

    @override_settings(DATA_UPLOAD_MAX_MEMORY_SIZE=64)
    def test_oversized_json_is_rejected_before_input_processing(self):
        response = self.client.post("/api/v1/watchlist/", {"instrument_id": "x" * 128}, content_type="application/json")
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["code"], "request_too_large")
        self.assertEqual(WatchlistEntry.objects.count(), 0)

    def test_demo_bars_have_explicit_provenance_and_stable_snapshot(self):
        url = "/api/v1/instruments/xnas-aapl/bars/"
        response = self.client.get(url, {"range": "1y", "mode": "demo"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["provenance"]["data_mode"], "demo")
        self.assertEqual(payload["provenance"]["price_basis"], "synthetic")
        self.assertEqual(payload["provenance"]["as_of"], payload["bars"][-1]["time"])
        self.assertIn("not observed market", payload["provenance"]["disclaimer"])
        repeat = self.client.get(url, {"range": "1m"}).json()
        self.assertLess(len(repeat["bars"]), len(payload["bars"]))
        self.assertEqual(repeat["provenance"], payload["provenance"])
        self.assertEqual(MarketSnapshot.objects.count(), 1)
        self.assertEqual(response["Cache-Control"], "private, no-store")

    @override_settings(CADRISYN_MARKET_DATA_ENABLED=False)
    @patch("workspace.market_data.fetch_market_bars")
    def test_disabled_market_mode_does_not_call_provider(self, provider):
        result = self.client.get("/api/v1/instruments/xnas-aapl/bars/?mode=market")
        self.assertEqual(result.status_code, 503)
        provider.assert_not_called()

    @override_settings(CADRISYN_MARKET_DATA_ENABLED=True)
    @patch("workspace.market_data.fetch_market_bars", side_effect=RuntimeError("sensitive provider detail"))
    def test_provider_failure_is_unavailable_without_synthetic_fallback(self, provider):
        result = self.client.get("/api/v1/instruments/xnas-aapl/bars/?mode=market")
        self.assertEqual(result.status_code, 503)
        self.assertNotIn("sensitive provider detail", result.content.decode())
        self.assertNotIn("bars", result.json())
        self.assertEqual(MarketSnapshot.objects.count(), 0)

    @override_settings(CADRISYN_MARKET_DATA_ENABLED=True)
    @patch("workspace.market_data.fetch_market_bars")
    def test_market_payload_retains_provider_identity(self, provider):
        provider.return_value = [{"time": "2025-01-02", "open": 100, "high": 102, "low": 99, "close": 101, "volume": 10}]
        result = self.client.get("/api/v1/instruments/xnas-aapl/bars/?mode=market").json()
        self.assertEqual(result["provenance"]["data_mode"], "delayed")
        self.assertEqual(result["provenance"]["source_id"], "yahoo-personal-research")
        self.assertIsNone(result["provenance"]["delay_seconds"])

    @override_settings(CADRISYN_MARKET_DATA_ENABLED=True)
    @patch("workspace.market_data.datetime")
    @patch("workspace.market_data.fetch_market_bars")
    def test_unchanged_snapshot_records_latest_retrieval_time(self, provider, clock):
        provider.return_value = [{"time": "2025-01-02", "open": 100, "high": 102, "low": 99, "close": 101, "volume": 10}]
        first = datetime(2025, 1, 3, 12, tzinfo=timezone.utc)
        clock.now.return_value = first
        url = "/api/v1/instruments/xnas-aapl/bars/?mode=market"
        earlier = self.client.get(url).json()["provenance"]
        cache.clear()
        clock.now.return_value = first + timedelta(minutes=6)
        later = self.client.get(url).json()["provenance"]
        self.assertEqual(earlier["snapshot_id"], later["snapshot_id"])
        self.assertNotEqual(earlier["fetched_at"], later["fetched_at"])
        self.assertEqual(MarketSnapshot.objects.count(), 1)

    @patch("workspace.views.get_market_response", side_effect=RuntimeError("private implementation detail"))
    def test_unexpected_errors_return_safe_json(self, response):
        with self.assertLogs("workspace.exceptions", level="ERROR"):
            result = self.client.get("/api/v1/instruments/xnas-aapl/bars/")
        self.assertEqual(result.status_code, 500)
        self.assertEqual(result.json()["code"], "internal_error")
        self.assertTrue(result.json()["request_id"])
        self.assertNotIn("private implementation", result.content.decode())


class SessionSecurityTests(TestCase):
    def setUp(self):
        cache.clear()
        get_user_model().objects.create_user("analyst", password="fixture-password-927!")
        self.client = Client(enforce_csrf_checks=True)

    def test_login_requires_csrf_and_rotates_session_then_logout(self):
        url = "/api/v1/session/"
        credentials = {"username": "analyst", "password": "fixture-password-927!"}
        self.assertEqual(self.client.post(url, credentials, content_type="application/json").status_code, 403)
        initial = self.client.get(url).json()
        self.assertFalse(initial["authenticated"])
        result = self.client.post(url, credentials, content_type="application/json", HTTP_X_CSRFTOKEN=initial["csrf_token"])
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json()["authenticated"])
        self.assertNotEqual(initial["csrf_token"], result.json()["csrf_token"])
        self.assertEqual(self.client.post("/api/v1/watchlist/", {"instrument_id": "xnas-aapl"}, content_type="application/json").status_code, 403)
        self.assertEqual(self.client.post("/api/v1/watchlist/", {"instrument_id": "xnas-aapl"}, content_type="application/json", HTTP_X_CSRFTOKEN=result.json()["csrf_token"]).status_code, 201)
        logged_out = self.client.delete(url, HTTP_X_CSRFTOKEN=result.json()["csrf_token"])
        self.assertFalse(logged_out.json()["authenticated"])
        self.assertEqual(self.client.get("/api/v1/watchlist/").status_code, 403)

    def test_legacy_training_route_is_not_exposed_by_default(self):
        self.assertEqual(self.client.post("/api/rl/train/", {}, content_type="application/json").status_code, 404)
