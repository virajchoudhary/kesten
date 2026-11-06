"""Qualify additive research migrations in a new isolated PostgreSQL database."""

import io
import json
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quantvision.settings')
import django
django.setup()
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from research.services import import_dataset
from research.quant.fixtures import make_fixture_payload
from workspace.models import WatchlistEntry

if not settings.DEBUG or connection.vendor != 'postgresql' or connection.settings_dict['NAME'] != 'cadrisyn_qualification_phase35':
    raise SystemExit('Requires the explicitly isolated qualification database.')
if connection.introspection.table_names():
    raise SystemExit('Refusing a nonempty target; no tables or data will be removed.')

executor = MigrationExecutor(connection)
executor.migrate([node for node in executor.loader.graph.leaf_nodes() if node[0] != 'research'])
if any(app == 'research' for app, _ in MigrationExecutor(connection).loader.applied_migrations):
    raise SystemExit('Unexpected research dependency in the pre-research schema.')
owner = get_user_model().objects.create_user('migration_probe')
WatchlistEntry.objects.create(owner=owner, instrument_id='xnys-jpm')
snapshots = []
for stage in ['before', 'after', 'repeat']:
    if stage != 'before':
        call_command('migrate', interactive=False, stdout=io.StringIO(), verbosity=0)
    output = io.StringIO()
    call_command('dumpdata', 'auth.user', 'workspace', 'accounts', use_natural_foreign_keys=True, use_natural_primary_keys=True, stdout=output)
    snapshots.append(sorted(json.dumps(row, sort_keys=True) for row in json.loads(output.getvalue())))
if snapshots[0] != snapshots[1] or snapshots[0] != snapshots[2]:
    raise SystemExit('Existing account/watchlist fields changed during migration.')
if ('research', '0001_initial') not in MigrationExecutor(connection).loader.applied_migrations:
    raise SystemExit('The research migration was not applied.')
dataset, created = import_dataset(make_fixture_payload(), owner=owner, operator=owner, synthetic_bootstrap=True)
if not created or dataset.payload['data_kind'] != 'synthetic_fixture':
    raise SystemExit('Upgraded research storage did not accept the explicit synthetic fixture.')
print(json.dumps({'result': 'PASS', 'schema_before': 'all enabled migrations except research', 'existing_fixture_objects': len(snapshots[0]), 'existing_fields_unchanged': True, 'research_migration_applied': True, 'repeat_migration_preserves_fields': True, 'new_research_storage': 'synthetic_fixture'}))
