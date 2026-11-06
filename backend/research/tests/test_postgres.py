import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection
from django.test import TransactionTestCase

from research.models import ResearchDataset, ResearchRun
from research.quant.fixtures import make_fixture_payload
from research.services import import_dataset, run_evaluation


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row locks and concurrent transactions")
class ResearchPostgresTests(TransactionTestCase):
    def test_concurrent_identical_requests_persist_one_complete_result(self):
        user = get_user_model().objects.create_user("parallel-research", is_staff=True)
        dataset, _ = import_dataset(make_fixture_payload(), owner=user, operator=user)
        key = uuid.uuid4()

        def calculate():
            close_old_connections()
            try:
                current_user = get_user_model().objects.get(pk=user.pk)
                current_dataset = ResearchDataset.objects.get(pk=dataset.pk)
                run, created = run_evaluation(
                    owner=current_user, dataset=current_dataset, horizon=5, idempotency_key=key
                )
                return run.id, created, run.result
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: calculate(), range(2)))
        self.assertEqual(results[0][0], results[1][0])
        self.assertEqual(sum(created for _, created, _ in results), 1)
        self.assertEqual(results[0][2], results[1][2])
        self.assertEqual(ResearchRun.objects.count(), 1)
