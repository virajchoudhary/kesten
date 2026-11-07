import hashlib
import io
import json
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing, redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.ops import recovery


ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = (
    "postgresql://operator%40desk:p%3Ass%5C%40%2B@localhost:5432/"
    "cadrisyn?sslmode=require&connect_timeout=9&application_name=recovery+test"
)
TARGET_URL = (
    "postgresql://restore:target%40secret@localhost:5432/"
    "cadrisyn-restore?sslmode=verify-full"
)
TOC_LISTING = (
    "; Archive created at 2026-11-06 00:00:00 UTC\n"
    ";     Format: CUSTOM\n"
    "; Selected TOC Entries:\n"
    "1; 1259 16384 TABLE public watchlist cadrisyn\n"
    "2; 1259 16385 TABLE DATA public watchlist cadrisyn\n"
)
SOURCE_IDENTITY = {
    "database_oid": 16384,
    "server_version_num": 170011,
    "user_schema_count": 1,
    "user_object_count": 14,
    "django_migrations_present": True,
    "system_identifier": "7430123456789012345",
}
EMPTY_TARGET_IDENTITY = {
    "database_oid": 16385,
    "server_version_num": 170011,
    "user_schema_count": 0,
    "user_object_count": 0,
    "django_migrations_present": False,
    "system_identifier": "7430123456789012345",
}


class RecoveryTests(unittest.TestCase):
    def test_sqlite_final_path_is_absent_until_validation_completes(self):
        source = self.temp / "source.sqlite3"
        with closing(sqlite3.connect(source)) as db:
            db.execute("CREATE TABLE retained (value TEXT)")
            db.execute("INSERT INTO retained VALUES ('preserved')")
            db.commit()
        _, manifest = recovery.backup_sqlite(source, self.temp / "backup.sqlite3")
        target = self.temp / "restored.sqlite3"
        metadata = recovery._sqlite_metadata
        inspections = 0

        def fail_restored_validation(connection):
            nonlocal inspections
            inspections += 1
            self.assertFalse(target.exists())
            if inspections == 2:
                raise recovery.RecoveryError("Simulated validation failure")
            return metadata(connection)

        with patch.object(recovery, "_sqlite_metadata", side_effect=fail_restored_validation):
            with self.assertRaisesRegex(recovery.RecoveryError, "Simulated validation"):
                recovery.restore_sqlite(manifest, target)
        self.assertFalse(target.exists())
        self.assertEqual(list(self.temp.glob("*.partial")), [])

    def test_sqlite_publish_cannot_overwrite_a_concurrently_created_target(self):
        source = self.temp / "source.sqlite3"
        with closing(sqlite3.connect(source)) as db:
            db.execute("CREATE TABLE retained (value TEXT)")
        _, manifest = recovery.backup_sqlite(source, self.temp / "backup.sqlite3")
        target = self.temp / "restored.sqlite3"
        publication_method = "rename" if os.name == "nt" else "link"
        publish = getattr(os, publication_method)

        def concurrent_publish(temporary, final):
            target.write_bytes(b"another operator's file")
            publish(temporary, final)

        with patch.object(recovery.os, publication_method, side_effect=concurrent_publish):
            with self.assertRaises(recovery.RecoveryError):
                recovery.restore_sqlite(manifest, target)
        self.assertEqual(target.read_bytes(), b"another operator's file")

    def setUp(self):
        (ROOT / ".local").mkdir(exist_ok=True)
        self.temporary_directory = tempfile.TemporaryDirectory(dir=ROOT / ".local")
        self.addCleanup(self.temporary_directory.cleanup)
        self.temp = Path(self.temporary_directory.name)
        self.calls = []
        self.pgpass_paths = []
        self.pgpass_records = []
        self.target_identity = EMPTY_TARGET_IDENTITY

    def test_postgres_url_decodes_userinfo_and_preserves_supported_options(self):
        parsed = recovery.parse_postgres_url(SOURCE_URL)

        self.assertEqual(parsed.username, "operator@desk")
        self.assertEqual(parsed.password, "p:ss\\@+")
        self.assertEqual(parsed.database, "cadrisyn")
        self.assertEqual(parsed.host, "localhost")
        self.assertEqual(parsed.port, 5432)
        self.assertEqual(parsed.sslmode, "require")
        self.assertEqual(parsed.connect_timeout, 9)
        self.assertEqual(parsed.application_name, "recovery test")
        self.assertNotIn(parsed.password, repr(parsed))
        self.assertEqual(recovery._escape_pgpass(parsed.password), "p\\:ss\\\\@+")

    def test_postgres_url_rejects_ambiguous_or_unsupported_options(self):
        with self.assertRaisesRegex(recovery.RecoveryError, "percent escape"):
            recovery.parse_postgres_url("postgresql://user:bad%zz@host/db")
        with self.assertRaisesRegex(recovery.RecoveryError, "repeats"):
            recovery.parse_postgres_url(
                "postgresql://user:pass@host/db?sslmode=require&sslmode=prefer"
            )
        with self.assertRaisesRegex(recovery.RecoveryError, "Unsupported"):
            recovery.parse_postgres_url(
                "postgresql://user:pass@host/db?options=-cunsafe"
            )

    def test_verified_tls_ca_is_passed_explicitly_without_inherited_pg_settings(self):
        from urllib.parse import quote

        certificate = self.temp / 'private-ca.crt'
        certificate.write_text('local test CA')
        parsed = recovery.parse_postgres_url(TARGET_URL + '&sslrootcert=' + quote(str(certificate)))
        with patch.dict(os.environ, {'PGSSLROOTCERT': 'unrelated-ca', 'PGSSLMODE': 'disable'}):
            with recovery._postgres_environment(parsed) as environment:
                self.assertEqual(environment['PGSSLROOTCERT'], str(certificate))
                self.assertEqual(environment['PGSSLMODE'], 'verify-full')
        with self.assertRaisesRegex(recovery.RecoveryError, 'CA certificate'):
            recovery.parse_postgres_url(TARGET_URL + '&sslrootcert=missing-ca-file')

    def test_cli_rejects_url_argument_without_echoing_it(self):
        standard_error = io.StringIO()

        with redirect_stderr(standard_error):
            with self.assertRaises(SystemExit):
                recovery.main(
                    [
                        "backup-postgres",
                        "--database-url",
                        SOURCE_URL,
                        "--output",
                        str(self.temp / "unused.dump"),
                    ]
                )

        self.assertNotIn(SOURCE_URL, standard_error.getvalue())
        self.assertNotIn(
            recovery.parse_postgres_url(SOURCE_URL).password,
            standard_error.getvalue(),
        )

    def test_sqlite_backup_and_restore_round_trip_without_changing_source(self):
        source = self.temp / "source.sqlite3"
        backup = self.temp / "backup.sqlite3"
        restored = self.temp / "restored.sqlite3"
        database = self._connect(source)
        database.execute("PRAGMA user_version = 7")
        database.execute(
            "CREATE TABLE notes (id INTEGER PRIMARY KEY, body TEXT NOT NULL)"
        )
        database.execute(
            "INSERT INTO notes (body) VALUES (?)",
            ("preserved research",),
        )
        database.commit()
        source_hash_before = hashlib.sha256(source.read_bytes()).hexdigest()

        artifact, manifest_path = recovery.backup_sqlite(source, backup)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        target = recovery.restore_sqlite(manifest_path, restored)

        self.assertEqual(artifact, backup.resolve())
        self.assertEqual(target, restored.resolve())
        self.assertEqual(
            manifest["artifact"]["sha256"],
            hashlib.sha256(backup.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            hashlib.sha256(source.read_bytes()).hexdigest(),
            source_hash_before,
        )
        restored_database = self._connect(restored)
        self.assertEqual(
            restored_database.execute("SELECT body FROM notes").fetchone(),
            ("preserved research",),
        )
        self.assertEqual(
            restored_database.execute("PRAGMA user_version").fetchone(),
            (7,),
        )

    def test_backup_paths_are_exclusive_and_existing_files_remain_unchanged(self):
        source = self.temp / "source.sqlite3"
        backup = self.temp / "backup.sqlite3"
        database = self._connect(source)
        database.execute("CREATE TABLE values_table (value INTEGER)")
        database.execute("INSERT INTO values_table VALUES (12)")
        database.commit()
        recovery.backup_sqlite(source, backup)
        before = backup.read_bytes()

        with self.assertRaisesRegex(recovery.RecoveryError, "already exists"):
            recovery.backup_sqlite(source, backup)

        self.assertEqual(backup.read_bytes(), before)

    def test_sqlite_restore_refuses_existing_and_preserved_database_targets(self):
        source = self.temp / "source.sqlite3"
        backup = self.temp / "backup.sqlite3"
        existing = self.temp / "existing.sqlite3"
        database = self._connect(source)
        database.execute("CREATE TABLE values_table (value INTEGER)")
        database.commit()
        _, manifest_path = recovery.backup_sqlite(source, backup)
        existing_database = self._connect(existing)
        existing_database.execute("CREATE TABLE keep_me (value TEXT)")
        existing_database.execute("INSERT INTO keep_me VALUES ('untouched')")
        existing_database.commit()
        existing_hash_before = hashlib.sha256(existing.read_bytes()).hexdigest()

        with self.assertRaisesRegex(recovery.RecoveryError, "new, unused path"):
            recovery.restore_sqlite(manifest_path, existing)
        with self.assertRaisesRegex(recovery.RecoveryError, "preserved"):
            recovery.restore_sqlite(
                manifest_path,
                ROOT / "backend" / "db.sqlite3",
            )

        self.assertEqual(
            hashlib.sha256(existing.read_bytes()).hexdigest(),
            existing_hash_before,
        )

    def test_sqlite_restore_refuses_backup_artifact_as_target(self):
        source = self.temp / "source.sqlite3"
        backup = self.temp / "backup.sqlite3"
        database = self._connect(source)
        database.execute("CREATE TABLE values_table (value INTEGER)")
        database.commit()
        _, manifest_path = recovery.backup_sqlite(source, backup)

        with self.assertRaisesRegex(recovery.RecoveryError, "backup artifact"):
            recovery.restore_sqlite(manifest_path, backup)

    def test_sqlite_restore_rejects_tampered_backup_before_creating_target(self):
        source = self.temp / "source.sqlite3"
        backup = self.temp / "backup.sqlite3"
        target = self.temp / "restore.sqlite3"
        database = self._connect(source)
        database.execute("CREATE TABLE values_table (value INTEGER)")
        database.execute("INSERT INTO values_table VALUES (42)")
        database.commit()
        _, manifest_path = recovery.backup_sqlite(source, backup)
        corrupted = bytearray(backup.read_bytes())
        corrupted[-1] ^= 1
        backup.write_bytes(corrupted)

        with self.assertRaisesRegex(recovery.RecoveryError, "checksum"):
            recovery.restore_sqlite(manifest_path, target)

        self.assertFalse(target.exists())

    def test_postgres_backup_keeps_password_out_of_arguments_and_output(self):
        output = self.temp / "postgres.dump"
        password = recovery.parse_postgres_url(SOURCE_URL).password
        fake = self._postgres_runner()
        standard_output = io.StringIO()

        with (
            patch.dict(
                os.environ,
                {
                    "CADRISYN_SOURCE_DATABASE_URL": SOURCE_URL,
                    "PRIVATE_CONNECTION": SOURCE_URL,
                    "DATABASE_URL": SOURCE_URL,
                    "POSTGRES_PASSWORD": password,
                    "PGPASSWORD": password,
                },
                clear=False,
            ),
            patch.object(recovery.subprocess, "run", side_effect=fake),
            redirect_stdout(standard_output),
        ):
            result = recovery.main(
                [
                    "backup-postgres",
                    "--database-url-env",
                    "CADRISYN_SOURCE_DATABASE_URL",
                    "--output",
                    str(output),
                ]
            )

        self.assertEqual(result, 0)
        self.assertTrue(output.is_file())
        self.assertTrue(Path(f"{output}.manifest.json").is_file())
        self.assertNotIn(password, standard_output.getvalue())
        self.assertGreaterEqual(len(self.calls), 3)
        for arguments, child_environment in self.calls:
            flattened = " ".join(arguments)
            self.assertNotIn(password, flattened)
            self.assertNotIn(SOURCE_URL, flattened)
            self.assertNotIn("--password", flattened)
            self.assertNotIn("PGPASSWORD", child_environment)
            self.assertNotIn("DATABASE_URL", child_environment)
            self.assertNotIn("CADRISYN_SOURCE_DATABASE_URL", child_environment)
            self.assertNotIn("PRIVATE_CONNECTION", child_environment)
        self.assertTrue(self.pgpass_paths)
        self.assertTrue(all(not path.exists() for path in self.pgpass_paths))

    def test_pgpass_is_restricted_and_supported_url_settings_reach_clients(self):
        output = self.temp / "postgres.dump"
        parsed = recovery.parse_postgres_url(SOURCE_URL)
        password = parsed.password
        fake = self._postgres_runner()

        with (
            patch.dict(
                os.environ,
                {"CADRISYN_SOURCE_DATABASE_URL": SOURCE_URL},
                clear=False,
            ),
            patch.object(recovery.subprocess, "run", side_effect=fake),
        ):
            recovery.backup_postgres(SOURCE_URL, output)

        self.assertTrue(self.pgpass_records)
        for contents, file_mode, child_environment in self.pgpass_records:
            self.assertIn(recovery._escape_pgpass(password), contents)
            self.assertEqual(child_environment["PGSSLMODE"], "require")
            self.assertEqual(child_environment["PGCONNECT_TIMEOUT"], "9")
            self.assertEqual(child_environment["PGAPPNAME"], "recovery test")
            if os.name == "posix":
                self.assertEqual(file_mode, 0o600)
        self.assertTrue(all(not path.exists() for path in self.pgpass_paths))

    def test_postgres_restore_rejects_same_source_without_running_restore(self):
        _, manifest_path = self._create_postgres_backup()
        fake = self._postgres_runner()

        with patch.object(recovery.subprocess, "run", side_effect=fake):
            with self.assertRaisesRegex(recovery.RecoveryError, "same PostgreSQL endpoint"):
                recovery.restore_postgres(manifest_path, SOURCE_URL)

        self.assertFalse(any("pg_restore" in call[0][0] and "--single-transaction" in call[0] for call in self.calls))

    def test_postgres_restore_rejects_nonempty_target_before_writes(self):
        _, manifest_path = self._create_postgres_backup()
        self.calls.clear()
        self.target_identity = {
            **EMPTY_TARGET_IDENTITY,
            "database_oid": 16386,
            "user_object_count": 1,
        }
        fake = self._postgres_runner()

        with patch.object(recovery.subprocess, "run", side_effect=fake):
            with self.assertRaisesRegex(recovery.RecoveryError, "not empty"):
                recovery.restore_postgres(manifest_path, TARGET_URL)

        self.assertFalse(
            any(
                arguments[0] == "pg_restore" and "--single-transaction" in arguments
                for arguments, _ in self.calls
            )
        )

    def test_postgres_restore_validates_hash_before_starting_clients(self):
        _, manifest_path = self._create_postgres_backup()
        self.calls.clear()
        artifact = self.temp / "postgres.dump"
        artifact.write_bytes(artifact.read_bytes() + b"tampered")
        fake = self._postgres_runner()

        with patch.object(recovery.subprocess, "run", side_effect=fake):
            with self.assertRaisesRegex(recovery.RecoveryError, "does not match"):
                recovery.restore_postgres(manifest_path, TARGET_URL)

        self.assertEqual(self.calls, [])

    def test_postgres_restore_uses_single_transaction_without_clean_or_create(self):
        _, manifest_path = self._create_postgres_backup()
        self.calls.clear()
        fake = self._postgres_runner()

        with patch.object(recovery.subprocess, "run", side_effect=fake):
            recovery.restore_postgres(manifest_path, TARGET_URL)

        restore_calls = [
            arguments
            for arguments, _ in self.calls
            if arguments[0] == "pg_restore" and "--single-transaction" in arguments
        ]
        self.assertEqual(len(restore_calls), 1)
        command = restore_calls[0]
        self.assertIn("--exit-on-error", command)
        self.assertNotIn("--clean", command)
        self.assertNotIn("--create", command)
        self.assertFalse(any(argument.startswith("--jobs") for argument in command))
        self.assertNotIn(recovery.parse_postgres_url(TARGET_URL).password, " ".join(command))

    def test_postgres_client_failures_redact_secrets_and_remove_partial_backups(self):
        output = self.temp / "failed.dump"
        password = recovery.parse_postgres_url(SOURCE_URL).password

        def fail_dump(arguments, env=None, **kwargs):
            self.calls.append((arguments, dict(env or {})))
            if arguments[0] == "psql":
                return SimpleNamespace(
                    returncode=0,
                    stdout=json.dumps(SOURCE_IDENTITY),
                    stderr="",
                )
            if arguments[0] == "pg_dump":
                raise recovery.subprocess.CalledProcessError(
                    1,
                    arguments,
                    stderr=f"failed DSN {SOURCE_URL}; password={password}",
                )
            self.fail("Unexpected PostgreSQL command in failure test.")

        with patch.object(recovery.subprocess, "run", side_effect=fail_dump):
            with self.assertRaises(recovery.RecoveryError) as captured:
                recovery.backup_postgres(SOURCE_URL, output)

        self.assertNotIn(SOURCE_URL, str(captured.exception))
        self.assertNotIn(password, str(captured.exception))
        self.assertFalse(output.exists())
        self.assertFalse(Path(f"{output}.manifest.json").exists())
        self.assertTrue(all(not path.exists() for path in self.pgpass_paths))

    def _create_postgres_backup(self):
        output = self.temp / "postgres.dump"
        fake = self._postgres_runner()
        with patch.object(recovery.subprocess, "run", side_effect=fake):
            return recovery.backup_postgres(SOURCE_URL, output)

    def _connect(self, path):
        database = sqlite3.connect(path)
        self.addCleanup(database.close)
        return database

    def _postgres_runner(self):
        def run(arguments, env=None, capture_output=False, text=False, check=False):
            self.calls.append((arguments, dict(env or {})))
            if env and env.get("PGPASSFILE"):
                pgpass_path = Path(env["PGPASSFILE"])
                self.pgpass_paths.append(pgpass_path)
                self.assertTrue(pgpass_path.is_file())
                self.pgpass_records.append(
                    (
                        pgpass_path.read_text(encoding="utf-8"),
                        pgpass_path.stat().st_mode & 0o777,
                        dict(env),
                    )
                )

            executable = Path(arguments[0]).name
            if executable == "psql":
                database_name = next(
                    argument.removeprefix("--dbname=")
                    for argument in arguments
                    if argument.startswith("--dbname=")
                )
                identity = (
                    self.target_identity
                    if database_name == "cadrisyn-restore"
                    else SOURCE_IDENTITY
                )
                return SimpleNamespace(
                    returncode=0,
                    stdout=json.dumps(identity),
                    stderr="",
                )
            if executable == "pg_dump":
                output_argument = next(
                    argument for argument in arguments if argument.startswith("--file=")
                )
                Path(output_argument.removeprefix("--file=")).write_bytes(
                    b"mock PostgreSQL custom-format archive"
                )
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            if executable == "pg_restore" and "--list" in arguments:
                return SimpleNamespace(
                    returncode=0,
                    stdout=TOC_LISTING,
                    stderr="",
                )
            if executable == "pg_restore":
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            self.fail(f"Unexpected PostgreSQL executable: {executable}")

        return run


if __name__ == "__main__":
    unittest.main()
