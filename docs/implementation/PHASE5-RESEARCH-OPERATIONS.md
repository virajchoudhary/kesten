# Research intake operations

## Verify without touching existing data

From the repository root, using the existing workspace environment:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/check_research_intake.py
```

This creates new synthetic source files, a new isolated SQLite database, a backup and a restored database under `.local/research-intake-qualification`. It verifies the upgrade from `research.0001`, original dataset/run identities, the real CSV command, receipt verification and exact replay after restoration in a fresh process. Its summary is `intake-recovery.json`. UUID-named artifacts from earlier runs are retained. No genuine market data or model training is involved.

The original `backend/db.sqlite3` is never a target. Do not delete retained proof databases as part of startup or recovery.

## Prepare a lawful historical intake

First complete the [source review](PHASE5-RESEARCH-SOURCES.md). Do not use this procedure to relabel the test fixture. Select an isolated or explicitly approved application database through the existing environment configuration. Keep runtime and migrator PostgreSQL roles separate.

Back up the selected database with the existing `scripts/ops/recovery.py` workflow. Apply the additive migration with the configured migration role:

```powershell
.venv/Scripts/python.exe backend/manage.py migrate --noinput
```

This direct management command uses the environment already supplied to it. Inspect the configured target before invoking it. The convenience `scripts/research.py` launcher intentionally uses `.local/cadrisyn.sqlite3` through `development_environment()`; it does not honor an arbitrary production database target. Existing preview databases were not migrated during this phase.

Supply five files. CSV, metadata, source and availability inputs are each limited to 2,000,000 bytes. The terms snapshot is limited to 1,000,000 bytes. JSON is strict UTF-8 with unique object keys, valid Unicode and finite numbers.

1. The CSV has the exact ordered header `session,close,available_at,split_ratio,cash_dividend`. Supply every value on every row. No missing-session fill, inferred publication times or default actions are performed. Keep the 120-to-1,500-session v1 limits.
2. `metadata.json` contains the existing v1 dataset fields except `observations`. Its exact keys are `schema_version`, `name`, `instrument_id`, `data_kind`, `source_id`, `license_reference`, `availability_evidence`, `adjustment_basis`, `calendar`, `corporate_actions_complete` and `issue_lag_minutes`. Use the existing protocol definitions; an arbitrary provider field is rejected.
3. `source.json` follows the record below. Hash the original file bytes, including any BOM/newlines. Acquisition time must be aware, not in the future, and no earlier than the supplied observation availability times.
4. `terms.bin` is the exact retained terms snapshot whose digest appears in the source record. The software does not interpret its legal meaning.
5. `availability.json` contains ordered per-observation evidence as described below. Retain upstream support for each reference; the importer does not fetch or authenticate it.

The following is a schema illustration, not a dataset or legal attestation. Replace every descriptive placeholder with reviewed source facts before import.

```json
{
  "schema_version": 1,
  "source_id": "same-as-metadata",
  "source_url": "https://provider.example/archive",
  "acquired_at": "actual-aware-ISO-timestamp",
  "csv_sha256": "64-lowercase-hex-characters",
  "terms_url": "https://provider.example/terms",
  "terms_sha256": "64-lowercase-hex-characters",
  "availability_sha256": "64-lowercase-hex-characters",
  "review_reference": "internal-review-reference",
  "permissions": {
    "storage": true,
    "private_research": true,
    "backup": true,
    "internal_transfer": true,
    "redistribution": false
  }
}
```

All four internal permissions must be true to use this storage/recovery workflow. `redistribution` must be a boolean and may be false. HTTPS source/terms URLs cannot contain credentials, query strings or fragments. They are identifiers, not download instructions. Review and row references may be internal document references; URL references have the same restrictions.

The availability document has exactly `schema_version: 1`, `source_id` and `observations`. Every row has exactly `session`, `available_at`, `reference` and `observation_sha256`. Row order and count must match the parsed dataset. Hash the UTF-8 output of `research.quant.dataset.canonical_json(normalized_observation)` after the existing parser normalizes the row. This digest includes close, actions, session and availability. Hashing raw CSV row text is not equivalent. The synthetic test helper demonstrates serialization only; it is not a source of historical publication evidence.

## Import and verify

Under the configured runtime environment for the migrated target:

```powershell
.venv/Scripts/python.exe backend/manage.py import_research_csv `
  --csv path/to/prices.csv --metadata path/to/metadata.json `
  --source path/to/source.json --terms path/to/terms.bin `
  --availability path/to/availability.json `
  --owner account-name --approved-by staff-account-name --acknowledge-terms

.venv/Scripts/python.exe backend/manage.py verify_research_intake `
  --receipt returned-receipt-uuid --owner account-name
```

Import emits dataset/receipt UUIDs and versions, data kind, whether the numerical dataset was created and `independently_verified_source: false`. Store these identities with the experiment record. Repeating identical input is idempotent. Updating acquisition evidence creates a new receipt without changing an otherwise identical dataset or its runs.

Verification reads archived blobs and reconstructs both versions. It does not rewrite evidence or certify upstream authenticity. A mismatch is an integrity failure. Preserve the failing database and receipt, investigate the source of corruption, and restore into a new target using the documented recovery workflow. Do not edit a receipt to make verification pass.

The existing research application can select imported private datasets and run its fixed one/five-session references. It has no new source-acquisition screen. Until a real archive passes review, use only explicitly synthetic research checks and report empirical qualification as blocked.

## PostgreSQL qualification boundary

The retained Docker PostgreSQL instance was used through loopback port 15435. Only `test_cadrisyn` received the new migration. Runtime-role tests use that pre-provisioned database with `--keepdb`; runtime cannot create schemas. A test-only `TRUNCATE` grant for the new table supports Django test cleanup. Do not copy that grant to application databases. No role, volume or application database was recreated.

SQLite archived-byte backup/restore is currently exercised end to end by the reusable proof. PostgreSQL tests exercise bytea storage, migration and replay; a fresh PostgreSQL backup/restore drill containing the new receipt table remains a separate operational gate. Prior PostgreSQL recovery evidence is not relabeled as a current-schema drill.
