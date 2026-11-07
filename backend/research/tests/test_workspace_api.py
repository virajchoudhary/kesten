import copy
import json
import uuid
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import Client, TestCase

from research.models import ResearchRun
from research.quant.fixtures import make_fixture_payload
from research.replay import result_hash
from research.services import import_dataset, run_evaluation


class ResearchWorkspaceAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user('workspace-research-owner')
        cls.other = get_user_model().objects.create_user('workspace-research-other')
        operator = get_user_model().objects.create_user('workspace-research-operator', is_staff=True)
        cls.dataset, _ = import_dataset(make_fixture_payload(), owner=cls.owner, operator=operator)
        cls.left, _ = run_evaluation(owner=cls.owner, dataset=cls.dataset, horizon=1, idempotency_key=uuid.uuid4())
        cls.right, _ = run_evaluation(owner=cls.owner, dataset=cls.dataset, horizon=1, idempotency_key=uuid.uuid4())
        other_dataset, _ = import_dataset(make_fixture_payload(), owner=cls.other, operator=operator)
        cls.foreign, _ = run_evaluation(owner=cls.other, dataset=other_dataset, horizon=1, idempotency_key=uuid.uuid4())

    def setUp(self):
        cache.clear()
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.owner)
        self.csrf = self.client.get('/api/v1/session/').json()['csrf_token']

    def route(self, run=None, action=''):
        return f'/api/v1/research/runs/{(run or self.left).id}/{action}'

    def replay(self, **kwargs):
        return self.client.post(self.route(action='replay/'), {}, content_type='application/json', HTTP_X_CSRFTOKEN=self.csrf, **kwargs)

    def test_history_is_private_bounded_and_lightweight(self):
        first = self.client.get('/api/v1/research/history/', {'limit': 1}).json()
        second = self.client.get('/api/v1/research/history/', {'limit': 1, 'offset': 1}).json()
        self.assertEqual(first['total'], 2)
        self.assertNotEqual(first['items'][0]['id'], second['items'][0]['id'])
        self.assertEqual({first['items'][0]['id'], second['items'][0]['id']}, {str(self.left.id), str(self.right.id)})
        response = self.client.get('/api/v1/research/history/')
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        self.assertNotIn('result', response.json()['items'][0])
        self.assertNotIn('runtime', response.json()['items'][0])
        self.assertLess(len(response.content) * 10, len(self.client.get('/api/v1/research/runs/').content))

    def test_history_search_filters_and_validation(self):
        for query in [str(self.left.id), self.left.id.hex]:
            response = self.client.get('/api/v1/research/history/', {'q': query})
            self.assertEqual(response.status_code, 200)
            self.assertEqual([r['id'] for r in response.json()['items']], [str(self.left.id)])
        self.assertEqual(self.client.get('/api/v1/research/history/', {'q': str(self.foreign.id)}).json()['total'], 0)
        self.assertEqual(self.client.get('/api/v1/research/history/', {'instrument_id': 'xnys-jpm', 'horizon_sessions': 1, 'data_kind': 'synthetic_fixture'}).json()['total'], 2)
        self.assertEqual(self.client.get('/api/v1/research/history/', {'horizon_sessions': 5}).json()['total'], 0)
        for query in [{'limit': 51}, {'offset': -1}, {'offset': '9' * 80}, {'horizon_sessions': 2}, {'data_kind': 'live'}, {'q': 'a' * 129}, {'unknown': 'x'}]:
            with self.subTest(query=query):
                self.assertEqual(self.client.get('/api/v1/research/history/', query).status_code, 400)

    def test_history_rejects_inconsistent_dataset_lineage(self):
        self.left.result = {**self.left.result, 'dataset_version': '0' * 64}
        self.left.save(update_fields=['result'])
        response = self.client.get('/api/v1/research/history/')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['code'], 'history_integrity_unavailable')
        self.assertNotIn('items', response.json())

    def test_new_routes_require_owner_and_session(self):
        for action in ['export/', f'compare/{self.foreign.id}/']:
            self.assertEqual(self.client.get(self.route(self.foreign, action)).status_code, 404)
        self.assertEqual(self.client.post(self.route(self.foreign, 'replay/'), {}, content_type='application/json', HTTP_X_CSRFTOKEN=self.csrf).status_code, 404)
        self.assertEqual(self.client.get(self.route(action=f'compare/{self.foreign.id}/')).status_code, 404)
        self.client.logout()
        for route in ['/api/v1/research/history/', self.route(action='export/'), self.route(action=f'compare/{self.right.id}/')]:
            self.assertEqual(self.client.get(route).status_code, 403)
        self.assertEqual(self.replay().status_code, 403)

    def test_replay_agrees_with_cli_and_does_not_mutate_run(self):
        before = copy.deepcopy(self.left.result)
        response = self.replay()
        self.assertEqual(response.status_code, 200)
        output = StringIO()
        call_command('replay_research_run', run=str(self.left.id), owner=self.owner.username, stdout=output)
        self.assertEqual(response.json(), json.loads(output.getvalue()))
        self.left.refresh_from_db()
        self.assertEqual(self.left.result, before)
        self.assertEqual(ResearchRun.objects.count(), 3)
        self.left.runtime = {**self.left.runtime, 'engine_source_sha256': '0' * 64}
        self.left.save(update_fields=['runtime'])
        response = self.replay()
        self.assertEqual(response.json()['result'], 'FAIL')
        self.assertFalse(response.json()['engine_matches'])
        self.left.refresh_from_db()
        self.assertEqual(self.left.result, before)

    def test_replay_csrf_body_media_and_throttle(self):
        self.assertEqual(self.client.post(self.route(action='replay/'), {}, content_type='application/json').status_code, 403)
        self.assertEqual(self.client.post(self.route(action='replay/'), {'x': 1}, content_type='application/json', HTTP_X_CSRFTOKEN=self.csrf).status_code, 400)
        self.assertEqual(self.client.post(self.route(action='replay/'), {}, HTTP_X_CSRFTOKEN=self.csrf).status_code, 415)
        cache.clear()
        for _ in range(6):
            self.assertEqual(self.replay().status_code, 200)
        self.assertEqual(self.replay().status_code, 429)

    def test_synthetic_export_preserves_canonical_result_and_identity(self):
        response = self.client.get(self.route(action='export/'))
        self.assertEqual(response.status_code, 200)
        exported = response.json()
        self.assertEqual(exported['run']['id'], str(self.left.id))
        self.assertEqual(exported['dataset']['version'], self.dataset.version)
        self.assertEqual(exported['result_sha256'], result_hash(exported['run']['result']))
        self.assertEqual(exported['run']['result'], self.left.result)
        self.assertEqual(response['Content-Disposition'], f'attachment; filename="cadrisyn-run-{self.left.id}.json"')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        self.assertNotIn('owner', exported['dataset'])
        self.assertNotIn('observations', exported['dataset'])

    def test_export_fails_closed_on_historical_or_tampered_identity(self):
        for mutation in ['historical', 'version', 'claim']:
            with self.subTest(mutation=mutation):
                original = copy.deepcopy(self.left.result)
                original_payload = copy.deepcopy(self.dataset.payload)
                if mutation == 'historical':
                    self.dataset.payload = {**self.dataset.payload, 'data_kind': 'historical'}
                    self.dataset.save(update_fields=['payload'])
                else:
                    self.left.result = {**self.left.result, **({'dataset_version': '0' * 64} if mutation == 'version' else {'empirical_performance_established': True})}
                    self.left.save(update_fields=['result'])
                self.assertEqual(self.client.get(self.route(action='export/')).status_code, 403)
                self.dataset.payload = original_payload
                self.dataset.save(update_fields=['payload'])
                self.left.result = original
                self.left.save(update_fields=['result'])

    def test_comparison_requires_full_compatible_evidence(self):
        route = self.route(action=f'compare/{self.right.id}/')
        self.assertTrue(self.client.get(route).json()['compatible'])
        for field, value, reason in [('protocol', {}, 'protocol_mismatch'), ('models', [], 'method_version_mismatch'), ('target', {}, 'target_mismatch'), ('evaluation_rows', [], 'row_alignment_mismatch'), ('dataset_version', '0' * 64, 'dataset_version_mismatch'), ('engine_version', 'changed', 'engine_version_mismatch'), ('data_kind', 'historical', 'data_kind_mismatch')]:
            with self.subTest(field=field):
                original = copy.deepcopy(self.right.result)
                self.right.result = {**self.right.result, field: value}
                self.right.save(update_fields=['result'])
                comparison = self.client.get(route).json()
                self.assertFalse(comparison['compatible'])
                self.assertIn(reason, comparison['reasons'])
                self.right.result = original
                self.right.save(update_fields=['result'])
