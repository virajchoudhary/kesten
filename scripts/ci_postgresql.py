"""Run application tests against a new, password-authenticated PostgreSQL container."""

import os
import secrets
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]


def main():
    directory = ROOT / ".local"
    directory.mkdir(exist_ok=True)
    name = "kerquant-ci-postgres-" + uuid.uuid4().hex[:12]
    administrator = secrets.token_hex(24)
    runtime = secrets.token_hex(24)
    migration = secrets.token_hex(24)
    with tempfile.TemporaryDirectory(prefix="postgres-ci-", dir=directory) as temporary:
        env_file = Path(temporary) / "database.env"
        env_file.write_text(
            f"POSTGRES_USER=postgres\nPOSTGRES_PASSWORD={administrator}\n"
            f"CADRISYN_DB_PASSWORD={runtime}\nCADRISYN_MIGRATION_PASSWORD={migration}\n",
            encoding="utf-8",
        )
        env_file.chmod(0o600)
        cid_file = Path(temporary) / "container-id"
        try:
            subprocess.run([
                "docker", "run", "--detach", "--rm", "--name", name,
                "--cidfile", str(cid_file), "--tmpfs", "/var/lib/postgresql/data",
                "--publish", "127.0.0.1::5432", "--env-file", str(env_file),
                "postgres:17.11",
            ], check=True, stdout=subprocess.DEVNULL, timeout=120)
            port = subprocess.check_output(
                ["docker", "port", name, "5432/tcp"], text=True, timeout=15,
            ).strip().rsplit(":", 1)[1]
            deadline = time.monotonic() + 180
            while True:
                probe = subprocess.run(
                    ["docker", "exec", name, "pg_isready", "-U", "postgres", "-h", "127.0.0.1"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=10,
                )
                if probe.returncode == 0:
                    break
                state = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.Running}}", name],
                    capture_output=True, text=True, timeout=15,
                )
                if state.returncode != 0 or state.stdout.strip() != "true":
                    raise RuntimeError("Disposable PostgreSQL exited before readiness or became unavailable.")
                if time.monotonic() >= deadline:
                    raise RuntimeError("Disposable PostgreSQL did not become ready.")
                time.sleep(0.5)
            subprocess.run(
                ["docker", "exec", "--interactive", name, "sh"],
                input=(ROOT / "deploy/postgres-init.sh").read_bytes(), check=True, timeout=60,
            )
            with psycopg.connect(
                host="127.0.0.1", port=port, dbname="postgres",
                user="postgres", password=administrator, autocommit=True,
            ) as database:
                database.execute("CREATE DATABASE test_cadrisyn OWNER cadrisyn_migrator")
                database.execute("REVOKE ALL ON DATABASE test_cadrisyn FROM PUBLIC, cadrisyn")
                database.execute("GRANT CONNECT ON DATABASE test_cadrisyn TO cadrisyn, cadrisyn_migrator")

            environment = {
                **os.environ,
                "DJANGO_SETTINGS_MODULE": "quantvision.settings",
                "DJANGO_DEBUG": "true",
                "DJANGO_SECRET_KEY": secrets.token_hex(32),
                "DJANGO_ALLOWED_HOSTS": "localhost,127.0.0.1,testserver",
                "CADRISYN_MARKET_DATA_ENABLED": "false",
                "CADRISYN_LEGACY_ENABLED": "false",
            }
            environment.pop("DJANGO_SECRET_KEY_FILE", None)
            environment.pop("CADRISYN_DB_PATH", None)

            def manage(*arguments, user="cadrisyn", password=runtime, database="cadrisyn"):
                env = {
                    **environment,
                    "DATABASE_URL": f"postgresql://{user}:{password}@127.0.0.1:{port}/{database}",
                }
                subprocess.run(
                    [sys.executable, str(ROOT / "backend/manage.py"), *arguments],
                    cwd=ROOT / "backend", env=env, check=True,
                )

            for database in ("cadrisyn", "test_cadrisyn"):
                manage("migrate", "--noinput", user="cadrisyn_migrator", password=migration, database=database)
            with psycopg.connect(
                host="127.0.0.1", port=port, dbname="test_cadrisyn",
                user="postgres", password=administrator,
            ) as database:
                database.execute("GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA public TO cadrisyn")
                database.execute("GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO cadrisyn")
            manage("makemigrations", "--check", "--dry-run")
            manage("test", "accounts", "workspace", "research", "api.test_security", "--keepdb", "--noinput")
        finally:
            if cid_file.is_file():
                container_id = cid_file.read_text().strip()
                original_error = sys.exception()
                try:
                    stopped = subprocess.run(
                        ["docker", "stop", container_id],
                        capture_output=True, text=True, timeout=30,
                    )
                    if stopped.returncode and "No such container:" not in stopped.stderr:
                        stopped.check_returncode()
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    if original_error is None:
                        raise
                    original_error.add_note("Disposable PostgreSQL cleanup also failed; inspect the recorded container ID.")
                    print("Disposable PostgreSQL cleanup failed; the original error is preserved.", file=sys.stderr)


if __name__ == "__main__":
    main()
