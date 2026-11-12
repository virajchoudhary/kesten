import csv
import hashlib
import io
from datetime import UTC, datetime

from research.quant.dataset import canonical_json, parse_dataset
from research.quant.fixtures import make_fixture_payload


def intake_arguments() -> dict:
    payload = make_fixture_payload()
    now = datetime(2026, 11, 6, 23, 59, tzinfo=UTC)
    dataset = parse_dataset(payload, now=now)
    metadata = {key: value for key, value in payload.items() if key != "observations"}
    csv_output = io.StringIO(newline="")
    writer = csv.writer(csv_output, lineterminator="\n")
    writer.writerow(("session", "close", "available_at", "split_ratio", "cash_dividend"))
    for row in payload["observations"]:
        writer.writerow(
            (
                row["session"],
                repr(row["close"]),
                row["available_at"],
                repr(row["split_ratio"]),
                repr(row["cash_dividend"]),
            )
        )
    csv_bytes = csv_output.getvalue().encode("utf-8")
    terms_bytes = b"SYNTHETIC terms snapshot; no market-data license or redistribution grant."
    availability_bytes = canonical_json(
        {
            "schema_version": 1,
            "source_id": metadata["source_id"],
            "observations": [
                {
                    "session": row["session"],
                    "available_at": row["available_at"],
                    "reference": f"SYNTHETIC publication evidence for {row['session']}",
                    "observation_sha256": hashlib.sha256(
                        canonical_json(row).encode("utf-8")
                    ).hexdigest(),
                }
                for row in dataset.payload["observations"]
            ],
        }
    ).encode("utf-8")
    source_record = {
        "schema_version": 1,
        "source_id": metadata["source_id"],
        "source_url": "https://example.invalid/synthetic-source",
        "acquired_at": now.isoformat(),
        "csv_sha256": hashlib.sha256(csv_bytes).hexdigest(),
        "terms_url": "https://example.invalid/synthetic-terms",
        "terms_sha256": hashlib.sha256(terms_bytes).hexdigest(),
        "availability_sha256": hashlib.sha256(availability_bytes).hexdigest(),
        "review_reference": "SYNTHETIC local review reference",
        "permissions": {
            "storage": True,
            "private_research": True,
            "backup": True,
            "internal_transfer": True,
            "redistribution": False,
        },
    }
    return {
        "csv_bytes": csv_bytes,
        "metadata": metadata,
        "source_record": source_record,
        "terms_bytes": terms_bytes,
        "availability_bytes": availability_bytes,
        "now": now,
    }
