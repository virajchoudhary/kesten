"""Container-side checks for disposable production qualification, never application startup."""

import json
import os
from pathlib import Path
from uuid import uuid4


def bootstrap(credentials):
    """Seed only an explicitly marked, empty development bootstrap container."""
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.db import connection
    from research.ingestion import prepare_csv_intake
    from research.models import ResearchDataset
    from research.replay import result_hash
    from research.services import import_dataset, run_evaluation
    from research.tests.intake_fixtures import intake_arguments

    if not settings.DEBUG or connection.settings_dict["NAME"] != "cadrisyn":
        raise ValueError("Bootstrap requires the disposable development database.")
    users = get_user_model().objects
    if users.exists() or ResearchDataset.objects.exists():
        raise ValueError("Qualification bootstrap refuses a populated database.")
    for item in credentials:
        users.create_user(item["username"], password=item["password"])
    operator = users.create_user("qualification_operator", is_staff=True)
    owner = users.get(username=credentials[0]["username"])
    intake = prepare_csv_intake(**intake_arguments())
    payload = json.loads(json.dumps(intake.dataset.payload, allow_nan=False))
    dataset, _ = import_dataset(payload, owner=owner, operator=operator, intake=intake)
    hashes = {}
    for horizon in (1, 5):
        run, _ = run_evaluation(owner=dataset.owner, dataset=dataset, horizon=horizon, idempotency_key=uuid4())
        hashes[str(horizon)] = result_hash(run.result)
    expected = {
        "1": "9a45a5cca4ce69b11d0ae494f23679a278057ae61b995cf2957d7ea378c19e50",
        "5": "995a224ce3925f972ca224ece6f548d45277ecdd364a50d13998b4649e5f33be",
    }
    if hashes != expected or dataset.version != "9203cba1c9d58f65505fc7c05120669be1829719c7d033d58ab8155387a47a94":
        raise ValueError("Validated synthetic numerical contract changed.")
    return {"result": "PASS", "data_kind": "synthetic_fixture", "empirical_evaluation": False, "result_hashes": hashes}


def recover():
    """Verify an actual dump/restore and refusal of source or populated targets."""
    from django.db import connection
    from qualify_research_postgres import compare_snapshots, snapshot

    from scripts.ops.recovery import RecoveryError, backup_postgres, restore_postgres
    before = snapshot()
    source = Path("/run/secrets/database_url").read_text().strip()
    target = Path("/run/secrets/migration_url").read_text().strip().replace("/cadrisyn?", "/qualification_restore?")
    artifact, manifest = backup_postgres(source, Path("/qualification/database.dump"))
    rejected = []
    try:
        restore_postgres(manifest, source)
    except RecoveryError:
        rejected.append("source")
    restore_postgres(manifest, target)
    try:
        restore_postgres(manifest, target)
    except RecoveryError:
        rejected.append("populated")
    connection.close()
    connection.settings_dict["NAME"] = "qualification_restore"
    after = snapshot()
    compare_snapshots(before, after)
    if rejected != ["source", "populated"]:
        raise ValueError("Restore refusal contract failed.")
    return {
        "result": "PASS", "tables": len(after["tables"]), "runs_replayed": len(after["replays"]),
        "intakes": len(after["intakes"]), "refused": rejected, "dump_bytes": artifact.stat().st_size,
        "runtime_privileges": after["runtime_privileges"], "data_kind": "synthetic_fixture", "empirical_evaluation": False,
    }


def main(operation, payload):
    if os.environ.get("KERQUANT_PRODUCTION_QUALIFICATION") != "isolated":
        raise ValueError("The isolated qualification marker is required.")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quantvision.settings")
    import django

    django.setup()
    if operation == "bootstrap":
        result = bootstrap(payload)
    elif operation == "recover":
        result = recover()
    elif operation == "marker":
        result = mark_restored(payload)
    else:
        raise ValueError("Unsupported qualification operation.")
    print(json.dumps(result))


def mark_restored(username):
    """Write a disposable HTTP-visible marker exclusively into the restored database."""
    from django.contrib.auth import get_user_model
    from django.db import connection
    from workspace.models import WatchlistEntry

    connection.close()
    connection.settings_dict["NAME"] = "qualification_restore"
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database()")
        if cursor.fetchone()[0] != "qualification_restore":
            raise ValueError("The marker must target the isolated restore.")
    owner = get_user_model().objects.get(username=username)
    if WatchlistEntry.objects.filter(owner=owner).exists():
        raise ValueError("The disposable marker owner must have an empty watchlist.")
    WatchlistEntry.objects.create(owner=owner, instrument_id="xnas-msft")
    return {"result": "PASS", "database": "qualification_restore"}
