import copy
import tempfile
import unittest
from pathlib import Path
from urllib.parse import quote

from scripts.ops.preflight import inspect_configuration


class ProductionPreflightTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        root = Path(self.folder.name)
        ca = root / 'ca.pem'
        ca.write_text('local fixture certificate path; no trusted TLS assertion')
        values = {
            'DJANGO_SECRET_KEY': 'test-only-' * 8,
            'DATABASE_URL': 'postgresql://cadrisyn:fixture@database/cadrisyn?sslmode=verify-full&sslrootcert=' + quote(str(ca)),
            'DJANGO_CACHE_URL': 'rediss://:fixture@cache:6379/0?ssl_ca_certs=' + quote(str(ca)),
        }
        self.environment = {
            'DJANGO_DEBUG': 'false', 'CADRISYN_RELEASE_PROFILE': 'demo', 'CADRISYN_WEB_RELEASE_PROFILE': 'demo',
            'DJANGO_ALLOWED_HOSTS': 'localhost', 'DJANGO_CSRF_TRUSTED_ORIGINS': 'https://localhost:8443',
            'DJANGO_TRUST_X_FORWARDED_PROTO': 'true', 'API_IMAGE': 'sha256:' + '1' * 64, 'WEB_IMAGE': 'sha256:' + '2' * 64,
        }
        for key, value in values.items():
            path = root / key
            path.write_text(value)
            self.environment[key + '_FILE'] = str(path)

    def test_safe_configuration_does_not_claim_deployment_or_trusted_storage(self):
        result = inspect_configuration(self.environment)
        self.assertEqual(result['result'], 'PASS')
        self.assertIn('Configuration only', result['scope'])
        self.assertNotIn('fixture@database', str(result))
        self.assertNotIn('test-only-', str(result))

    def test_demonstrated_unsafe_configs_cannot_pass(self):
        for mutation in [
            {'DJANGO_DEBUG': 'true'}, {'DJANGO_ALLOWED_HOSTS': '*'},
            {'DJANGO_CSRF_TRUSTED_ORIGINS': 'http://localhost'}, {'WEB_IMAGE': 'app:latest'},
            {'CADRISYN_RELEASE_PROFILE': 'development'}, {'CADRISYN_WEB_RELEASE_PROFILE': 'historical_research'},
            {'DJANGO_SECRET_KEY': 'insecure-plain-override'}, {'DATABASE_URL_FILE': '/missing'},
            {'CADRISYN_MARKET_DATA_ENABLED': 'true'}, {'DJANGO_TRUST_X_FORWARDED_PROTO': 'false'},
        ]:
            with self.subTest(mutation=mutation):
                self.assertEqual(inspect_configuration({**self.environment, **mutation})['result'], 'FAIL')
