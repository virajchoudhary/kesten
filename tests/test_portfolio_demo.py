import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import demo


class PortfolioDemoTests(unittest.TestCase):
    def setUp(self):
        (demo.ROOT / ".local").mkdir(exist_ok=True)

    def test_test_workspace_is_created_for_a_clean_checkout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(demo, "ROOT", root):
                self.setUp()
            self.assertTrue((root / ".local").is_dir())

    def test_demo_environment_isolated_from_inherited_production_and_market_settings(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / ".local/demo"
            inherited = {
                "DATABASE_URL": "postgresql://shared.invalid/user-data",
                "DJANGO_SECRET_KEY_FILE": "/private/key",
                "DATABASE_URL_FILE": "/private/database",
                "DJANGO_CACHE_URL_FILE": "/private/cache",
                "CADRISYN_MARKET_DATA_ENABLED": "true",
                "CADRISYN_LEGACY_ENABLED": "true",
                "CADRISYN_WEB_RELEASE_PROFILE": "demo",
            }
            with patch.object(demo, "ROOT", root), patch.dict(os.environ, inherited):
                environment = demo.demo_environment(directory, api_port=8123, web_port=3123)
                original_secret = (directory / "django-secret").read_bytes()
                repeated = demo.demo_environment(directory, api_port=8123, web_port=3123)
            self.assertEqual(environment["CADRISYN_DB_PATH"], str(directory / "workspace.sqlite3"))
            self.assertEqual(environment["DATABASE_URL"], "")
            self.assertEqual(environment["CADRISYN_MARKET_DATA_ENABLED"], "false")
            self.assertEqual(environment["CADRISYN_YAHOO_PERSONAL_USE_ACKNOWLEDGED"], "false")
            self.assertEqual(environment["CADRISYN_RELEASE_PROFILE"], "development")
            self.assertEqual(environment["CADRISYN_WEB_RELEASE_PROFILE"], "development")
            self.assertEqual(environment["DJANGO_API_URL"], "http://127.0.0.1:8123")
            self.assertIn("http://127.0.0.1:3123", environment["DJANGO_CSRF_TRUSTED_ORIGINS"])
            self.assertEqual(environment["DJANGO_SECRET_KEY"], repeated["DJANGO_SECRET_KEY"])
            self.assertEqual((directory / "django-secret").read_bytes(), original_secret)
            for name in ("DJANGO_SECRET_KEY_FILE", "DATABASE_URL_FILE", "DJANGO_CACHE_URL_FILE"):
                self.assertNotIn(name, environment)

    def test_refuses_unrelated_or_unmarked_directories_without_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(demo, "ROOT", root):
                for directory in (root, root / ".local", root / "elsewhere"):
                    with self.assertRaises(ValueError):
                        demo.demo_environment(directory)
                directory = root / ".local/existing"
                directory.mkdir(parents=True)
                protected = directory / "keep.txt"
                protected.write_bytes(b"existing user work")
                with self.assertRaises(ValueError):
                    demo.demo_environment(directory)
                self.assertEqual(protected.read_bytes(), b"existing user work")
                self.assertEqual(list(directory.iterdir()), [protected])

    def test_occupied_port_is_not_reused(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            with self.assertRaises(OSError):
                demo.require_free_ports(listener.getsockname()[1])

    def test_real_bootstrap_and_restart_preserve_accounts_and_saved_results(self):
        with tempfile.TemporaryDirectory(dir=demo.ROOT / ".local", prefix="demo-check-") as temporary:
            directory = Path(temporary) / "workspace"
            command = [sys.executable, "-B", str(demo.ROOT / "scripts/demo.py"), "--directory", str(directory), "--prepare-only"]
            subprocess.run(command, cwd=demo.ROOT, check=True, capture_output=True)
            credentials = (directory / "credentials.json").read_bytes()
            environment = demo.demo_environment(directory)
            probe = (
                "import django,json; django.setup(); "
                "from django.contrib.auth import get_user_model; "
                "from research.models import ResearchDataset,ResearchRun; "
                "from workspace.models import WatchlistEntry; "
                "print(json.dumps({'users':get_user_model().objects.count(),"
                "'datasets':list(ResearchDataset.objects.values_list('id','version')),"
                "'runs':list(ResearchRun.objects.order_by('horizon_sessions').values_list('id','result')),"
                "'watchlist':list(WatchlistEntry.objects.values_list('instrument_id',flat=True))},default=str))"
            )
            before = subprocess.run([sys.executable, "-B", "-c", probe], cwd=demo.ROOT / "backend", env=environment, check=True, capture_output=True, text=True)
            subprocess.run(command, cwd=demo.ROOT, check=True, capture_output=True)
            after = subprocess.run([sys.executable, "-B", "-c", probe], cwd=demo.ROOT / "backend", env=environment, check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(before.stdout), json.loads(after.stdout))
            state = json.loads(after.stdout)
            self.assertEqual(state["users"], 1)
            self.assertEqual(len(state["datasets"]), 1)
            self.assertEqual(len(state["runs"]), 2)
            self.assertEqual(len(state["watchlist"]), 3)
            self.assertEqual((directory / "credentials.json").read_bytes(), credentials)
            remove = "import django; django.setup(); from workspace.models import WatchlistEntry; WatchlistEntry.objects.filter(instrument_id='xnas-msft').delete()"
            subprocess.run([sys.executable, "-B", "-c", remove], cwd=demo.ROOT / "backend", env=environment, check=True, capture_output=True)
            subprocess.run(command, cwd=demo.ROOT, check=True, capture_output=True)
            after_remove = subprocess.run([sys.executable, "-B", "-c", probe], cwd=demo.ROOT / "backend", env=environment, check=True, capture_output=True, text=True)
            self.assertNotIn("xnas-msft", json.loads(after_remove.stdout)["watchlist"])
            change_password = (
                "import django; django.setup(); from django.contrib.auth import get_user_model; "
                "user=get_user_model().objects.get(username='analyst'); "
                "user.set_password('changed-only-in-test'); user.save(update_fields=['password'])"
            )
            subprocess.run([sys.executable, "-B", "-c", change_password], cwd=demo.ROOT / "backend", env=environment, check=True, capture_output=True)
            restarted = subprocess.run(command, cwd=demo.ROOT, capture_output=True, text=True)
            self.assertEqual(restarted.returncode, 0, restarted.stderr)
            self.assertIn("Use your current password", restarted.stdout)
            verify_password = (
                "import django; django.setup(); from django.contrib.auth import get_user_model; "
                "user=get_user_model().objects.get(username='analyst'); "
                "assert user.check_password('changed-only-in-test')"
            )
            subprocess.run([sys.executable, "-B", "-c", verify_password], cwd=demo.ROOT / "backend", env=environment, check=True, capture_output=True)
            self.assertEqual((directory / "credentials.json").read_bytes(), credentials)
            after_password = subprocess.run([sys.executable, "-B", "-c", probe], cwd=demo.ROOT / "backend", env=environment, check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(after_remove.stdout), json.loads(after_password.stdout))

    def test_browser_fixtures_are_explicit_and_never_overwrite_one_use_secrets(self):
        with tempfile.TemporaryDirectory(dir=demo.ROOT / ".local", prefix="demo-browser-check-") as temporary:
            directory = Path(temporary) / "workspace"
            command = [
                sys.executable, "-B", str(demo.ROOT / "scripts/demo.py"), "--directory", str(directory),
                "--prepare-only", "--browser-fixtures",
            ]
            subprocess.run(command, cwd=demo.ROOT, check=True, capture_output=True)
            names = ("credentials.json", "account-e2e-invitation.txt", "account-e2e-reset.json", "research-e2e-isolation.json")
            originals = {name: (directory / name).read_bytes() for name in names}
            refused = subprocess.run(command, cwd=demo.ROOT, capture_output=True)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn(b"Browser fixtures already exist", refused.stderr)
            self.assertEqual(originals, {name: (directory / name).read_bytes() for name in names})


if __name__ == "__main__":
    unittest.main()
