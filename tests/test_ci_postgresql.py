import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts import ci_postgresql


class PostgreSQLCIProcedureTests(unittest.TestCase):
    def run_procedure(self, root, *, startup_failure=False, partial_start=False):
        calls = []
        passwords = {}

        def run(arguments, **options):
            calls.append((arguments, options))
            if arguments[:2] == ["docker", "run"]:
                env_file = Path(arguments[arguments.index("--env-file") + 1])
                passwords.update(
                    line.split("=", 1) for line in env_file.read_text().splitlines()
                )
                if startup_failure:
                    if partial_start:
                        Path(arguments[arguments.index("--cidfile") + 1]).write_text("owned-container-id")
                    raise subprocess.CalledProcessError(1, arguments)
                Path(arguments[arguments.index("--cidfile") + 1]).write_text("owned-container-id")
            return subprocess.CompletedProcess(arguments, 0)

        (root / "deploy").mkdir()
        (root / "deploy/postgres-init.sh").write_text("restricted-role-init\n")
        with (
            patch.object(ci_postgresql, "ROOT", root),
            patch.object(ci_postgresql.subprocess, "run", side_effect=run),
            patch.object(ci_postgresql.subprocess, "check_output", return_value="127.0.0.1:35432\n"),
            patch.object(ci_postgresql.psycopg, "connect", return_value=MagicMock()),
            patch.dict(os.environ, {
                "DATABASE_URL": "postgresql://retained.invalid/personal",
                "CADRISYN_DB_PATH": "/retained/personal.sqlite3",
                "DJANGO_SECRET_KEY_FILE": "/retained/private-key",
            }),
        ):
            if startup_failure:
                with self.assertRaises(subprocess.CalledProcessError):
                    ci_postgresql.main()
            else:
                ci_postgresql.main()
        return calls, passwords

    def test_credentials_are_fresh_and_kept_out_of_commands_and_retained_configuration(self):
        runs = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                calls, passwords = self.run_procedure(root)
                self.assertEqual(list((root / ".local").iterdir()), [])
                runs.append(passwords)
                for name in ("POSTGRES_PASSWORD", "CADRISYN_DB_PASSWORD", "CADRISYN_MIGRATION_PASSWORD"):
                    self.assertEqual(len(passwords[name]), 48)
                    self.assertTrue(all(passwords[name] not in str(args) for args, _ in calls))
                container_run = calls[0][0]
                self.assertEqual(container_run[container_run.index("--publish") + 1], "127.0.0.1::5432")
                self.assertNotIn("--volume", container_run)
                self.assertIn("--rm", container_run)
                self.assertEqual(container_run[container_run.index("--tmpfs") + 1], "/var/lib/postgresql/data")
                manage = [options["env"] for args, options in calls if str(args[1]).endswith("manage.py")]
                self.assertEqual(len(manage), 4)
                for environment in manage:
                    self.assertNotIn("CADRISYN_DB_PATH", environment)
                    self.assertNotIn("DJANGO_SECRET_KEY_FILE", environment)
                    self.assertIn("@127.0.0.1:35432/", environment["DATABASE_URL"])
                    self.assertEqual(environment["CADRISYN_MARKET_DATA_ENABLED"], "false")
                    self.assertEqual(environment["CADRISYN_LEGACY_ENABLED"], "false")
                self.assertEqual(calls[-1][0][:2], ["docker", "stop"])
                self.assertEqual(calls[-1][0][2], "owned-container-id")
        self.assertNotEqual(runs[0]["POSTGRES_PASSWORD"], runs[1]["POSTGRES_PASSWORD"])

    def test_container_startup_failure_does_not_run_migrations_or_stop_unowned_containers(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            calls, _ = self.run_procedure(root, startup_failure=True)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][0][:2], ["docker", "run"])
            self.assertEqual(list((root / ".local").iterdir()), [])

    def test_partial_start_failure_stops_only_the_recorded_container(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            calls, _ = self.run_procedure(root, startup_failure=True, partial_start=True)
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[-1][0], ["docker", "stop", "owned-container-id"])
            self.assertEqual(list((root / ".local").iterdir()), [])

    def test_exited_container_reports_startup_failure_without_cleanup_masking(self):
        for cleanup_error in ("No such container: owned-container-id", "daemon unavailable"):
            with self.subTest(cleanup_error=cleanup_error), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                calls = []

                def run(arguments, **options):
                    calls.append(arguments)
                    if arguments[:2] == ["docker", "run"]:
                        Path(arguments[arguments.index("--cidfile") + 1]).write_text("owned-container-id")
                        return subprocess.CompletedProcess(arguments, 0)
                    if arguments[:2] == ["docker", "stop"]:
                        result = subprocess.CompletedProcess(arguments, 1, "", cleanup_error)
                    elif arguments[:2] == ["docker", "inspect"]:
                        result = subprocess.CompletedProcess(arguments, 1, "", "No such container")
                    else:
                        result = subprocess.CompletedProcess(arguments, 1)
                    if options.get("check"):
                        result.check_returncode()
                    return result

                with (
                    patch.object(ci_postgresql, "ROOT", root),
                    patch.object(ci_postgresql.subprocess, "run", side_effect=run),
                    patch.object(ci_postgresql.subprocess, "check_output", return_value="127.0.0.1:35432\n"),
                    patch.object(ci_postgresql.time, "monotonic", side_effect=[0, 181]),
                    patch.object(ci_postgresql.time, "sleep") as sleep,
                ):
                    with self.assertRaisesRegex(RuntimeError, "exited before readiness"):
                        ci_postgresql.main()
                sleep.assert_not_called()
                self.assertEqual(calls[-1], ["docker", "stop", "owned-container-id"])
                self.assertFalse(any(str(argument).endswith("manage.py") for call in calls for argument in call))
                self.assertEqual(list((root / ".local").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
