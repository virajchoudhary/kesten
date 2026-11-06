import hashlib
import io
import json
import os
import uuid
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quantvision.settings')
import django
django.setup()
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from research.models import ResearchDataset
from research.services import run_evaluation

assert settings.DEBUG and connection.vendor == 'postgresql'
assert connection.settings_dict['NAME'] == 'cadrisyn'
owner = get_user_model().objects.get(username='analyst')
dataset = ResearchDataset.objects.get(owner=owner)
assert dataset.payload['data_kind'] == 'synthetic_fixture'
replays = []
for horizon in [1, 5]:
    run, created = run_evaluation(owner=owner, dataset=dataset, horizon=horizon, idempotency_key=uuid.uuid4())
    assert created
    output = io.StringIO()
    call_command('replay_research_run', run=str(run.id), owner=owner.username, stdout=output)
    replay = json.loads(output.getvalue())
    assert replay['result'] == 'PASS'
    replays.append({'horizon_sessions': horizon, **replay})

output = io.StringIO()
models = ['auth.user', 'auth.group', 'workspace', 'accounts', 'research', 'admin.logentry']
call_command('dumpdata', *models, use_natural_foreign_keys=True, use_natural_primary_keys=True, stdout=output)
fixture = json.loads(output.getvalue())
canonical = sorted(json.dumps(row, sort_keys=True, separators=(',', ':')) for row in fixture)
summary = {
    'result': 'PASS', 'data_kind': 'synthetic_fixture', 'empirical_performance_established': False,
    'replays': replays, 'objects_compared_after_restore': len(fixture),
    'fixture_sha256': hashlib.sha256(json.dumps(canonical).encode()).hexdigest(),
}
Path('/tmp/phase35-source-summary.json').write_text(json.dumps(summary), encoding='utf-8')
print(json.dumps(summary))
