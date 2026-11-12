import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection, connections
from django.test import TransactionTestCase

from research.models import ResearchDataset, ResearchRun
from research.quant import evaluate
from research.quant.fixtures import make_fixture_payload
from research.services import import_dataset, run_evaluation


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row locks and concurrent transactions")
class ResearchPostgresTests(TransactionTestCase):
    def test_concurrent_identical_requests_persist_one_complete_result(self):
        user = get_user_model().objects.create_user("parallel-research", is_staff=True)
        dataset, _ = import_dataset(make_fixture_payload(), owner=user, operator=user)
        key = uuid.uuid4()
        evaluated = Barrier(2, timeout=10)

        def evaluate_together(parsed, *, horizon):
            result = evaluate(parsed, horizon=horizon)
            evaluated.wait()
            return result

        def calculate():
            connections.close_all()
            try:
                current_user = get_user_model().objects.get(pk=user.pk)
                current_dataset = ResearchDataset.objects.get(pk=dataset.pk)
                run, created = run_evaluation(
                    owner=current_user, dataset=current_dataset, horizon=5, idempotency_key=key
                )
                return run.id, created, run.result
            finally:
                connections.close_all()

        with patch("research.quant.evaluate", side_effect=evaluate_together):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: calculate(), range(2)))
        self.assertEqual(results[0][0], results[1][0])
        self.assertEqual(sum(created for _, created, _ in results), 1)
        self.assertEqual(results[0][2], results[1][2])
        self.assertEqual(ResearchRun.objects.count(), 1)
