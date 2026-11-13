"""Prove synthetic intake, additive migration and recovery in new disposable databases."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
from io import StringIO

root = Path(__file__).resolve().parents[1]


def verify_restored_result(result, *, receipt, artifacts, runs):
    identity = ('receipt_id', 'receipt_version', 'dataset_id', 'dataset_version', 'data_kind')
    restored_runs = result['runs']
    restored_identities = [(run['run_id'], run['result_sha256']) for run in restored_runs]
    if (
        result['data_kind'] != 'synthetic_fixture'
        or result['intake']['match'] is not True
        or any(result['intake'][key] != receipt[key] for key in identity)
        or result['artifact_sha256'] != artifacts
        or len(runs) != 2
        or restored_identities != runs
        or any(run['result'] != 'PASS' for run in restored_runs)
    ):
        raise ValueError('Restoration did not preserve the expected receipt, archived bytes and both exact runs.')


def main():
    task = root / '.local/research-intake-qualification'
    task.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(root / 'scripts'))
    from dev import development_environment

    environment = development_environment()
    restore_check = len(sys.argv) == 3 and sys.argv[1] == '--restore-check'
    token = uuid.uuid4().hex[:12]
    database = Path(sys.argv[2]) if restore_check else task / ('intake-' + token + '.sqlite3')
    assert database.resolve().is_relative_to(task.resolve())
    environment['CADRISYN_DB_PATH'] = str(database)
    os.environ.update(environment)
    sys.path.insert(0, str(root / 'backend'))
    import django
    django.setup()

    from django.contrib.auth import get_user_model
    from django.core.management import call_command
    from django.db import connection, connections
    from django.db.migrations.executor import MigrationExecutor
    from research.intake_replay import verify_intake
    from research.models import ResearchIntakeReceipt, ResearchRun
    from research.quant.fixtures import make_fixture_payload
    from research.replay import replay_run, result_hash
    from research.services import import_dataset, run_evaluation
    from research.tests.intake_fixtures import intake_arguments

    if restore_check:
        receipt = ResearchIntakeReceipt.objects.select_related('dataset').get()
        owner = receipt.dataset.owner
        print(json.dumps({
            'data_kind': 'synthetic_fixture',
            'intake': verify_intake(receipt, owner=owner),
            'artifact_sha256': {
                field: hashlib.sha256(bytes(getattr(receipt, field))).hexdigest()
                for field in ['csv_content', 'terms_content', 'availability_content']
            },
            'runs': [replay_run(r) for r in ResearchRun.objects.order_by('horizon_sessions')],
        }))
        raise SystemExit(0)

    assert not database.exists()
    executor = MigrationExecutor(connection)
    targets = [node for node in executor.loader.graph.leaf_nodes() if node[0] != 'research']
    executor.migrate(targets + [('research','0001_initial')])
    users = get_user_model().objects
    owner = users.create_user('phase5-proof-owner')
    operator = users.create_user('phase5-proof-operator',is_staff=True)
    dataset, _ = import_dataset(make_fixture_payload(),owner=owner,operator=operator)
    runs = [
        run_evaluation(owner=owner, dataset=dataset, horizon=h, idempotency_key=uuid.uuid4())[0]
        for h in [1, 5]
    ]
    before = {
        'dataset_id': str(dataset.id), 'dataset_version': dataset.version,
        'runs': [(str(r.id), result_hash(r.result)) for r in runs],
    }
    executor = MigrationExecutor(connection)
    executor.migrate(executor.loader.graph.leaf_nodes())
    dataset.refresh_from_db()
    for run in runs:
        run.refresh_from_db()
    after = {
        'dataset_id': str(dataset.id), 'dataset_version': dataset.version,
        'runs': [(str(r.id), result_hash(r.result)) for r in runs],
    }
    assert before == after

    arguments = intake_arguments()
    files = {
        'csv':arguments['csv_bytes'],'metadata':json.dumps(arguments['metadata']).encode(),
        'source':json.dumps(arguments['source_record']).encode(),'terms':arguments['terms_bytes'],
        'availability':arguments['availability_bytes'],
    }
    directory = task / ('input-' + token)
    directory.mkdir()
    paths = {}
    for key,content in files.items():
        paths[key] = directory / key
        with paths[key].open('xb') as file:
            file.write(content)
    output = StringIO()
    call_command(
        'import_research_csv', **paths, owner=owner.username, approved_by=operator.username,
        acknowledge_terms=True, stdout=output,
    )
    receipt_report = json.loads(output.getvalue())
    receipt = ResearchIntakeReceipt.objects.select_related('dataset').get()
    assert receipt.dataset_id == dataset.id
    assert verify_intake(receipt,owner=owner)['match']
    original = {
        field: hashlib.sha256(bytes(getattr(receipt, field))).hexdigest()
        for field in ['csv_content', 'terms_content', 'availability_content']
    }
    connections.close_all()

    from ops.recovery import backup_sqlite,restore_sqlite
    artifact,manifest = backup_sqlite(database,task / ('backup-' + token + '.sqlite3'))
    restored = restore_sqlite(manifest,task / ('restored-' + token + '.sqlite3'))
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), '--restore-check', str(restored)],
        cwd=root, env=environment, capture_output=True, text=True, check=True,
    )
    restored_result = json.loads(completed.stdout)
    verify_restored_result(restored_result, receipt=receipt_report, artifacts=original, runs=before['runs'])
    report = {
        'result':'PASS','data_kind':'synthetic_fixture','empirical_evaluation':False,
        'migration_preserved_dataset_and_runs':before==after,'before':before,'after':after,
        'source_intake':receipt_report,'artifact_sha256':original,'restored':restored_result,
        'database':str(database.relative_to(root)),'backup':str(artifact.relative_to(root)),
        'backup_manifest':str(manifest.relative_to(root)),'restored_database':str(restored.relative_to(root)),
    }
    (task/'intake-recovery.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Synthetic source intake, additive upgrade, backup/restore and exact replay PASS.')


if __name__ == '__main__':
    main()
