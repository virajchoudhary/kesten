import csv
import hashlib
import io
import json
import unittest

from research.ingestion import PreparedIntake, prepare_csv_intake, strict_json_loads
from research.quant import DatasetError, evaluate, parse_dataset
from research.quant.dataset import canonical_json
from research.quant.fixtures import make_fixture_payload
from research.tests.intake_fixtures import intake_arguments


def _rewrite_csv(arguments, mutate):
    rows = list(csv.reader(io.StringIO(arguments["csv_bytes"].decode("utf-8-sig"))))
    mutate(rows)
    output = io.StringIO(newline="")
    csv.writer(output, lineterminator="\n").writerows(rows)
    arguments["csv_bytes"] = output.getvalue().encode("utf-8")
    arguments["source_record"]["csv_sha256"] = hashlib.sha256(
        arguments["csv_bytes"]
    ).hexdigest()


def _rewrite_availability(arguments, mutate):
    evidence = json.loads(arguments["availability_bytes"])
    mutate(evidence)
    arguments["availability_bytes"] = canonical_json(evidence).encode("utf-8")
    arguments["source_record"]["availability_sha256"] = hashlib.sha256(
        arguments["availability_bytes"]
    ).hexdigest()


class StrictJsonTests(unittest.TestCase):
    def test_rejects_duplicate_members_at_root_and_nested_depth(self):
        for raw in (b'{"value":1,"value":2}', b'{"outer":{"value":1,"value":2}}'):
            with self.subTest(raw=raw), self.assertRaises(DatasetError):
                strict_json_loads(raw)

    def test_rejects_malformed_utf8_nonfinite_values_and_oversize_input(self):
        for raw in (
            b"\xff",
            b'{"value":NaN}',
            b'{"value":1e999}',
            b'"\\ud800"',
        ):
            with self.subTest(raw=raw), self.assertRaises(DatasetError):
                strict_json_loads(raw)
        with self.assertRaises(DatasetError):
            strict_json_loads(b"{}", max_bytes=1)


class CsvIntakeTests(unittest.TestCase):
    def test_preserves_v1_dataset_version_and_horizon_results(self):
        arguments = intake_arguments()
        original = parse_dataset(make_fixture_payload(), now=arguments["now"])
        prepared = prepare_csv_intake(**arguments)

        self.assertIsInstance(prepared, PreparedIntake)
        self.assertEqual(prepared.dataset.version, original.version)
        for horizon in (1, 5):
            self.assertEqual(
                evaluate(prepared.dataset, horizon=horizon),
                evaluate(original, horizon=horizon),
            )

    def test_rejects_metadata_headers_duplicate_sessions_and_missing_actions(self):
        arguments = intake_arguments()
        arguments["metadata"]["observations"] = []
        with self.assertRaises(DatasetError):
            prepare_csv_intake(**arguments)

        for change in (
            lambda rows: rows[0].__setitem__(0, "date"),
            lambda rows: rows[0].__setitem__(1, "session"),
            lambda rows: rows[2].__setitem__(0, rows[1][0]),
        ):
            arguments = intake_arguments()
            _rewrite_csv(arguments, change)
            with self.subTest(change=change), self.assertRaises(DatasetError):
                prepare_csv_intake(**arguments)

        for column in (3, 4):
            arguments = intake_arguments()
            _rewrite_csv(arguments, lambda rows: rows[1].__setitem__(column, ""))
            with self.subTest(column=column), self.assertRaises(DatasetError):
                prepare_csv_intake(**arguments)

    def test_rejects_malformed_csv_empty_records_and_more_than_1500_rows(self):
        arguments = intake_arguments()
        _rewrite_csv(arguments, lambda rows: rows.insert(2, []))
        with self.assertRaises(DatasetError):
            prepare_csv_intake(**arguments)

        arguments = intake_arguments()
        arguments["csv_bytes"] = (
            b"session,close,available_at,split_ratio,cash_dividend\n"
            b'"unterminated'
        )
        arguments["source_record"]["csv_sha256"] = hashlib.sha256(
            arguments["csv_bytes"]
        ).hexdigest()
        with self.assertRaises(DatasetError):
            prepare_csv_intake(**arguments)

        arguments = intake_arguments()
        _rewrite_csv(arguments, lambda rows: rows.extend([rows[-1].copy()] * 1321))
        with self.assertRaises(DatasetError):
            prepare_csv_intake(**arguments)

    def test_rejects_hash_mismatches_and_false_internal_permissions(self):
        for terms in (b"", b" \r\n\t"):
            arguments = intake_arguments()
            arguments["terms_bytes"] = terms
            arguments["source_record"]["terms_sha256"] = hashlib.sha256(terms).hexdigest()
            with self.subTest(terms=terms), self.assertRaises(DatasetError):
                prepare_csv_intake(**arguments)

        for field in ("csv_sha256", "terms_sha256", "availability_sha256"):
            arguments = intake_arguments()
            arguments["source_record"][field] = "0" * 64
            with self.subTest(field=field), self.assertRaises(DatasetError):
                prepare_csv_intake(**arguments)

        for permission in ("storage", "private_research", "backup", "internal_transfer"):
            arguments = intake_arguments()
            arguments["source_record"]["permissions"][permission] = False
            with self.subTest(permission=permission), self.assertRaises(DatasetError):
                prepare_csv_intake(**arguments)

        arguments = intake_arguments()
        arguments["source_record"]["source_id"] = "SYNTHETIC: different source"
        with self.assertRaises(DatasetError):
            prepare_csv_intake(**arguments)

        prepared = prepare_csv_intake(**intake_arguments())
        redistribution = json.loads(prepared.receipt_json)["source"]["permissions"][
            "redistribution"
        ]
        self.assertFalse(redistribution)

    def test_rejects_future_or_retrospective_acquisition_and_missing_publication_evidence(self):
        arguments = intake_arguments()
        arguments["source_record"]["acquired_at"] = "2026-11-07T00:00:00Z"
        with self.assertRaises(DatasetError):
            prepare_csv_intake(**arguments)

        arguments = intake_arguments()
        arguments["source_record"]["acquired_at"] = "2023-01-01T00:00:00Z"
        with self.assertRaises(DatasetError):
            prepare_csv_intake(**arguments)

        arguments = intake_arguments()
        arguments["metadata"]["availability_evidence"] = ""
        with self.assertRaises(DatasetError):
            prepare_csv_intake(**arguments)

        arguments = intake_arguments()
        _rewrite_availability(
            arguments,
            lambda evidence: evidence["observations"][0].__setitem__("reference", ""),
        )
        with self.assertRaises(DatasetError):
            prepare_csv_intake(**arguments)

    def test_rejects_availability_source_session_time_and_reference_mismatches(self):
        mutations = (
            lambda evidence: evidence.__setitem__("source_id", "SYNTHETIC: another source"),
            lambda evidence: evidence["observations"][0].__setitem__(
                "session", "2024-01-03"
            ),
            lambda evidence: evidence["observations"][0].__setitem__(
                "available_at", "2024-01-02T22:00:00Z"
            ),
            lambda evidence: evidence["observations"][0].__setitem__(
                "reference", "https://example.invalid/evidence?token=secret"
            ),
            lambda evidence: evidence["observations"][0].__setitem__(
                "observation_sha256", "0" * 64
            ),
        )
        for change in mutations:
            arguments = intake_arguments()
            _rewrite_availability(arguments, change)
            with self.subTest(change=change), self.assertRaises(DatasetError):
                prepare_csv_intake(**arguments)

    def test_rejects_stale_pit_proof_after_close_or_action_revision(self):
        for row_index, column, replacement in (
            (1, 1, "123.45"),
            (2, 3, "1.5"),
            (2, 4, "0.75"),
        ):
            arguments = intake_arguments()
            _rewrite_csv(
                arguments,
                lambda rows, row_index=row_index, column=column, replacement=replacement: rows[
                    row_index
                ].__setitem__(
                    column, replacement
                ),
            )
            with self.subTest(column=column), self.assertRaises(DatasetError):
                prepare_csv_intake(**arguments)

    def test_source_byte_identity_changes_receipt_version_even_when_dataset_is_identical(self):
        first_arguments = intake_arguments()
        first = prepare_csv_intake(**first_arguments)

        second_arguments = intake_arguments()
        second_arguments["csv_bytes"] = b"\xef\xbb\xbf" + second_arguments["csv_bytes"]
        second_arguments["source_record"]["csv_sha256"] = hashlib.sha256(
            second_arguments["csv_bytes"]
        ).hexdigest()
        second = prepare_csv_intake(**second_arguments)

        self.assertEqual(first.dataset.version, second.dataset.version)
        self.assertNotEqual(first.csv_bytes, second.csv_bytes)
        self.assertNotEqual(first.receipt_json, second.receipt_json)
        self.assertNotEqual(first.version, second.version)

    def test_receipt_is_canonical_and_hashes_all_supplied_bytes(self):
        arguments = intake_arguments()
        prepared = prepare_csv_intake(**arguments)
        receipt = json.loads(prepared.receipt_json)

        self.assertEqual(prepared.receipt_json, canonical_json(receipt))
        self.assertEqual(
            prepared.version,
            hashlib.sha256(prepared.receipt_json.encode()).hexdigest(),
        )
        self.assertEqual(receipt["adapter_id"], "canonical-daily-close-csv-v1")
        self.assertEqual(receipt["source_attestation"], "operator_attested")
        self.assertFalse(receipt["independently_verified_source"])
        self.assertEqual(receipt["observation_count"], len(make_fixture_payload()["observations"]))
        self.assertIn("not entitlement or point-in-time authenticity", receipt["limitation"])
        self.assertEqual(prepared.csv_bytes, arguments["csv_bytes"])
        self.assertEqual(prepared.terms_bytes, arguments["terms_bytes"])
        self.assertEqual(prepared.availability_bytes, arguments["availability_bytes"])

    def test_rejects_bad_urls_and_rights_schema(self):
        for url in (
            "http://example.invalid/source",
            "https://user:pass@example.invalid/source",
            "https://example.invalid/source?key=value",
            "https://example.invalid/source#fragment",
        ):
            arguments = intake_arguments()
            arguments["source_record"]["source_url"] = url
            with self.subTest(url=url), self.assertRaises(DatasetError):
                prepare_csv_intake(**arguments)

        arguments = intake_arguments()
        arguments["source_record"]["permissions"]["unknown"] = True
        with self.assertRaises(DatasetError):
            prepare_csv_intake(**arguments)

    def test_all_invalid_inputs_raise_dataset_error(self):
        arguments = intake_arguments()
        arguments["availability_bytes"] = b'{"schema_version":1}'
        with self.assertRaises(DatasetError):
            prepare_csv_intake(**arguments)

        arguments = intake_arguments()
        arguments["csv_bytes"] = b"\xff"
        arguments["source_record"]["csv_sha256"] = hashlib.sha256(
            arguments["csv_bytes"]
        ).hexdigest()
        with self.assertRaises(DatasetError):
            prepare_csv_intake(**arguments)

