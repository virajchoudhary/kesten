"""Exercise synthetic research upgrade and recovery inside an isolated PostgreSQL stack."""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import uuid


def verify_runtime_privileges(role, privileges):
    if role != "cadrisyn" or any(privileges.values()):
        raise ValueError("Qualification requires the constrained runtime role.")


def read_runtime_privileges(cursor):
    cursor.execute(
        "SELECT rolname, rolsuper, rolcreatedb, rolcreaterole, "
        "has_database_privilege(current_user, current_database(), 'CREATE'), "
        "has_database_privilege(current_user, current_database(), 'TEMPORARY'), "
        "EXISTS(SELECT 1 FROM pg_namespace WHERE nspname !~ '^pg_' "
        "AND nspname <> 'information_schema' AND has_schema_privilege(current_user, oid, 'CREATE')), "
        "EXISTS(SELECT 1 FROM pg_shdepend WHERE refclassid='pg_authid'::regclass "
        "AND refobjid=r.oid AND deptype='o' "
        "AND dbid IN (0, (SELECT oid FROM pg_database WHERE datname=current_database()))), "
        "EXISTS(SELECT 1 FROM pg_auth_members WHERE member=r.oid) "
        "FROM pg_roles r WHERE rolname = current_user"
    )
    role, *flags = cursor.fetchone()
    return role, dict(zip(
        ("superuser", "create_database", "create_role", "create_schema", "temporary", "writable_schema", "owns_objects", "role_membership"),
        flags, strict=True,
    ))


def compare_snapshots(expected, actual):
    if (
        expected != actual
        or expected.get("qualification_schema_version") != 2
        or expected.get("data_kind") != "synthetic_fixture"
        or expected.get("empirical_evaluation") is not False
        or not expected.get("tables")
        or not expected.get("intakes")
        or len(expected.get("replays", [])) < 2
        or {row["horizon_sessions"] for row in expected["replays"]} != {1, 5}
        or any(row["result"] != "PASS" for row in expected["replays"])
    ):
        raise ValueError("Recovery did not preserve all tables, archived intake and exact research replays.")


def prepare_upgrade(directory):
    from django.contrib.auth import get_user_model
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor
    from research.quant.fixtures import make_fixture_payload
    from research.replay import result_hash
    from research.services import import_dataset, run_evaluation

    if connection.introspection.table_names():
        raise ValueError("Upgrade preparation requires a fresh empty qualification database.")
    executor = MigrationExecutor(connection)
    targets = [node for node in executor.loader.graph.leaf_nodes() if node[0] != "research"]
    executor.migrate(targets + [("research", "0001_initial")])
    credentials = json.loads((directory / "fixtures/credentials.json").read_text())
    users = get_user_model().objects
    owner = users.create_user(credentials["username"], password=credentials["password"])
    operator = users.create_user("phase51-operator", is_staff=True)
    dataset, _ = import_dataset(make_fixture_payload(), owner=owner, operator=operator)
    runs = [
        run_evaluation(owner=owner, dataset=dataset, horizon=h, idempotency_key=uuid.uuid4())[0]
        for h in (1, 5)
    ]
    summary = {
        "dataset_id": str(dataset.id), "dataset_version": dataset.version,
        "runs": [{"id": str(run.id), "result_sha256": result_hash(run.result)} for run in runs],
    }
    with (directory / "before-upgrade.json").open("x") as output:
        json.dump(summary, output, indent=2)
    return {"result": "PASS", "schema": "research.0001", "data_kind": "synthetic_fixture"}


def archive_intake(directory):
    from django.contrib.auth import get_user_model
    from django.core.management import call_command
    from django.db.migrations.recorder import MigrationRecorder
    from research.models import ResearchDataset, ResearchRun
    from research.replay import result_hash
    from research.tests.intake_fixtures import intake_arguments

    if not MigrationRecorder.Migration.objects.filter(app="research", name="0002_researchintakereceipt").exists():
        raise ValueError("The intake migration has not been applied.")
    before = json.loads((directory / "before-upgrade.json").read_text())
    dataset = ResearchDataset.objects.get(pk=before["dataset_id"])
    if dataset.version != before["dataset_version"]:
        raise ValueError("Upgrade changed the original dataset version.")
    for identity in before["runs"]:
        if result_hash(ResearchRun.objects.get(pk=identity["id"]).result) != identity["result_sha256"]:
            raise ValueError("Upgrade changed an original run result.")
    owner = dataset.owner
    operator = get_user_model().objects.get(username="phase51-operator")
    arguments = intake_arguments()
    contents = {
        "csv": arguments["csv_bytes"], "terms": arguments["terms_bytes"],
        "availability": arguments["availability_bytes"],
        "metadata": json.dumps(arguments["metadata"]).encode(),
        "source": json.dumps(arguments["source_record"]).encode(),
    }
    with tempfile.TemporaryDirectory() as temporary:
        paths = {name: Path(temporary) / name for name in contents}
        for name, content in contents.items():
            paths[name].write_bytes(content)
        output = io.StringIO()
        call_command(
            "import_research_csv", **paths, owner=owner.username, approved_by=operator.username,
            acknowledge_terms=True, stdout=output,
        )
    receipt = json.loads(output.getvalue())
    if receipt["dataset_id"] != before["dataset_id"] or receipt["data_kind"] != "synthetic_fixture":
        raise ValueError("The imported fixture changed dataset identity or provenance.")
    return {"result": "PASS", "upgrade_preserved_identities": True, "intake": receipt}


def seed_watchlist(directory):
    from research.models import ResearchDataset
    from workspace.models import WatchlistEntry

    before = json.loads((directory / "before-upgrade.json").read_text())
    dataset = ResearchDataset.objects.get(pk=before["dataset_id"])
    if dataset.payload["data_kind"] != "synthetic_fixture":
        raise ValueError("Browser setup requires the isolated synthetic research owner.")
    instruments = ("xnas-aapl", "xnas-msft", "xnas-nvda")
    for instrument in instruments:
        WatchlistEntry.objects.get_or_create(owner=dataset.owner, instrument_id=instrument)
    return {"result": "PASS", "watchlist_fixture": list(instruments), "market_data_mode": "demo"}


def snapshot():
    from django.db import connection, transaction
    from research.intake_replay import verify_intake
    from research.models import ResearchDataset, ResearchIntakeReceipt, ResearchRun
    from research.replay import replay_run

    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            tables = {}
            for name in sorted(connection.introspection.table_names()):
                cursor.execute(f"SELECT row_to_json(t)::text FROM {connection.ops.quote_name(name)} t")
                rows = sorted(row[0] for row in cursor.fetchall())
                tables[name] = {"rows": len(rows), "sha256": hashlib.sha256("\n".join(rows).encode()).hexdigest()}
            role, privileges = read_runtime_privileges(cursor)
        verify_runtime_privileges(role, privileges)
        datasets = [
            {"id": str(row.id), "version": row.version, "data_kind": row.payload["data_kind"]}
            for row in ResearchDataset.objects.order_by("id")
        ]
        if any(row["data_kind"] != "synthetic_fixture" for row in datasets):
            raise ValueError("Qualification must not inspect empirical datasets.")
        intakes = []
        for receipt in ResearchIntakeReceipt.objects.select_related("dataset__owner").order_by("id"):
            intakes.append({
                **verify_intake(receipt, owner=receipt.dataset.owner),
                "artifact_sha256": {
                    field: hashlib.sha256(bytes(getattr(receipt, field))).hexdigest()
                    for field in ("csv_content", "terms_content", "availability_content")
                },
            })
        replays = [
            {**replay_run(run), "horizon_sessions": run.horizon_sessions}
            for run in ResearchRun.objects.select_related("dataset").order_by("id")
        ]
    result = {
        "qualification_schema_version": 2,
        "data_kind": "synthetic_fixture", "empirical_evaluation": False,
        "tables": tables, "datasets": datasets, "intakes": intakes, "replays": replays,
        "runtime_role": role, "runtime_privileges": privileges, "runtime_ddl": False,
    }
    compare_snapshots(result, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare-upgrade", "archive", "seed-watchlist", "snapshot", "verify", "privileges"))
    parser.add_argument("--expected-database", required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get("KERQUANT_ISOLATED_QUALIFICATION") != "phase51":
        parser.error("Set the explicit isolated qualification marker; never target an existing application database.")
    sys.path.insert(0, "/app/backend")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quantvision.settings")
    import django

    django.setup()
    from django.conf import settings
    from django.db import connection

    if not settings.DEBUG or connection.vendor != "postgresql" or connection.settings_dict["NAME"] != args.expected_database:
        parser.error("The configured development PostgreSQL database does not match the explicit target.")
    if args.command == "prepare-upgrade":
        result = prepare_upgrade(args.evidence_dir)
    elif args.command == "archive":
        result = archive_intake(args.evidence_dir)
    elif args.command == "seed-watchlist":
        result = seed_watchlist(args.evidence_dir)
    elif args.command == "privileges":
        with connection.cursor() as cursor:
            role, privileges = read_runtime_privileges(cursor)
        verify_runtime_privileges(role, privileges)
        result = {"result": "PASS", "runtime_role": role, "runtime_privileges": privileges}
    else:
        result = snapshot()
        path = args.evidence_dir / "source-snapshot.json"
        if args.command == "snapshot":
            with path.open("x") as output:
                json.dump(result, output, indent=2)
        else:
            compare_snapshots(json.loads(path.read_text()), result)
        result = {
            "result": "PASS", "command": args.command, "tables": len(result["tables"]),
            "intakes": len(result["intakes"]), "replays": len(result["replays"]),
            "runtime_ddl": False, "data_kind": "synthetic_fixture", "empirical_evaluation": False,
        }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
