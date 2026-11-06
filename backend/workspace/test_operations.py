import importlib.util
import io
import json
import logging
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.db import OperationalError, connection
from django.test import TestCase, override_settings
from django.utils import timezone
from operations.logging import JsonFormatter
from redis.exceptions import ConnectionError as RedisConnectionError
from rest_framework.throttling import AnonRateThrottle

from .instruments import INSTRUMENTS
from .market_data import MarketDataUnavailable, get_market_response, validate_bars
from .providers import market_data_available


class ProviderPolicyTests(TestCase):
    def setUp(self):
        cache.clear()

    @override_settings(CADRISYN_MARKET_DATA_ENABLED=True, DEBUG=True, CADRISYN_YAHOO_PERSONAL_USE_ACKNOWLEDGED=False)
    @patch("workspace.market_data.cache.get")
    def test_acknowledgement_is_required_even_for_cached_data(self, cached):
        with self.assertRaises(MarketDataUnavailable):
            get_market_response(INSTRUMENTS[0], "1y", "market")
        cached.assert_not_called()
        self.assertFalse(market_data_available())

    @override_settings(CADRISYN_MARKET_DATA_ENABLED=True, DEBUG=False, CADRISYN_YAHOO_PERSONAL_USE_ACKNOWLEDGED=True)
    @patch("workspace.market_data.fetch_market_bars")
    def test_personal_adapter_cannot_be_enabled_in_production(self, provider):
        with self.assertRaises(MarketDataUnavailable):
            get_market_response(INSTRUMENTS[0], "1y", "market")
        provider.assert_not_called()

    @patch("workspace.market_data.cache.get", return_value={"source_id": "other-provider", "price_basis": "synthetic"})
    def test_wrong_source_in_cache_is_unavailable(self, cached):
        with self.assertRaisesMessage(MarketDataUnavailable, "cached dataset failed validation"):
            get_market_response(INSTRUMENTS[0], "1y", "demo")

    def test_malformed_data_is_rejected_at_boundary(self):
        bar = {"time": "2025-01-02", "open": 100, "high": 102, "low": 99, "close": 101, "volume": 10}
        for data in ([{**bar, "open": True}], [{**bar, "volume": "10"}], [{"time": "2025-01-02"}], [], [bar] * 1001):
            with self.subTest(data=str(data)[:80]), self.assertRaises(MarketDataUnavailable):
                validate_bars(data)

    def test_cache_content_must_match_its_snapshot_identity(self):
        first = get_market_response(INSTRUMENTS[0], "1y", "demo")
        key = "workspace:v2:cadrisyn-synthetic-v1:synthetic:xnas-aapl"
        cached = cache.get(key)
        cached["bars"][-1]["volume"] += 1
        cache.set(key, cached)
        with self.assertRaisesMessage(MarketDataUnavailable, "cached dataset failed validation"):
            get_market_response(INSTRUMENTS[0], "1y", "demo")
        self.assertEqual(first["provenance"]["data_mode"], "demo")


class OperationsTests(TestCase):
    def test_workspace_transfer_refuses_retained_destination_sessions(self):
        path = Path(__file__).resolve().parents[2] / "scripts/migrate_workspace.py"
        spec = importlib.util.spec_from_file_location("workspace_transfer", path)
        transfer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(transfer)
        transfer.require_empty_destination([])
        Session.objects.create(session_key="retained-session", session_data="old session", expire_date=timezone.now() + timedelta(hours=1))
        with self.assertRaisesMessage(ValueError, "session"):
            transfer.require_empty_destination([])
    @override_settings(CADRISYN_TRUST_REQUEST_ID=True)
    def test_explicit_trusted_ingress_preserves_only_valid_request_ids(self):
        expected = "a" * 32
        response = self.client.get("/api/v1/session/", HTTP_X_REQUEST_ID=expected)
        self.assertEqual(response["X-Request-ID"], expected)
        rejected = self.client.get("/api/v1/session/", HTTP_X_REQUEST_ID="not-a-safe-id")
        self.assertNotEqual(rejected["X-Request-ID"], "not-a-safe-id")

    @override_settings(CADRISYN_TRUST_CLIENT_IP=False)
    def test_untrusted_forwarding_headers_cannot_change_client_throttle_identity(self):
        response = self.client.get("/api/v1/session/", REMOTE_ADDR="198.51.100.2", HTTP_X_CADRISYN_CLIENT_IP="203.0.113.8", HTTP_X_FORWARDED_FOR="203.0.113.9")
        self.assertEqual(AnonRateThrottle().get_ident(response.wsgi_request), "198.51.100.2")

    @override_settings(CADRISYN_TRUST_CLIENT_IP=True)
    def test_trusted_ingress_supplies_validated_client_identity(self):
        response = self.client.get("/api/v1/session/", REMOTE_ADDR="172.18.0.2", HTTP_X_CADRISYN_CLIENT_IP="198.51.100.2", HTTP_X_FORWARDED_FOR="203.0.113.9")
        self.assertEqual(AnonRateThrottle().get_ident(response.wsgi_request), "198.51.100.2")
        invalid = self.client.get("/api/v1/session/", HTTP_X_CADRISYN_CLIENT_IP="invalid-client")
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(invalid.json()["request_id"], invalid["X-Request-ID"])

    def test_readiness_checks_real_database_schema_and_cache(self):
        response = self.client.get("/health/ready/")
        self.assertEqual(response.status_code, 200)
        expected = {"database": True, "cache": True}
        if connection.vendor == "postgresql":
            expected["database_role"] = True
        self.assertEqual(response.json()["checks"], expected)
        self.assertEqual(response["Cache-Control"], "no-store")

    @patch("operations.health.MigrationExecutor")
    @patch("operations.health.connection")
    def test_privileged_application_database_role_is_not_ready(self, database, executor):
        database.vendor = "postgresql"
        database.cursor.return_value.__enter__.return_value.fetchone.side_effect = [
            (1,),
            (True, False, False, False, False, False, False, False),
        ]
        executor.return_value.migration_plan.return_value = []
        response = self.client.get("/health/ready/")
        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json()["checks"]["database_role"])

    @patch("operations.health.MigrationExecutor")
    @patch("operations.health.connection")
    def test_runtime_database_owner_is_not_ready(self, database, executor):
        database.vendor = "postgresql"
        database.cursor.return_value.__enter__.return_value.fetchone.side_effect = [
            (1,),
            (False, False, False, False, False, True, False, False),
        ]
        executor.return_value.migration_plan.return_value = []
        response = self.client.get("/health/ready/")
        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json()["checks"]["database_role"])

    @patch("operations.health.cache.set", side_effect=RedisConnectionError("password=private"))
    def test_cache_failure_changes_readiness_but_not_liveness(self, cache_set):
        response = self.client.get("/health/ready/")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private", response.content.decode())
        self.assertEqual(self.client.get("/health/").status_code, 200)

    @patch("operations.health.MigrationExecutor")
    def test_pending_migrations_block_readiness(self, executor):
        executor.return_value.migration_plan.return_value = [object()]
        self.assertEqual(self.client.get("/health/ready/").status_code, 503)

    @patch("workspace.views.WatchlistEntry.objects.filter", side_effect=OperationalError("password=private"))
    def test_database_outage_is_sanitized_and_correlated(self, query):
        self.client.force_login(get_user_model().objects.create_user("operations-test"))
        result = self.client.get("/api/v1/watchlist/")
        self.assertEqual(result.status_code, 503)
        self.assertEqual(result.json()["request_id"], result["X-Request-ID"])
        self.assertNotIn("password", result.content.decode())
        self.assertEqual(result["Cache-Control"], "private, no-store")

    def test_request_logs_exclude_secrets_queries_and_raw_exception_messages(self):
        output = io.StringIO()
        handler = logging.StreamHandler(output)
        handler.setFormatter(JsonFormatter())
        logger = logging.getLogger("cadrisyn.requests")
        logger.addHandler(handler)
        try:
            response = self.client.get("/api/v1/session/?token=private-secret", HTTP_X_REQUEST_ID="attacker-controlled")
        finally:
            logger.removeHandler(handler)
        entry = json.loads(output.getvalue().splitlines()[-1])
        self.assertEqual(entry["request_id"], response["X-Request-ID"])
        self.assertEqual(entry["route"], "api/v1/session/")
        self.assertNotIn("private-secret", output.getvalue())
        self.assertNotIn("attacker-controlled", output.getvalue())
        record = logging.LogRecord("django.request", logging.ERROR, "", 0, "password=private-secret", (), None)
        self.assertNotIn("private-secret", JsonFormatter().format(record))
