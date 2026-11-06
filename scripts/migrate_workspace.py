"""Copy a workspace SQLite database to an empty, migrated PostgreSQL database."""

import argparse
import io
import json
import os
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = ["auth.user", "auth.group", "workspace", "accounts", "admin.logentry"]


def source_path(value):
    path = Path(value).expanduser().resolve()
    if path == (ROOT / "backend/db.sqlite3").resolve():
        raise ValueError("The original research database is not a workspace migration source.")
    if not path.is_file():
        raise ValueError("The workspace source must be an existing SQLite file.")
    return path


def canonical_fixture(text):
    return sorted(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in json.loads(text))


def transferable_fixture(text):
    rows = json.loads(text)
    allowed = []
    excluded = {"restricted_snapshots": 0, "unused_account_tokens": 0}
    for row in rows:
        fields = row["fields"]
        if row["model"] == "workspace.marketsnapshot" and fields.get("data_mode") != "demo":
            excluded["restricted_snapshots"] += 1
        elif row["model"] in {"accounts.accountinvitation", "accounts.passwordresettoken"} and not fields.get("consumed_at") and not fields.get("revoked_at"):
            excluded["unused_account_tokens"] += 1
        else:
            allowed.append(row)
    return json.dumps(allowed), excluded


def require_empty_destination(models):
    from django.contrib.sessions.models import Session

    if Session.objects.exists() or any(model._default_manager.exists() for model in models):
        raise ValueError("The destination contains account, session or workspace data; refusing to overwrite it.")


def snapshot_sqlite(source, target):
    with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as original, closing(sqlite3.connect(target)) as copy:
        original.backup(copy)
        if copy.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Source integrity check failed.")


def transfer(source):
    import django

    sys.path.insert(0, str(ROOT / "backend"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quantvision.settings")
    django.setup()
    from django.apps import apps
    from django.conf import settings
    from django.core.management import call_command
    from django.db import connections, transaction
    from django.db.migrations.executor import MigrationExecutor

    destination = connections["default"]
    if destination.vendor != "postgresql":
        raise ValueError("Set DATABASE_URL to the explicit PostgreSQL destination; SQLite destinations are refused.")
    executor = MigrationExecutor(destination)
    if executor.migration_plan(executor.loader.graph.leaf_nodes()):
        raise ValueError("Run schema migrations on the empty destination first.")
    copied_models = [model for model in apps.get_models() if model._meta.app_label in {"workspace", "accounts"}]
    copied_models.extend(apps.get_model(name) for name in ("auth.User", "auth.Group", "admin.LogEntry"))
    require_empty_destination(copied_models)
    local = ROOT / ".local"
    local.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="workspace-migration-", dir=local) as directory:
        clone = Path(directory) / "source.sqlite3"
        snapshot_sqlite(source, clone)
        clone.chmod(0o600)
        settings.DATABASES["migration_source"] = {
            **settings.DATABASES["default"],
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": clone,
            "OPTIONS": {"timeout": 30},
            "CONN_MAX_AGE": 0,
        }
        source_connection = connections["migration_source"]
        try:
            source_executor = MigrationExecutor(source_connection)
            if source_executor.migration_plan(source_executor.loader.graph.leaf_nodes()):
                raise ValueError("Migrate the local workspace schema before transferring it.")
            output = io.StringIO()
            call_command("dumpdata", *MODELS, database="migration_source", use_natural_foreign_keys=True, use_natural_primary_keys=True, stdout=output)
            transferable, excluded = transferable_fixture(output.getvalue())
            fixture = Path(directory) / "workspace.json"
            fixture.write_text(transferable, encoding="utf-8")
            fixture.chmod(0o600)
            with transaction.atomic():
                # Serialize concurrent invocations without changing existing destination rows.
                with destination.cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_xact_lock(%s)", [817327491])
                require_empty_destination(copied_models)
                call_command("loaddata", str(fixture), verbosity=0)
                verified = io.StringIO()
                call_command("dumpdata", *MODELS, use_natural_foreign_keys=True, use_natural_primary_keys=True, stdout=verified)
                if canonical_fixture(transferable) != canonical_fixture(verified.getvalue()):
                    raise ValueError("Destination verification differs from source; transfer rolled back.")
            return {"result": "PASS", "objects_copied": len(json.loads(transferable)), "restricted_snapshots_left_at_source": excluded["restricted_snapshots"], "unused_account_tokens_left_at_source": excluded["unused_account_tokens"], "verification": "all copied fixture fields match", "sessions": "not copied; empty destination required; sign in again"}
        finally:
            source_connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-sqlite", required=True)
    args = parser.parse_args()
    try:
        result = transfer(source_path(args.source_sqlite))
    except Exception as error:
        # Connection and fixture exceptions may contain credentials or password hashes.
        print(f"Workspace transfer failed ({type(error).__name__}). Destination must be empty and both schemas current. Source remains unchanged.", file=sys.stderr)
        raise SystemExit(1) from None
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
