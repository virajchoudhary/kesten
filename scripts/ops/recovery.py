"""Explicit, non-destructive database backup and restore commands."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from urllib.parse import parse_qsl, unquote, urlsplit


MANIFEST_VERSION = 1
_ROOT = Path(__file__).resolve().parents[2]
_PRESERVED_SQLITE = (_ROOT / "backend" / "db.sqlite3").resolve()
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_SAFE_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SSL_MODES = {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}
_URL_OPTIONS = {"sslmode", "connect_timeout", "application_name"}
_METADATA_SQL = """
WITH app_namespaces AS (
  SELECT oid, nspname FROM pg_namespace
  WHERE nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
    AND nspname !~ '^pg_temp_[0-9]+$' AND nspname !~ '^pg_toast_temp_[0-9]+$'
)
SELECT json_build_object(
  'database_oid', (SELECT oid::bigint FROM pg_database WHERE datname = current_database()),
  'server_version_num', current_setting('server_version_num')::integer,
  'user_schema_count', (SELECT count(*) FROM app_namespaces WHERE nspname <> 'public'),
  'user_object_count',
    (SELECT count(*) FROM pg_class c JOIN app_namespaces n ON n.oid = c.relnamespace)
    + (SELECT count(*) FROM pg_proc p JOIN app_namespaces n ON n.oid = p.pronamespace)
    + (SELECT count(*) FROM pg_type t JOIN app_namespaces n ON n.oid = t.typnamespace)
    + (SELECT count(*) FROM pg_operator o JOIN app_namespaces n ON n.oid = o.oprnamespace)
    + (SELECT count(*) FROM pg_statistic_ext s JOIN app_namespaces n ON n.oid = s.stxnamespace)
    + (SELECT count(*) FROM pg_extension e JOIN app_namespaces n ON n.oid = e.extnamespace),
  'django_migrations_present', to_regclass('public.django_migrations') IS NOT NULL,
  'system_identifier', CASE WHEN has_function_privilege(
    current_user, 'pg_catalog.pg_control_system()', 'EXECUTE'
  ) THEN (SELECT system_identifier::text FROM pg_catalog.pg_control_system()) ELSE NULL END
)::text;
"""


class RecoveryError(RuntimeError):
    """An operator-facing error that does not expose credentials."""


@dataclass(frozen=True, slots=True)
class PostgresConnection:
    host: str
    port: int
    username: str
    password: str = field(repr=False)
    database: str
    sslmode: str | None
    connect_timeout: int | None
    application_name: str | None

    @property
    def endpoint_fingerprint(self) -> str:
        value = [self.host.lower(), self.port, self.database]
        return _fingerprint(value)


def parse_postgres_url(value: str) -> PostgresConnection:
    """Parse a PostgreSQL URL without passing it to a child process."""
    if not isinstance(value, str) or not value.strip():
        raise RecoveryError("The PostgreSQL URL environment variable is empty.")
    value = value.strip()
    if re.search(r"%(?![0-9A-Fa-f]{2})", value):
        raise RecoveryError("The PostgreSQL URL contains an invalid percent escape.")

    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {"postgres", "postgresql"} or parsed.fragment:
            raise RecoveryError("The URL must be a PostgreSQL URL without a fragment.")
        host = unquote(parsed.hostname or "", errors="strict")
        port = parsed.port if parsed.port is not None else 5432
        username = unquote(parsed.username or "", errors="strict")
        password = unquote(parsed.password or "", errors="strict")
        database = unquote(parsed.path.lstrip("/"), errors="strict")
        query = parse_qsl(
            parsed.query,
            keep_blank_values=True,
            strict_parsing=True,
            errors="strict",
        )
    except RecoveryError:
        raise
    except (ValueError, UnicodeError) as error:
        raise RecoveryError("The PostgreSQL URL is not valid.") from error

    if not host or not username or not database:
        raise RecoveryError("The PostgreSQL URL must include host, username, and database.")
    if not 1 <= port <= 65535:
        raise RecoveryError("The PostgreSQL URL port must be between 1 and 65535.")

    options: dict[str, str] = {}
    for name, setting in query:
        if name not in _URL_OPTIONS:
            raise RecoveryError("Unsupported PostgreSQL URL option.")
        if name in options:
            raise RecoveryError("The PostgreSQL URL repeats an option.")
        options[name] = setting

    sslmode = options.get("sslmode")
    if sslmode is not None and sslmode not in _SSL_MODES:
        raise RecoveryError("The PostgreSQL URL has an unsupported sslmode.")
    try:
        timeout = int(options["connect_timeout"]) if "connect_timeout" in options else None
    except ValueError as error:
        raise RecoveryError("connect_timeout must be a positive integer.") from error
    if timeout is not None and not 1 <= timeout <= 600:
        raise RecoveryError("connect_timeout must be between 1 and 600 seconds.")

    application_name = options.get("application_name")
    for item in (host, username, password, database, application_name or ""):
        if any(ord(char) < 32 or ord(char) == 127 for char in item):
            raise RecoveryError("PostgreSQL URL components cannot contain control characters.")
    return PostgresConnection(
        host,
        port,
        username,
        password,
        database,
        sslmode,
        timeout,
        application_name,
    )


def backup_postgres(database_url: str, output_path: Path) -> tuple[Path, Path]:
    connection = parse_postgres_url(database_url)
    artifact, manifest = _reserve_backup_files(output_path)
    try:
        with _postgres_environment(connection) as environment:
            source = _postgres_metadata(connection, environment)
            _run_postgres(
                [
                    "pg_dump",
                    "--format=custom",
                    "--no-owner",
                    "--no-privileges",
                    "--no-password",
                    *_pg_arguments(connection),
                    f"--file={artifact}",
                ],
                environment,
            )
            _restrict_mode(artifact)
            archive = _inspect_dump(artifact, environment)

        schema = {
            "server_version_num": source["server_version_num"],
            "user_schema_count": source["user_schema_count"],
            "user_object_count": source["user_object_count"],
            "django_migrations_present": source["django_migrations_present"],
            **archive,
        }
        data = {
            "manifest_version": MANIFEST_VERSION,
            "backup_type": "postgresql_custom",
            "created_at": _utc_now(),
            "artifact": _artifact_info(artifact),
            "source": {
                "engine": "postgresql",
                "endpoint_fingerprint": connection.endpoint_fingerprint,
                "cluster_database_fingerprint": _cluster_fingerprint(source),
            },
            "schema_metadata": schema,
        }
        _write_manifest(manifest, data)
        return artifact, manifest
    except BaseException:
        _remove_created((artifact, manifest))
        raise


def backup_sqlite(source_path: Path, output_path: Path) -> tuple[Path, Path]:
    source = _existing_file(source_path, "SQLite source")
    artifact, manifest = _reserve_backup_files(output_path)
    try:
        with _sqlite_readonly(source) as source_db:
            destination = sqlite3.connect(artifact)
            try:
                source_db.backup(destination, pages=256, sleep=0.01)
            finally:
                destination.close()

        _restrict_mode(artifact)
        with _sqlite_readonly(artifact) as backup_db:
            schema = _sqlite_metadata(backup_db)
        data = {
            "manifest_version": MANIFEST_VERSION,
            "backup_type": "sqlite_database",
            "created_at": _utc_now(),
            "artifact": _artifact_info(artifact),
            "source": {"engine": "sqlite"},
            "schema_metadata": schema,
        }
        _write_manifest(manifest, data)
        return artifact, manifest
    except BaseException:
        _remove_created((artifact, manifest))
        raise


def restore_postgres(manifest_path: Path, target_database_url: str) -> Path:
    data, artifact = _load_manifest(manifest_path, "postgresql_custom")
    target = parse_postgres_url(target_database_url)
    source = data["source"]
    schema = data["schema_metadata"]
    if target.endpoint_fingerprint == source["endpoint_fingerprint"]:
        raise RecoveryError("Restore target is the same PostgreSQL endpoint as the source.")

    with _postgres_environment(target) as environment:
        archive = _inspect_dump(artifact, environment)
        if archive != {key: schema[key] for key in ("toc_entries", "toc_sha256")}:
            raise RecoveryError("PostgreSQL archive listing does not match its manifest.")
        current = _postgres_metadata(target, environment)
        source_cluster = source.get("cluster_database_fingerprint")
        if source_cluster and source_cluster == _cluster_fingerprint(current):
            raise RecoveryError("Restore target is the same PostgreSQL database as the source.")
        if current["user_schema_count"] or current["user_object_count"]:
            raise RecoveryError("Restore target is not empty; no objects were changed.")

        _run_postgres(
            [
                "pg_restore",
                "--single-transaction",
                "--exit-on-error",
                "--no-owner",
                "--no-privileges",
                "--no-password",
                *_pg_arguments(target),
                str(artifact),
            ],
            environment,
        )
    return artifact


def restore_sqlite(manifest_path: Path, target_path: Path) -> Path:
    data, artifact = _load_manifest(manifest_path, "sqlite_database")
    target = _new_path(target_path, "SQLite restore target")
    manifest = _existing_file(manifest_path, "recovery manifest")
    if target == _PRESERVED_SQLITE:
        raise RecoveryError("The preserved backend/db.sqlite3 is never a restore target.")
    if target in {artifact, manifest}:
        raise RecoveryError("Restore target cannot be the backup artifact or manifest.")
    if target.exists():
        raise RecoveryError("SQLite restore target must be a new, unused path.")

    with _sqlite_readonly(artifact) as backup_db:
        if _sqlite_metadata(backup_db) != data["schema_metadata"]:
            raise RecoveryError("SQLite schema metadata does not match the manifest.")

    descriptor, filename = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".partial", dir=target.parent)
    os.close(descriptor)
    temporary = Path(filename)
    try:
        with _sqlite_readonly(artifact) as source_db:
            destination = sqlite3.connect(temporary)
            try:
                source_db.backup(destination, pages=256, sleep=0.01)
            finally:
                destination.close()
        _restrict_mode(temporary)
        with _sqlite_readonly(temporary) as restored_db:
            if _sqlite_metadata(restored_db) != data["schema_metadata"]:
                raise RecoveryError("Restored SQLite schema does not match the manifest.")
        with temporary.open("r+b") as restored_file:
            os.fsync(restored_file.fileno())
        try:
            if os.name == "nt":
                os.rename(temporary, target)
            else:
                os.link(temporary, target)
        except FileExistsError as error:
            raise RecoveryError("SQLite restore target must be a new, unused path.") from error
        if os.name == "posix":
            directory_fd = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def _load_manifest(path: Path, expected_type: str) -> tuple[dict, Path]:
    manifest_path = _existing_file(path, "recovery manifest")
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RecoveryError("Could not read a valid recovery manifest.") from error

    if (
        not isinstance(data, dict)
        or type(data.get("manifest_version")) is not int
        or data["manifest_version"] != MANIFEST_VERSION
        or data.get("backup_type") != expected_type
    ):
        raise RecoveryError("Recovery manifest is invalid or has an unsupported type/version.")
    artifact_data = data.get("artifact")
    source = data.get("source")
    schema = data.get("schema_metadata")
    if any(not isinstance(value, dict) for value in (artifact_data, source, schema)):
        raise RecoveryError("Recovery manifest is missing required metadata.")

    filename = artifact_data.get("filename")
    digest = artifact_data.get("sha256")
    size = artifact_data.get("size_bytes")
    if (
        not isinstance(filename, str)
        or not filename
        or Path(filename).name != filename
        or "/" in filename
        or "\\" in filename
        or not isinstance(digest, str)
        or not _SHA256.fullmatch(digest)
        or type(size) is not int
        or size < 0
    ):
        raise RecoveryError("Recovery manifest artifact metadata is invalid.")

    artifact_path = manifest_path.parent / filename
    try:
        artifact = _existing_file(artifact_path, "backup artifact")
        if artifact.stat().st_size != size:
            raise RecoveryError("Backup artifact size does not match the manifest.")
        if _sha256(artifact).lower() != digest.lower():
            raise RecoveryError("Backup artifact checksum does not match the manifest.")
    except RecoveryError:
        raise
    except OSError as error:
        raise RecoveryError("Could not read the backup artifact.") from error

    if expected_type == "postgresql_custom":
        if (
            source.get("engine") != "postgresql"
            or not _is_sha256(source.get("endpoint_fingerprint"))
            or not _is_sha256(schema.get("toc_sha256"))
        ):
            raise RecoveryError("PostgreSQL manifest metadata is invalid.")
        _require_counts(
            schema,
            ("toc_entries", "server_version_num", "user_schema_count", "user_object_count"),
        )
        if not isinstance(schema.get("django_migrations_present"), bool):
            raise RecoveryError("PostgreSQL migration metadata is invalid.")
        cluster = source.get("cluster_database_fingerprint")
        if cluster is not None and not _is_sha256(cluster):
            raise RecoveryError("PostgreSQL cluster fingerprint is invalid.")
    else:
        if source.get("engine") != "sqlite" or not _is_sha256(schema.get("schema_sha256")):
            raise RecoveryError("SQLite manifest metadata is invalid.")
        _require_counts(schema, ("table_count", "user_version", "application_id", "page_count"))
    return data, artifact


def _require_counts(data: dict, keys: tuple[str, ...]) -> None:
    if any(type(data.get(key)) is not int or data[key] < 0 for key in keys):
        raise RecoveryError("Recovery schema metadata is invalid.")


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def _postgres_metadata(
    connection: PostgresConnection,
    environment: dict[str, str],
) -> dict:
    output = _run_postgres(
        [
            "psql",
            "-X",
            "-A",
            "-t",
            "-q",
            "-v",
            "ON_ERROR_STOP=1",
            "--no-password",
            *_pg_arguments(connection),
            "-c",
            _METADATA_SQL,
        ],
        environment,
    )
    try:
        metadata = json.loads(output.strip())
    except json.JSONDecodeError as error:
        raise RecoveryError("PostgreSQL returned invalid recovery metadata.") from error
    if not isinstance(metadata, dict):
        raise RecoveryError("PostgreSQL returned invalid recovery metadata.")
    _require_counts(
        metadata,
        ("database_oid", "server_version_num", "user_schema_count", "user_object_count"),
    )
    if not isinstance(metadata.get("django_migrations_present"), bool):
        raise RecoveryError("PostgreSQL returned incomplete migration metadata.")
    return metadata


@contextmanager
def _postgres_environment(connection: PostgresConnection) -> Iterator[dict[str, str]]:
    environment = os.environ.copy()
    private_names = {"POSTGRES_PASSWORD", "DATABASE_PASSWORD", "DB_PASSWORD"}
    for name in list(environment):
        upper = name.upper()
        is_postgres_url = environment[name].lstrip().lower().startswith(
            ("postgres://", "postgresql://")
        )
        if (
            upper.startswith("PG")
            or upper.endswith("DATABASE_URL")
            or upper in private_names
            or is_postgres_url
        ):
            environment.pop(name, None)
    for key, value in (
        ("PGSSLMODE", connection.sslmode),
        ("PGCONNECT_TIMEOUT", str(connection.connect_timeout) if connection.connect_timeout else None),
        ("PGAPPNAME", connection.application_name),
    ):
        if value is not None:
            environment[key] = value

    descriptor, filename = tempfile.mkstemp(prefix="cadrisyn-pgpass-")
    pgpass = Path(filename)
    try:
        os.chmod(pgpass, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            descriptor = -1
            if connection.password:
                values = (
                    connection.host,
                    str(connection.port),
                    connection.database,
                    connection.username,
                    connection.password,
                )
                stream.write(":".join(_escape_pgpass(value) for value in values) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as error:
        if descriptor >= 0:
            os.close(descriptor)
        pgpass.unlink(missing_ok=True)
        raise RecoveryError("Could not create a restricted PostgreSQL credential file.") from error

    environment["PGPASSFILE"] = str(pgpass)
    try:
        yield environment
    finally:
        pgpass.unlink(missing_ok=True)


def _run_postgres(command: list[str], environment: dict[str, str]) -> str:
    try:
        result = subprocess.run(
            command,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        raise RecoveryError("PostgreSQL client command failed.") from None
    if result.returncode:
        executable = Path(command[0]).name
        raise RecoveryError(
            f"PostgreSQL client {executable} failed with exit code {result.returncode}."
        )
    return str(result.stdout or "")


def _inspect_dump(artifact: Path, environment: dict[str, str]) -> dict[str, object]:
    listing = _run_postgres(["pg_restore", "--list", str(artifact)], environment)
    if not re.search(r"(?im)^\s*;\s*Format:\s*CUSTOM\s*$", listing):
        raise RecoveryError("PostgreSQL archive is not a readable custom-format dump.")
    entries = [
        line.rstrip()
        for line in listing.splitlines()
        if line.strip() and not line.lstrip().startswith(";")
    ]
    content = ("\n".join(entries) + ("\n" if entries else "")).encode("utf-8")
    return {"toc_entries": len(entries), "toc_sha256": hashlib.sha256(content).hexdigest()}


@contextmanager
def _sqlite_readonly(path: Path) -> Iterator[sqlite3.Connection]:
    source = _existing_file(path, "SQLite database")
    connection = None
    try:
        connection = sqlite3.connect(f"{source.as_uri()}?mode=ro", uri=True)
        connection.execute("PRAGMA query_only = ON")
    except sqlite3.Error as error:
        if connection is not None:
            connection.close()
        raise RecoveryError("Could not open the SQLite database read-only.") from error
    try:
        yield connection
    finally:
        connection.close()


def _sqlite_metadata(connection: sqlite3.Connection) -> dict[str, object]:
    try:
        if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise RecoveryError("SQLite integrity check failed.")
        schema = connection.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_schema "
            "WHERE substr(name, 1, 7) <> 'sqlite_' ORDER BY type, name, tbl_name"
        ).fetchall()
        user_version = connection.execute("PRAGMA user_version").fetchone()[0]
        application_id = connection.execute("PRAGMA application_id").fetchone()[0]
        page_count = connection.execute("PRAGMA page_count").fetchone()[0]
    except sqlite3.Error as error:
        raise RecoveryError("Could not inspect the SQLite schema.") from error
    encoded_schema = json.dumps(schema, ensure_ascii=False, separators=(",", ":")).encode()
    return {
        "schema_sha256": hashlib.sha256(encoded_schema).hexdigest(),
        "table_count": sum(row[0] == "table" for row in schema),
        "user_version": int(user_version),
        "application_id": int(application_id),
        "page_count": int(page_count),
    }


def _pg_arguments(connection: PostgresConnection) -> list[str]:
    return [
        f"--host={connection.host}",
        f"--port={connection.port}",
        f"--username={connection.username}",
        f"--dbname={connection.database}",
    ]


def _reserve_backup_files(output_path: Path) -> tuple[Path, Path]:
    artifact = _new_path(output_path, "backup output")
    if artifact == _PRESERVED_SQLITE:
        raise RecoveryError("The preserved backend/db.sqlite3 is never a backup output.")
    manifest = artifact.with_name(f"{artifact.name}.manifest.json")
    created: list[Path] = []
    try:
        for path in (artifact, manifest):
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            created.append(path)
            os.close(descriptor)
    except FileExistsError as error:
        _remove_created(created)
        raise RecoveryError(
            "The backup artifact or manifest already exists; choose unused paths."
        ) from error
    except OSError as error:
        _remove_created(created)
        raise RecoveryError("Could not create the backup artifact and manifest.") from error
    return artifact, manifest


def _write_manifest(path: Path, data: dict[str, object]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    _restrict_mode(path)


def _artifact_info(path: Path) -> dict[str, object]:
    return {"filename": path.name, "sha256": _sha256(path), "size_bytes": path.stat().st_size}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _new_path(path: Path, label: str) -> Path:
    path = Path(path).expanduser()
    if path.is_symlink():
        raise RecoveryError(f"The {label} path cannot be a symbolic link.")
    try:
        resolved = path.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        raise RecoveryError(f"Could not resolve the {label} path.") from error
    if not resolved.name or not resolved.parent.is_dir():
        raise RecoveryError(f"The {label} parent directory must already exist.")
    return resolved


def _existing_file(path: Path, label: str) -> Path:
    path = Path(path).expanduser()
    if path.is_symlink():
        raise RecoveryError(f"The {label} path cannot be a symbolic link.")
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise RecoveryError(f"Could not read the {label} file.") from error
    if not resolved.is_file():
        raise RecoveryError(f"The {label} path must name a regular file.")
    return resolved


def _restrict_mode(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except OSError as error:
        raise RecoveryError("Could not restrict backup file permissions.") from error


def _remove_created(paths: tuple[Path, ...] | list[Path]) -> None:
    for path in reversed(paths):
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def _cluster_fingerprint(metadata: dict) -> str | None:
    system_identifier = metadata.get("system_identifier")
    database_oid = metadata.get("database_oid")
    if system_identifier is None or database_oid is None:
        return None
    return _fingerprint([str(system_identifier), int(database_oid)])


def _fingerprint(value: object) -> str:
    content = json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode()
    return hashlib.sha256(content).hexdigest()


def _escape_pgpass(value: str) -> str:
    return value.replace("\\", "\\\\").replace(":", "\\:")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _environment_value(name: str) -> str:
    if not _SAFE_ENV_NAME.fullmatch(name):
        raise RecoveryError("Environment variable name is invalid.")
    value = os.environ.get(name, "")
    if not value.strip():
        raise RecoveryError("The required database URL environment variable is empty.")
    return value


class _SafeArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        kwargs["allow_abbrev"] = False
        super().__init__(*args, **kwargs)

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: invalid command arguments\n")


def _parser() -> argparse.ArgumentParser:
    parser = _SafeArgumentParser(
        prog="cadrisyn-recovery",
        description="Create and restore explicit, verifiable database backups.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    postgres_backup = commands.add_parser("backup-postgres")
    postgres_backup.add_argument("--database-url-env", required=True)
    postgres_backup.add_argument("--output", type=Path, required=True)
    sqlite_backup = commands.add_parser("backup-sqlite")
    sqlite_backup.add_argument("--source-path", type=Path, required=True)
    sqlite_backup.add_argument("--output", type=Path, required=True)
    postgres_restore = commands.add_parser("restore-postgres")
    postgres_restore.add_argument("--manifest", type=Path, required=True)
    postgres_restore.add_argument("--target-database-url-env", required=True)
    sqlite_restore = commands.add_parser("restore-sqlite")
    sqlite_restore.add_argument("--manifest", type=Path, required=True)
    sqlite_restore.add_argument("--target-path", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "backup-postgres":
            artifact, manifest = backup_postgres(
                _environment_value(args.database_url_env),
                args.output,
            )
            print(f"Backup created: {artifact}")
            print(f"Manifest created: {manifest}")
        elif args.command == "backup-sqlite":
            artifact, manifest = backup_sqlite(args.source_path, args.output)
            print(f"Backup created: {artifact}")
            print(f"Manifest created: {manifest}")
        elif args.command == "restore-postgres":
            artifact = restore_postgres(
                args.manifest,
                _environment_value(args.target_database_url_env),
            )
            print(f"PostgreSQL restore completed from: {artifact}")
        elif args.command == "restore-sqlite":
            target = restore_sqlite(args.manifest, args.target_path)
            print(f"SQLite restore completed at: {target}")
    except KeyboardInterrupt:
        print("Recovery operation interrupted.", file=sys.stderr)
        return 130
    except RecoveryError as error:
        print(f"Recovery error: {error}", file=sys.stderr)
        return 2
    except (OSError, sqlite3.Error, subprocess.SubprocessError):
        print("Recovery error: a file, database, or PostgreSQL client operation failed.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
