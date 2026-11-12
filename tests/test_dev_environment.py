import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from dev import ROOT, development_environment


class DevelopmentIsolationTests(unittest.TestCase):
    def test_workspace_and_legacy_keep_separate_sqlite_transaction_modes(self):
        for module, expected in (("quantvision.settings", "IMMEDIATE"), ("quantvision.legacy_settings", "DEFERRED")):
            with self.subTest(module=module):
                environment = development_environment()
                environment.update({"DJANGO_SETTINGS_MODULE": module, "CADRISYN_LEGACY_ENABLED": "false"})
                result = subprocess.run(
                    [sys.executable, "-c", "from django.conf import settings; import json; print(json.dumps(settings.DATABASES['default']['OPTIONS'].get('transaction_mode', 'DEFERRED')))"],
                    cwd=ROOT / "backend", env=environment, capture_output=True, text=True, check=True,
                )
                self.assertEqual(json.loads(result.stdout), expected)

    def test_launcher_overrides_external_storage_and_legacy_scheduler(self):
        inherited = {
            'DATABASE_URL': 'postgresql://example.invalid/shared',
            'DJANGO_CACHE_URL': 'redis://example.invalid/0',
            'CADRISYN_DB_PATH': str(ROOT / 'backend/db.sqlite3'),
            'DJANGO_SETTINGS_MODULE': 'quantvision.legacy_settings',
            'CADRISYN_LEGACY_ENABLED': 'true',
            'CADRISYN_LEGACY_SCHEDULER_ENABLED': 'true',
            'DJANGO_SECRET_KEY_FILE': '/private/production-key',
            'DATABASE_URL_FILE': '/private/production-database',
            'DJANGO_CACHE_URL_FILE': '/private/production-cache',
            'CADRISYN_RELEASE_PROFILE': 'demo',
        }
        with patch.dict(os.environ, inherited):
            environment = development_environment()
        self.assertEqual(environment['DATABASE_URL'], '')
        self.assertEqual(environment['DJANGO_CACHE_URL'], '')
        self.assertEqual(Path(environment['CADRISYN_DB_PATH']), ROOT / '.local/cadrisyn.sqlite3')
        self.assertEqual(environment['DJANGO_SETTINGS_MODULE'], 'quantvision.settings')
        self.assertEqual(environment['CADRISYN_LEGACY_ENABLED'], 'false')
        self.assertEqual(environment['CADRISYN_LEGACY_SCHEDULER_ENABLED'], 'false')
        self.assertEqual(environment['CADRISYN_RELEASE_PROFILE'], 'development')
        for name in ('DJANGO_SECRET_KEY_FILE', 'DATABASE_URL_FILE', 'DJANGO_CACHE_URL_FILE'):
            self.assertNotIn(name, environment)


if __name__ == '__main__':
    unittest.main()
