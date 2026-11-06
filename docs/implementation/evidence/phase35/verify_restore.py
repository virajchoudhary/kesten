import hashlib
import io
import json
import os
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quantvision.settings')
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
from django.db import connection

assert settings.DEBUG and connection.vendor == 'postgresql'
assert connection.settings_dict['NAME'] == 'restore_cadrisyn'
expected = json.loads(Path('/verification/source-summary.json').read_text(encoding='utf-8'))
output = io.StringIO()
models = ['auth.user', 'auth.group', 'workspace', 'accounts', 'research', 'admin.logentry']
call_command('dumpdata', *models, use_natural_foreign_keys=True, use_natural_primary_keys=True, stdout=output)
fixture = json.loads(output.getvalue())
canonical = sorted(json.dumps(row, sort_keys=True, separators=(',', ':')) for row in fixture)
assert len(fixture) == expected['objects_compared_after_restore']
assert hashlib.sha256(json.dumps(canonical).encode()).hexdigest() == expected['fixture_sha256']
for saved in expected['replays']:
    replay = io.StringIO()
    call_command('replay_research_run', run=saved['run_id'], owner='analyst', stdout=replay)
    result = json.loads(replay.getvalue())
    assert result['result'] == 'PASS' and result['result_sha256'] == saved['result_sha256']
print(json.dumps({'result': 'PASS', 'objects_compared': len(fixture), 'comparison': 'all copied fixture fields', 'replayed_horizons': [1, 5], 'data_kind': 'synthetic_fixture', 'empirical_performance_established': False}))
