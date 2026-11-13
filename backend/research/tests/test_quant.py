import hashlib
import json
import math
import unittest
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from functools import lru_cache

import exchange_calendars

from research.quant import DatasetError, evaluate, parse_dataset
from research.quant.dataset import canonical_json
from research.quant.fixtures import make_fixture_payload

IMPORT_NOW = datetime(2026, 11, 6, 23, 59, tzinfo=UTC)


@lru_cache(maxsize=8)
def _calendar(start: str = "2024-01-02", end: str = "2024-12-31"):
    return exchange_calendars.get_calendar("XNYS", start=start, end=end)


def _calendar_sessions(start: str = "2024-01-02", end: str = "2024-12-31") -> list:
    calendar = _calendar(start, end)
    return list(calendar.sessions_in_range(start, end))


def _payload(
    close_values: list[float],
    *,
    sessions: list | None = None,
    split_ratios: dict[int, float] | None = None,
    dividends: dict[int, float] | None = None,
    data_kind: str = "synthetic_fixture",
) -> dict:
    if sessions is None:
        sessions = _calendar_sessions()[: len(close_values)]
    calendar = _calendar(
        start=sessions[0].date().isoformat(),
        end=(sessions[-1].date() + timedelta(days=20)).isoformat(),
    )
    split_ratios = split_ratios or {}
    dividends = dividends or {}
    observations = []
    for index, (session, close) in enumerate(zip(sessions, close_values)):
        close_at = calendar.session_close(session).to_pydatetime()
        observations.append(
            {
                "session": session.date().isoformat(),
                "close": close,
                "available_at": (close_at + timedelta(minutes=30)).isoformat(),
                "split_ratio": split_ratios.get(index, 1.0),
                "cash_dividend": dividends.get(index, 0.0),
            }
        )
    source_id = "SYNTHETIC: local test data"
    license_reference = "SYNTHETIC: generated for tests; no market-data license"
    availability_evidence = "SYNTHETIC: generated at close plus 30 minutes"
    if data_kind == "historical":
        source_id = "operator-attested-archive-2024"
        license_reference = "Operator-attested internal research license"
        availability_evidence = "Operator-attested publication timestamp manifest"
    return {
        "schema_version": 1,
        "name": "Deterministic test series",
        "instrument_id": "xnys-jpm",
        "data_kind": data_kind,
        "source_id": source_id,
        "license_reference": license_reference,
        "availability_evidence": availability_evidence,
        "adjustment_basis": "raw_with_causal_splits",
        "calendar": "XNYS",
        "corporate_actions_complete": True,
        "issue_lag_minutes": 60,
        "observations": observations,
    }


def _linear_payload(count: int = 180, *, horizon_step: float = 1.0) -> dict:
    return _payload([100.0 + horizon_step * index for index in range(count)])


def _parsed(payload: dict):
    return parse_dataset(payload, now=IMPORT_NOW)


class QuantDatasetTests(unittest.TestCase):
    def test_fixture_is_deterministic_valid_and_immutable(self):
        payload = make_fixture_payload()
        self.assertEqual(payload, make_fixture_payload())
        self.assertEqual(payload["name"], "Synthetic pipeline fixture")
        self.assertTrue(160 <= len(payload["observations"]) <= 200)
        self.assertTrue(any(row["split_ratio"] != 1 for row in payload["observations"]))
        self.assertTrue(any(row["cash_dividend"] > 0 for row in payload["observations"]))
        self.assertIn("SYNTHETIC", payload["source_id"])
        self.assertIn("SYNTHETIC", payload["license_reference"])

        dataset = _parsed(payload)
        self.assertEqual(
            dataset.version,
            hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest(),
        )
        self.assertEqual(dataset.payload, payload)
        with self.assertRaises(TypeError):
            dataset.payload["name"] = "changed"
        with self.assertRaises(TypeError):
            dataset.payload["observations"][0]["close"] = -1

    def test_historical_results_are_descriptive_and_never_claim_performance(self):
        dataset = _parsed(_payload([100.0 + index for index in range(150)], data_kind="historical"))
        result = evaluate(dataset, horizon=1)
        self.assertEqual(result["evidence_kind"], "historical_walk_forward")
        self.assertFalse(result["empirical_performance_established"])
        self.assertTrue(any("descriptive only" in item for item in result["limitations"]))

    def test_historical_metadata_with_known_synthetic_markers_is_rejected(self):
        payload = _payload([100.0 + index for index in range(120)], data_kind="historical")
        payload["source_id"] = "SYNTHETIC: local fixture"
        with self.assertRaises(DatasetError):
            _parsed(payload)


class QuantEvaluationTests(unittest.TestCase):
    def test_last_close_mae_and_rmse_match_hand_calculation(self):
        result = evaluate(_parsed(_linear_payload()), horizon=1)
        aggregate = next(
            row
            for row in result["evaluation"]
            if row["model_id"] == "last_close" and row["partition"] == "test"
        )
        rows = [
            row
            for row in result["evaluation_rows"]
            if row["model_id"] == "last_close" and row["partition"] == "test"
        ]
        self.assertEqual(aggregate["n"], len(rows))
        self.assertEqual(aggregate["mae"], 1.0)
        self.assertEqual(aggregate["rmse"], 1.0)
        expected_return_errors = [1.0 / row["origin_value"] for row in rows]
        self.assertAlmostEqual(
            aggregate["return_mae"],
            math.fsum(expected_return_errors) / len(expected_return_errors),
        )
        self.assertAlmostEqual(
            aggregate["return_rmse"],
            math.sqrt(
                math.fsum(error**2 for error in expected_return_errors)
                / len(expected_return_errors)
            ),
        )
        self.assertEqual(aggregate["direction_confusion"][1][2], aggregate["n"])
        self.assertEqual(sum(map(sum, aggregate["direction_confusion"])), aggregate["n"])

    def test_historical_log_mean_projects_a_geometric_drift_reference_path(self):
        close_values = [100.0 * (1.05**index) for index in range(180)]
        result = evaluate(_parsed(_payload(close_values)), horizon=1)
        row = next(
            row
            for row in result["evaluation_rows"]
            if row["model_id"] == "historical_log_mean" and row["partition"] == "test"
        )
        self.assertAlmostEqual(row["predicted"], row["origin_value"] * 1.05, delta=1e-8)

    def test_horizon_five_last_close_error_is_five_dollars(self):
        result = evaluate(_parsed(_linear_payload()), horizon=5)
        test_metric = next(
            row
            for row in result["evaluation"]
            if row["model_id"] == "last_close" and row["partition"] == "test"
        )
        self.assertEqual(result["target"]["horizon_sessions"], 5)
        self.assertEqual(test_metric["mae"], 5.0)
        self.assertEqual(test_metric["rmse"], 5.0)

    def test_split_is_applied_causally_and_unsplit_drop_remains_a_price_loss(self):
        count = 180
        split_index = 150
        neutral = [100.0] * count
        split_ratios = {split_index: 2.0}
        raw_with_split = [
            value / (2.0 if index >= split_index else 1.0)
            for index, value in enumerate(neutral)
        ]
        split_payload = _payload(
            raw_with_split,
            split_ratios=split_ratios,
        )
        split_result = evaluate(_parsed(split_payload), horizon=1)
        split_row = next(
            row
            for row in split_result["evaluation_rows"]
            if row["model_id"] == "last_close"
            and row["target"] == split_payload["observations"][split_index]["session"]
        )
        self.assertEqual(split_row["origin_value"], 100.0)
        self.assertEqual(split_row["predicted"], 100.0)
        self.assertEqual(split_row["actual"], 100.0)

        unsplit_drop = [100.0 if index < split_index else 50.0 for index in range(count)]
        unsplit_result = evaluate(_parsed(_payload(unsplit_drop)), horizon=1)
        drop_row = next(
            row
            for row in unsplit_result["evaluation_rows"]
            if row["model_id"] == "last_close"
            and row["target"] == split_payload["observations"][split_index]["session"]
        )
        self.assertEqual(drop_row["predicted"], 100.0)
        self.assertEqual(drop_row["actual"], 50.0)

    def test_dividends_remain_metadata_and_are_excluded_from_price_features(self):
        count = 180
        payload = _payload([100.0] * count, dividends={150: 5.0})
        dataset = _parsed(payload)
        result = evaluate(dataset, horizon=1)
        self.assertEqual(dataset.payload["observations"][150]["cash_dividend"], 5.0)
        self.assertTrue(all(point["value"] == 100.0 for point in result["forecast"]["history"]))
        forecast = next(
            model for model in result["forecast"]["models"] if model["model_id"] == "last_close"
        )
        self.assertTrue(all(point["value"] == 100.0 for point in forecast["points"]))

    def test_fixed_target_partitions_share_targets_across_models(self):
        result = evaluate(_parsed(_linear_payload()), horizon=5)
        self.assertEqual(result["protocol"]["id"], "expanding-60-20-20-v1")
        self.assertEqual(result["protocol"]["configuration_trials"], 1)
        self.assertEqual(len(result["protocol"]["protocol_sha256"]), 64)
        row_sets = {}
        for model_id in ("last_close", "historical_log_mean"):
            row_sets[model_id] = {
                (row["partition"], row["origin"], row["target"], row["input_sha256"])
                for row in result["evaluation_rows"]
                if row["model_id"] == model_id
            }
        self.assertEqual(row_sets["last_close"], row_sets["historical_log_mean"])
        self.assertEqual(
            [row["partition"] for row in result["evaluation"]],
            ["validation", "test", "validation", "test"],
        )

    def test_forecast_uses_scheduled_sessions_dst_and_early_close_cutoff(self):
        calendar = _calendar(
            start="2024-01-02",
            end="2024-08-01",
        )
        sessions = list(calendar.sessions_in_range("2024-01-02", "2024-07-03"))[-120:]
        self.assertEqual(sessions[-1].date().isoformat(), "2024-07-03")
        payload = _payload([100.0 + index for index in range(120)], sessions=sessions)
        early_close_row = payload["observations"][-1]
        early_close = calendar.session_close("2024-07-03").to_pydatetime()
        early_close_row["available_at"] = (early_close + timedelta(minutes=60)).isoformat()

        result = evaluate(_parsed(payload), horizon=5)
        forecast = result["forecast"]
        self.assertEqual(forecast["origin"], "2024-07-03")
        self.assertEqual(forecast["information_cutoff"], "2024-07-03T18:00:00+00:00")
        model = next(item for item in forecast["models"] if item["model_id"] == "last_close")
        self.assertEqual(
            [point["time"] for point in model["points"]],
            [
                "2024-07-03",
                "2024-07-05",
                "2024-07-08",
                "2024-07-09",
                "2024-07-10",
                "2024-07-11",
            ],
        )
        self.assertIn(
            "2024-03-08T21:30:00+00:00",
            {row["available_at"] for row in _parsed(payload).payload["observations"]},
        )
        self.assertIn(
            "2024-03-11T20:30:00+00:00",
            {row["available_at"] for row in _parsed(payload).payload["observations"]},
        )

    def test_future_price_and_action_perturbations_do_not_change_earlier_inputs(self):
        original = _linear_payload()
        original_result = evaluate(_parsed(original), horizon=1)
        changed = deepcopy(original)
        first_changed_index = 165
        for index, observation in enumerate(changed["observations"]):
            if index >= first_changed_index:
                observation["close"] *= 1.4
                observation["cash_dividend"] = 3.0
                observation["split_ratio"] = 1.5 if index == first_changed_index else 1.0
        changed_result = evaluate(_parsed(changed), horizon=1)

        original_early = [
            row
            for row in original_result["evaluation_rows"]
            if row["model_id"] == "historical_log_mean"
            and row["origin"] < original["observations"][first_changed_index]["session"]
        ]
        changed_rows = {
            (row["origin"], row["target"]): row
            for row in changed_result["evaluation_rows"]
            if row["model_id"] == "historical_log_mean"
        }
        self.assertTrue(original_early)
        for row in original_early:
            changed_row = changed_rows[(row["origin"], row["target"])]
            self.assertEqual(row["predicted"], changed_row["predicted"])
            self.assertEqual(row["input_sha256"], changed_row["input_sha256"])

    def test_replay_is_deterministic_and_result_is_finite_json(self):
        dataset = _parsed(make_fixture_payload())
        first = evaluate(dataset, horizon=5)
        second = evaluate(dataset, horizon=5)
        self.assertEqual(first, second)
        self.assertFalse(first["empirical_performance_established"])
        self.assertEqual(
            json.dumps(first, sort_keys=True, allow_nan=False),
            json.dumps(second, sort_keys=True, allow_nan=False),
        )
        self.assertEqual(len(first["forecast"]["history"]), 80)

    def test_invalid_horizons_are_rejected(self):
        dataset = _parsed(_linear_payload())
        for horizon in (0, 2, 5.0, True, "1"):
            with self.subTest(horizon=horizon), self.assertRaises(DatasetError):
                evaluate(dataset, horizon=horizon)


class QuantValidationTests(unittest.TestCase):
    def test_observation_count_is_bounded_from_120_through_1500(self):
        too_few = _payload([100.0 + index for index in range(119)])
        with self.assertRaises(DatasetError):
            _parsed(too_few)

        sessions = _calendar_sessions("2018-01-02", "2024-12-31")[:1501]
        too_many = _payload(
            [100.0 + index for index in range(1501)],
            sessions=sessions,
        )
        with self.assertRaises(DatasetError):
            _parsed(too_many)
        too_many["observations"].pop()
        self.assertEqual(len(_parsed(too_many).payload["observations"]), 1500)

    def test_missing_duplicate_and_unsorted_sessions_are_rejected(self):
        valid = _linear_payload()
        missing = deepcopy(valid)
        missing["observations"].pop(40)
        duplicate = deepcopy(valid)
        duplicate["observations"][40]["session"] = duplicate["observations"][39]["session"]
        unsorted = deepcopy(valid)
        unsorted["observations"][40], unsorted["observations"][41] = (
            unsorted["observations"][41],
            unsorted["observations"][40],
        )
        for changed in (missing, duplicate, unsorted):
            with self.subTest(case=changed), self.assertRaises(DatasetError):
                _parsed(changed)

    def test_boolean_and_nonfinite_numbers_are_rejected(self):
        mutations = [
            ("close", True),
            ("close", float("nan")),
            ("split_ratio", False),
            ("split_ratio", float("inf")),
            ("cash_dividend", float("-inf")),
        ]
        for field, value in mutations:
            payload = _linear_payload()
            payload["observations"][70][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(DatasetError):
                _parsed(payload)

    def test_boolean_schema_and_issue_lag_values_are_rejected(self):
        for field, value in (("schema_version", True), ("issue_lag_minutes", True)):
            payload = _linear_payload()
            payload[field] = value
            with self.subTest(field=field), self.assertRaises(DatasetError):
                _parsed(payload)

    def test_invalid_metadata_adjusted_basis_and_non_xnys_instrument_are_rejected(self):
        mutations = [
            ("adjustment_basis", "provider_adjusted"),
            ("instrument_id", "xnas-aapl"),
            ("calendar", "NASDAQ"),
            ("corporate_actions_complete", False),
            ("issue_lag_minutes", 30),
        ]
        for field, value in mutations:
            payload = _linear_payload()
            payload[field] = value
            with self.subTest(field=field), self.assertRaises(DatasetError):
                _parsed(payload)
        payload = _linear_payload()
        payload["unexpected"] = "extra"
        with self.assertRaises(DatasetError):
            _parsed(payload)

    def test_required_bounded_provenance_strings_are_validated(self):
        for field in ("name", "source_id", "license_reference", "availability_evidence"):
            missing = _linear_payload()
            del missing[field]
            with self.subTest(field=field), self.assertRaises(DatasetError):
                _parsed(missing)
            blank = _linear_payload()
            blank[field] = " "
            with self.subTest(field=field, blank=True), self.assertRaises(DatasetError):
                _parsed(blank)
        oversized = _linear_payload()
        oversized["availability_evidence"] = "x" * 1025
        with self.assertRaises(DatasetError):
            _parsed(oversized)

    def test_first_split_ratio_must_define_initial_share_units(self):
        payload = _linear_payload()
        payload["observations"][0]["split_ratio"] = 2.0
        with self.assertRaises(DatasetError):
            _parsed(payload)

    def test_availability_must_be_ordered_matured_and_within_the_fixed_cutoff(self):
        valid = _linear_payload()
        calendar = _calendar(
            start="2024-01-02",
            end="2024-12-31",
        )
        close = calendar.session_close(valid["observations"][50]["session"]).to_pydatetime()

        before_close = deepcopy(valid)
        before_close["observations"][50]["available_at"] = (
            close - timedelta(seconds=1)
        ).isoformat()
        after_cutoff = deepcopy(valid)
        after_cutoff["observations"][50]["available_at"] = (
            close + timedelta(minutes=60, seconds=1)
        ).isoformat()
        repeated = deepcopy(valid)
        repeated["observations"][50]["available_at"] = repeated["observations"][49]["available_at"]
        future = deepcopy(valid)
        future["observations"][-1]["available_at"] = (IMPORT_NOW + timedelta(seconds=1)).isoformat()

        for changed in (before_close, after_cutoff, repeated, future):
            with self.subTest(case=changed), self.assertRaises(DatasetError):
                _parsed(changed)
        with self.assertRaises(DatasetError):
            parse_dataset(valid, now=IMPORT_NOW.replace(tzinfo=None))
        last_close = calendar.session_close(valid["observations"][-1]["session"]).to_pydatetime()
        with self.assertRaises(DatasetError):
            parse_dataset(valid, now=last_close + timedelta(minutes=59))

    def test_exact_close_and_exact_sixty_minute_availability_are_valid(self):
        payload = _linear_payload()
        calendar = _calendar(
            start="2024-01-02",
            end="2024-12-31",
        )
        first_close = calendar.session_close(payload["observations"][0]["session"]).to_pydatetime()
        second_close = calendar.session_close(payload["observations"][1]["session"]).to_pydatetime()
        payload["observations"][0]["available_at"] = first_close.isoformat()
        payload["observations"][1]["available_at"] = (
            second_close + timedelta(minutes=60)
        ).isoformat()
        self.assertEqual(
            _parsed(payload).payload["observations"][1]["available_at"],
            (second_close + timedelta(minutes=60)).isoformat(),
        )

    def test_naive_and_malformed_available_timestamps_are_rejected(self):
        for timestamp in ("2024-02-01T16:00:00", "not-a-timestamp", "2024-02-01"):
            payload = _linear_payload()
            payload["observations"][10]["available_at"] = timestamp
            with self.subTest(timestamp=timestamp), self.assertRaises(DatasetError):
                _parsed(payload)

    def test_numerical_overflow_in_split_neutralization_is_rejected(self):
        payload = _linear_payload()
        payload["observations"][50]["split_ratio"] = 1e308
        payload["observations"][51]["split_ratio"] = 1e308
        with self.assertRaises(DatasetError):
            _parsed(payload)


if __name__ == "__main__":
    unittest.main()
