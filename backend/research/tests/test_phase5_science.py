import hashlib
from copy import deepcopy
from datetime import UTC, datetime

from django.test import SimpleTestCase

from research.quant import evaluate, parse_dataset
from research.quant.dataset import canonical_json
from research.quant.fixtures import make_fixture_payload


class Phase5ScientificContractTests(SimpleTestCase):
    def parse(self, payload):
        return parse_dataset(payload, now=datetime(2026, 11, 9, tzinfo=UTC))

    def test_frozen_synthetic_numerical_contract_is_unchanged(self):
        dataset = self.parse(make_fixture_payload())
        expected = {
            1: "9a45a5cca4ce69b11d0ae494f23679a278057ae61b995cf2957d7ea378c19e50",
            5: "995a224ce3925f972ca224ece6f548d45277ecdd364a50d13998b4649e5f33be",
        }
        self.assertEqual(dataset.version, "9203cba1c9d58f65505fc7c05120669be1829719c7d033d58ab8155387a47a94")
        for horizon, digest in expected.items():
            result = evaluate(dataset, horizon=horizon)
            self.assertEqual(hashlib.sha256(canonical_json(result).encode()).hexdigest(), digest)
            self.assertFalse(result["empirical_performance_established"])

    def test_both_references_ignore_future_prices_actions_and_labels(self):
        payload = make_fixture_payload()
        first_changed = 125
        changed = deepcopy(payload)
        for index, row in enumerate(changed["observations"]):
            if index >= first_changed:
                row["close"] *= 1.4
                row["cash_dividend"] += 3
                row["split_ratio"] = 1.5 if index == first_changed else 1
        cutoff = payload["observations"][first_changed]["session"]
        for horizon in [1, 5]:
            before = evaluate(self.parse(payload), horizon=horizon)
            after = evaluate(self.parse(changed), horizon=horizon)
            rows = {(r["model_id"], r["origin"], r["target"]): r for r in after["evaluation_rows"]}
            compared = 0
            changed_labels = 0
            for row in before["evaluation_rows"]:
                if row["origin"] >= cutoff:
                    continue
                revised = rows[(row["model_id"], row["origin"], row["target"])]
                self.assertEqual(row["predicted"], revised["predicted"])
                self.assertEqual(row["input_sha256"], revised["input_sha256"])
                self.assertEqual(row["information_cutoff"], revised["information_cutoff"])
                compared += 1
                changed_labels += row["actual"] != revised["actual"]
            self.assertGreater(compared, 0)
            self.assertGreater(changed_labels, 0)
            self.assertEqual(before["protocol"]["configuration_trials"], 1)
