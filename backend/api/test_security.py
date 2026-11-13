import base64
import os
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote

import certifi

from django.contrib.auth.models import AnonymousUser, User
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate
from unittest.mock import ANY, patch

from .security import (
    LegacyOperatorPermission,
    bounded_float,
    bounded_int,
    is_safe_legacy_session_id,
    normalize_tickers,
    optional_iso_date,
    parse_bool,
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent


class LegacySecurityTests(SimpleTestCase):
    @override_settings(CADRISYN_LEGACY_ENABLED=True)
    def test_browser_cached_basic_credentials_cannot_invoke_legacy_actions(self):
        from .views import ChatView

        operator = User(username="operator", is_staff=True)
        password = secrets.token_urlsafe(24)
        authorization = "Basic " + base64.b64encode(
            f"{operator.username}:{password}".encode()
        ).decode()
        factory = APIRequestFactory()
        with patch("rest_framework.authentication.BasicAuthentication.authenticate_credentials", return_value=(operator, None)) as authenticate, patch("api.views._load_ai_services") as services:
            rejected = ChatView.as_view()(factory.post("/api/chat/", {}, format="json", HTTP_AUTHORIZATION=authorization))
            self.assertEqual(rejected.status_code, 401)
            authenticate.assert_not_called()
            accepted = ChatView.as_view()(factory.post("/api/chat/", {}, format="json", HTTP_AUTHORIZATION=authorization, HTTP_X_CADRISYN_RESEARCH="1"))
            self.assertEqual(accepted.status_code, 400)
            authenticate.assert_called_once_with(operator.username, password, ANY)
            session_request = APIRequestFactory(enforce_csrf_checks=True).post("/api/chat/", {}, format="json", HTTP_X_CADRISYN_RESEARCH="1")
            session_request.user = operator
            self.assertEqual(ChatView.as_view()(session_request).status_code, 403)
            services.assert_not_called()

    def test_legacy_permission_is_disabled_by_default(self):
        permission = LegacyOperatorPermission()
        request = APIRequestFactory().get("/api/rl/train/")
        request.user = User(username="operator", is_staff=True)

        with override_settings(CADRISYN_LEGACY_ENABLED=False):
            self.assertFalse(permission.has_permission(request, None))

    def test_legacy_permission_requires_staff_when_enabled(self):
        permission = LegacyOperatorPermission()
        request = APIRequestFactory().get("/api/rl/train/")

        with override_settings(CADRISYN_LEGACY_ENABLED=True):
            request.user = AnonymousUser()
            self.assertFalse(permission.has_permission(request, None))

            request.user = User(username="analyst", is_staff=False)
            self.assertFalse(permission.has_permission(request, None))

            request.user = User(username="operator", is_staff=True)
            self.assertTrue(permission.has_permission(request, None))

    def test_disabled_legacy_view_denies_before_loading_quant_services(self):
        from unittest.mock import patch

        from .views import ChatView

        request = APIRequestFactory().post(
            "/api/chat/", {"message": "status"}, format="json"
        )
        force_authenticate(request, user=AnonymousUser())

        with override_settings(CADRISYN_LEGACY_ENABLED=False):
            with patch("api.views._load_ai_services") as load_services:
                response = ChatView.as_view()(request)

        self.assertEqual(response.status_code, 403)
        load_services.assert_not_called()

    def test_session_ids_reject_path_syntax(self):
        for invalid in ("", ".", "..", "../secret", r"..\secret", "%2e%2e%2fsecret", "x" * 65):
            with self.subTest(session_id=invalid):
                self.assertFalse(is_safe_legacy_session_id(invalid))

        self.assertTrue(is_safe_legacy_session_id("aZ09_-"))

    def test_ticker_and_numeric_inputs_are_bounded(self):
        self.assertEqual(normalize_tickers(["aapl", "BRK.B"]), ["AAPL", "BRK.B"])
        with self.assertRaises(ValueError):
            normalize_tickers(["AAPL", "../secret"])
        with self.assertRaises(ValueError):
            normalize_tickers(["AAPL"] * 21)
        with self.assertRaises(ValueError):
            bounded_int(100_001, 1, 100_000)
        with self.assertRaises(ValueError):
            bounded_float(float("nan"), 0.0, 1.0)
        with self.assertRaises(ValueError):
            bounded_float(float("inf"), 0.0, 1.0)

    def test_optional_dates_and_booleans_reject_ambiguous_values(self):
        self.assertEqual(optional_iso_date("2026-11-05"), "2026-11-05")
        for invalid_date in ("2026-02-30", "2026-W45-4", "2026-1-05"):
            with self.subTest(value=invalid_date), self.assertRaises(ValueError):
                optional_iso_date(invalid_date)
        self.assertFalse(parse_bool("false"))
        with self.assertRaises(ValueError):
            parse_bool("sometimes")


class ImportBoundaryTests(SimpleTestCase):
    def test_workspace_url_and_legacy_view_imports_do_not_load_quant_stack(self):
        code = """
import sys
import django
django.setup()
from django.urls import get_resolver
get_resolver()
import api.views
blocked = {"api.ai_services", "torch", "fastembed", "groq", "polygon"} & set(sys.modules)
if blocked:
    raise SystemExit("unexpected quant imports: " + ", ".join(sorted(blocked)))
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            environment = {key: value for key, value in os.environ.items() if not key.startswith(('DJANGO_', 'CADRISYN_', 'DATABASE_URL'))}
            environment.update(
                {
                    "DJANGO_SETTINGS_MODULE": "quantvision.settings",
                    "DJANGO_SECRET_KEY": "unit-test-only-cadrisyn-key",
                    "DJANGO_DEBUG": "true",
                    "DJANGO_ALLOWED_HOSTS": "localhost,127.0.0.1",
                    "CADRISYN_DB_PATH": str(Path(temp_dir) / "isolated.sqlite3"),
                    "CADRISYN_LEGACY_ENABLED": "false",
                    "HF_HUB_OFFLINE": "1",
                }
            )
            python_path = environment.get("PYTHONPATH")
            environment["PYTHONPATH"] = (
                str(BACKEND_ROOT)
                if not python_path
                else os.pathsep.join((str(BACKEND_ROOT), python_path))
            )
            completed = subprocess.run(
                [sys.executable, "-c", code],
                cwd=REPO_ROOT,
                env=environment,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

        self.assertEqual(
            completed.returncode,
            0,
            msg=f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )


class SettingsConfigurationTests(SimpleTestCase):
    def test_dangerous_settings_fail_closed_before_database_access(self):
        base_environment = {key: value for key, value in os.environ.items() if not key.startswith(('DJANGO_', 'CADRISYN_', 'DATABASE_URL'))}
        base_environment.update(
            {
                "DJANGO_SETTINGS_MODULE": "quantvision.settings",
                "DJANGO_DEBUG": "true",
                "DJANGO_SECRET_KEY": "unit-test-only-cadrisyn-key",
                "DJANGO_ALLOWED_HOSTS": "testserver",
                "DJANGO_CSRF_TRUSTED_ORIGINS": "",
                "CADRISYN_DB_PATH": str(
                    Path(tempfile.gettempdir()) / "cadrisyn-settings-negative-test.sqlite3"
                ),
                "DATABASE_URL": "",
                "DJANGO_CACHE_URL": "",
                "CADRISYN_LEGACY_ENABLED": "false",
                "POLYGON_API_KEY": "",
                "GROQ_API_KEY": "",
            }
        )
        legacy_database = (BACKEND_ROOT / "db.sqlite3").resolve()
        cases = (
            ("missing secret", {"DJANGO_SECRET_KEY": ""}, "DJANGO_SECRET_KEY must be configured."),
            (
                "wildcard host",
                {"DJANGO_ALLOWED_HOSTS": "*"},
                "DJANGO_ALLOWED_HOSTS must contain explicit values",
            ),
            (
                "preserved database",
                {"CADRISYN_DB_PATH": str(legacy_database)},
                "CADRISYN_DB_PATH cannot point to the preserved legacy database.",
            ),
            ("wildcard subdomains", {"DJANGO_ALLOWED_HOSTS": ".example.com"}, "must contain explicit values"),
            ("wildcard origins", {"DJANGO_CSRF_TRUSTED_ORIGINS": "https://*.example.com"}, "must contain explicit values"),
            ("invalid freshness window", {"CADRISYN_EOD_GRACE_HOURS": "49"}, "must be an integer from 0 to 48"),
            ("weak production secret", {"DJANGO_DEBUG": "false"}, "at least 50 characters"),
            ("missing production database", {"DJANGO_DEBUG": "false", "DJANGO_SECRET_KEY": "configuration-test-key-" * 4}, "explicit PostgreSQL"),
            ("missing shared cache", {"DJANGO_DEBUG": "false", "DJANGO_SECRET_KEY": "configuration-test-key-" * 4, "DATABASE_URL": "postgresql://probe:fixture@database.invalid/cadrisyn?sslmode=verify-full&sslrootcert=" + quote(certifi.where())}, "explicit shared Redis"),
            ("invalid cache URL", {"DJANGO_CACHE_URL": "file:///tmp/cache"}, "Redis URL with a host"),
        )

        for label, overrides, expected_error in cases:
            with self.subTest(configuration=label):
                environment = base_environment.copy()
                environment.update(overrides)
                completed = subprocess.run(
                    [sys.executable, "manage.py", "check"],
                    cwd=BACKEND_ROOT,
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )

                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(
                    expected_error,
                    f"{completed.stdout}\n{completed.stderr}",
                )
