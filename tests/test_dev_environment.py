import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from dev import ROOT, development_environment


class DevelopmentIsolationTests(unittest.TestCase):
    def test_launcher_overrides_external_storage_and_legacy_scheduler(self):
        inherited = {
            'DATABASE_URL': 'postgresql://example.invalid/shared',
            'DJANGO_CACHE_URL': 'redis://example.invalid/0',
            'CADRISYN_DB_PATH': str(ROOT / 'backend/db.sqlite3'),
            'DJANGO_SETTINGS_MODULE': 'quantvision.legacy_settings',
            'CADRISYN_LEGACY_ENABLED': 'true',
            'CADRISYN_LEGACY_SCHEDULER_ENABLED': 'true',
        }
        with patch.dict(os.environ, inherited):
            environment = development_environment()
        self.assertEqual(environment['DATABASE_URL'], '')
        self.assertEqual(environment['DJANGO_CACHE_URL'], '')
        self.assertEqual(Path(environment['CADRISYN_DB_PATH']), ROOT / '.local/cadrisyn.sqlite3')
        self.assertEqual(environment['DJANGO_SETTINGS_MODULE'], 'quantvision.settings')
        self.assertEqual(environment['CADRISYN_LEGACY_ENABLED'], 'false')
        self.assertEqual(environment['CADRISYN_LEGACY_SCHEDULER_ENABLED'], 'false')


if __name__ == '__main__':
    unittest.main()
