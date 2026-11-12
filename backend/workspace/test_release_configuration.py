import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote

import certifi

from django.test import SimpleTestCase


class ReleaseConfigurationTests(SimpleTestCase):
    def probe(self, values):
        environment = {key: value for key, value in os.environ.items() if not key.startswith(('DJANGO_', 'CADRISYN_', 'DATABASE_URL'))}
        environment.update({
            'DJANGO_SETTINGS_MODULE': 'quantvision.settings', 'DJANGO_DEBUG': 'false',
            'DJANGO_SECRET_KEY': 'production-config-fixture-key-' * 3,
            'DJANGO_ALLOWED_HOSTS': 'localhost', 'DJANGO_CSRF_TRUSTED_ORIGINS': 'https://localhost:8443',
            'DATABASE_URL': 'postgresql://cadrisyn:fixture@database/cadrisyn?sslmode=verify-full&sslrootcert=' + quote(certifi.where()),
            'DJANGO_CACHE_URL': 'rediss://:fixture@cache:6379/0?ssl_ca_certs=' + quote(certifi.where()), 'CADRISYN_RELEASE_PROFILE': 'demo',
            **values,
        })
        return subprocess.run([sys.executable, '-c', 'from django.conf import settings; assert settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE; assert settings.CADRISYN_RELEASE_PROFILE == "demo"'], cwd=Path(__file__).resolve().parents[1], env=environment, capture_output=True, text=True)

    def test_production_secure_defaults_and_unsafe_configuration_rejection(self):
        self.assertEqual(self.probe({}).returncode, 0)
        for mutation in [
            {'CADRISYN_RELEASE_PROFILE': 'development'}, {'CADRISYN_LEGACY_ENABLED': 'true'},
            {'CADRISYN_MARKET_DATA_ENABLED': 'true'}, {'DJANGO_SECURE_SSL_REDIRECT': 'false'},
            {'DATABASE_URL': 'postgresql://cadrisyn:fixture@database/cadrisyn?sslmode=disable'},
            {'DATABASE_URL': 'postgresql://cadrisyn:fixture@database/cadrisyn?sslmode=require'},
            {'DJANGO_CACHE_URL': 'redis://:fixture@cache:6379/0'},
            {'DJANGO_CACHE_URL': 'rediss://:fixture@cache:6379/0?ssl_ca_certs=' + quote(certifi.where()) + '&ssl_cert_reqs=none'},
            {'DJANGO_CACHE_URL': 'rediss://:fixture@cache:6379/0?ssl_ca_certs=' + quote(certifi.where()) + '&ssl_check_hostname=false'},
            {'DJANGO_CSRF_TRUSTED_ORIGINS': 'http://localhost'},
        ]:
            with self.subTest(mutation=mutation):
                self.assertNotEqual(self.probe(mutation).returncode, 0)

    def test_secret_file_injection_refuses_ambiguous_plain_value(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'key'
            path.write_text('file-secret-fixture-' * 5)
            self.assertEqual(self.probe({'DJANGO_SECRET_KEY': '', 'DJANGO_SECRET_KEY_FILE': str(path)}).returncode, 0)
            result = self.probe({'DJANGO_SECRET_KEY_FILE': str(path)})
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('file-secret-fixture-', result.stderr)
