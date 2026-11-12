from django.contrib.auth import get_user_model
from django.test import TestCase


class OperationalMetricsTests(TestCase):
    def test_metrics_are_operator_only_and_aggregate_without_private_labels(self):
        self.assertEqual(self.client.get('/health/metrics/').status_code, 403)
        user = get_user_model().objects.create_user('metrics-user')
        self.client.force_login(user)
        self.assertEqual(self.client.get('/health/metrics/').status_code, 403)
        user.is_staff = True
        user.save(update_fields=['is_staff'])
        self.client.get('/health/')
        response = self.client.get('/health/metrics/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        snapshot = response.json()
        self.assertEqual(snapshot['scope'], 'single_worker')
        self.assertGreater(snapshot['requests_total'], 0)
        self.assertGreaterEqual(snapshot['request_duration_seconds_total'], 0)
        self.assertEqual(sum(snapshot['status_classes'].values()), snapshot['requests_total'])
        self.assertNotIn('metrics-user', response.content.decode())
        before = snapshot['requests_total']
        self.client.get('/health/')
        self.assertGreater(self.client.get('/health/metrics/').json()['requests_total'], before)
