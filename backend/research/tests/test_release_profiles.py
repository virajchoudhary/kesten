import copy
import uuid

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings

from research.models import ResearchRun
from research.quant.fixtures import make_fixture_payload
from research.services import import_dataset, run_evaluation


class ResearchReleaseProfileTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user('release-profile-owner', is_staff=True)
        cls.dataset, _ = import_dataset(make_fixture_payload(), owner=cls.owner, operator=cls.owner)
        cls.research_run, _ = run_evaluation(owner=cls.owner, dataset=cls.dataset, horizon=1, idempotency_key=uuid.uuid4())

    @override_settings(CADRISYN_RELEASE_PROFILE='demo')
    def test_demo_hides_every_private_research_route_and_preserves_data(self):
        client = Client(enforce_csrf_checks=True)
        original = copy.deepcopy(self.research_run.result)
        routes = ['/api/v1/research/datasets/', '/api/v1/research/history/', '/api/v1/research/runs/', f'/api/v1/research/runs/{self.research_run.id}/', f'/api/v1/research/runs/{self.research_run.id}/export/', f'/api/v1/research/runs/{self.research_run.id}/compare/{self.research_run.id}/']
        for authenticated in [False, True]:
            if authenticated:
                client.force_login(self.owner)
            for route in routes:
                with self.subTest(authenticated=authenticated, route=route):
                    response = client.get(route)
                    self.assertEqual(response.status_code, 404)
                    self.assertNotIn(str(self.dataset.id), response.content.decode())
            for route in ['/api/v1/research/runs/', f'/api/v1/research/runs/{self.research_run.id}/replay/']:
                self.assertEqual(client.post(route, {}, content_type='application/json').status_code, 404)
        self.research_run.refresh_from_db()
        self.assertEqual(self.research_run.result, original)
        self.assertEqual(ResearchRun.objects.count(), 1)

    @override_settings(CADRISYN_RELEASE_PROFILE='development')
    def test_development_preserves_existing_private_research(self):
        client = Client()
        client.force_login(self.owner)
        self.assertEqual(client.get('/api/v1/research/datasets/').json()['items'][0]['id'], str(self.dataset.id))
