"""Exercise the retained-volume role upgrade on a new, retained Docker volume."""

import argparse
import json
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def docker(*arguments, sql=None, check=True):
    result = subprocess.run(
        ["docker", *arguments], input=sql, text=True, capture_output=True, check=False
    )
    if check and result.returncode:
        # SQL commands never contain credentials; avoid echoing container metadata.
        raise RuntimeError(result.stderr.strip() or "Docker command failed")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="New disposable container/volume prefix")
    parser.add_argument("--env-file", required=True, type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r"cadrisyn-[a-z0-9-]+", args.name):
        parser.error("Use a cadrisyn- prefixed lowercase name")
    # Refuse reuse so this verification cannot modify an existing environment.
    for kind, name in (("container", args.name), ("volume", args.name + "-data")):
        if docker(kind, "inspect", name, check=False).returncode == 0:
            parser.error(f"{kind} already exists; choose a new disposable name")
    docker(
        "create", "--name", args.name, "--env-file", str(args.env_file.resolve()),
        "--env", "POSTGRES_USER=cadrisyn", "--env", "POSTGRES_DB=cadrisyn",
        "--volume", args.name + "-data:/var/lib/postgresql/data", "postgres:17.11",
    )
    docker("start", args.name)

    def psql(sql, *, user="cadrisyn", check=True):
        password_key = {
            "cadrisyn": "POSTGRES_PASSWORD",
            "postgres": "POSTGRES_ADMIN_PASSWORD",
            "cadrisyn_migrator": "POSTGRES_MIGRATION_PASSWORD",
        }[user]
        return docker(
            "exec", "--interactive", args.name, "sh", "-c",
            f'export PGPASSWORD="${password_key}"; exec psql "$@"', "psql", "-X", "-qAt",
            "-v", "ON_ERROR_STOP=1", "-h", "127.0.0.1", "-U", user,
            "-d", "cadrisyn", sql=sql, check=check,
        )

    for _ in range(90):
        if psql("SELECT 1;", check=False).returncode == 0:
            break
        time.sleep(1)
    else:
        raise RuntimeError("Legacy PostgreSQL did not become ready")
    assert psql("SELECT rolsuper FROM pg_roles WHERE rolname='cadrisyn';").stdout.strip() == "t"
    psql("CREATE TABLE preserved_probe(id bigserial PRIMARY KEY, value text); "
         "INSERT INTO preserved_probe(value) VALUES ('preserved legacy row');")
    before = psql("SELECT id, value FROM preserved_probe;").stdout
    psql((ROOT / "deploy/prepare-preview-role-upgrade.sql").read_text())
    upgrade = (ROOT / "deploy/upgrade-preview-roles.sql").read_text()
    # An operator must switch away from the role about to lose superuser power.
    refusal = psql(upgrade, check=False)
    assert refusal.returncode != 0 and "Reconnect as a separate" in refusal.stderr
    psql(upgrade, user="postgres")
    assert psql("SELECT id, value FROM preserved_probe;").stdout == before
    flags = psql("SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls "
                 "FROM pg_roles WHERE rolname='cadrisyn';").stdout.strip()
    assert flags == "f|f|f|f|f", flags
    assert psql("SELECT rolsuper,rolcanlogin FROM pg_roles WHERE "
                "rolname='cadrisyn_legacy_bootstrap';", user="postgres").stdout.strip() == "t|f"
    assert psql("SELECT pg_get_userbyid(datdba) FROM pg_database "
                "WHERE datname='cadrisyn';").stdout.strip() == "cadrisyn_migrator"
    for statement in ("CREATE TABLE forbidden(id int);", "CREATE TEMP TABLE forbidden(id int);"):
        assert psql(statement, check=False).returncode != 0
    psql("INSERT INTO preserved_probe(value) VALUES ('runtime write');")
    psql("CREATE TABLE migration_probe(id bigserial PRIMARY KEY, value text);", user="cadrisyn_migrator")
    psql("INSERT INTO migration_probe(value) VALUES ('default grants work');")
    # A second application must preserve both preexisting and runtime-written rows.
    psql(upgrade, user="postgres")
    assert psql("SELECT count(*) FROM preserved_probe;").stdout.strip() == "2"
    assert psql("SELECT count(*) FROM migration_probe;").stdout.strip() == "1"
    docker("restart", args.name)
    for _ in range(30):
        if psql("SELECT count(*) FROM preserved_probe;", check=False).stdout.strip() == "2":
            break
        time.sleep(1)
    else:
        raise RuntimeError("Upgraded database did not recover after restart")
    print(json.dumps({
        "result": "PASS", "legacy_runtime_superuser_before": True,
        "runtime_privileged_after": False, "rows_preserved": True,
        "runtime_dml": True, "runtime_permanent_and_temp_ddl_denied": True,
        "migration_default_grants": True, "idempotent_upgrade": True,
        "restart_preserved_data": True, "container": args.name,
        "retained_volume": args.name + "-data",
    }, indent=2))


if __name__ == "__main__":
    main()
