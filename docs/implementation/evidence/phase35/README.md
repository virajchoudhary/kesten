# Phase 3.5 evidence

Recorded on 2026-11-07 for the current code from `8817617`. [Results](../../PHASE35.md), [operations](../../PHASE35-OPERATIONS.md) and [historical-data qualification](../../HISTORICAL-DATA-QUALIFICATION.md) define scope. Console whitespace is normalized; original captures, secrets, dumps and disposable accounts remain ignored under `.local/phase35/`. No actual market observations are included.

## Final passing gates

- `host-recovery.json` records the targeted bootstrap-directory repair, live engine version and retention of all 15 previously visible volume names. It makes no VHD-byte-integrity claim.
- `backend-baseline.txt` is the source SQLite baseline with four explicit skips. `postgres-host-tests.txt` and `postgres-container-tests.txt` each pass all 120 supported tests with no skips. The latter runs inside the Linux image. They include the same 24 numerical checks; they are not 240 distinct test cases.
- `api-build.txt`, `web-build.txt`, `api-start.txt` and `stack-start.txt` record current builds, one-shot migrations and healthy services. `image-source-match.json` compares all 112 packaged Python/requirements files and declares the intentional metadata/environment exclusions. `compose-equivalence.json` proves the committed qualification override equals the exercised private one.
- `research-migration-upgrade.json` uses another new empty PostgreSQL database to create a pre-research schema, compare the two retained account/watchlist fixture objects through adding research and repeating migration, then verify new synthetic storage. `runtime-role.json` records actual constrained privileges and rejected temporary-table creation.
- `web-unit.txt`, `web-types.txt` and `web-lint.txt` pass. The optimized production frontend build is in `web-build.txt`.
- `browser.txt` passes six Chromium scenarios through the actual container gateway: four actual API journeys and two isolated account UI cases. `http-smoke.json` passes 19 actual checks, including synchronized 200/200 sign-ins and saved synthetic research.
- `source-replay.json` verifies exact source-image replay at horizons 1 and 5. `postgres-backup.txt` and `postgres-restore.txt` record a real PostgreSQL custom-format archive and separate-empty-target restoration. `recovery-verification.json` compares all fields of 23 fixture objects and replays both horizons. `restore-http.json` verifies fresh sessions/readiness, exact source/result-response equality and outsider 404 isolation. Backup bytes/manifests containing account state are intentionally not committed.
- `workspace-transfer.json` verifies all 87 copied fixture objects from a read-only SQLite backup against a separate empty PostgreSQL target. It explicitly excludes active sessions; this transfer is independent of the PostgreSQL restore.
- `legacy-tests.txt` passes 23 supported offline checks. Recovery-unit receipts pass 17 on Windows and 17 in Linux. Transfer, profile and client receipts pass 7, 2 and 2 respectively.
- `preservation-before.json` and `preservation-final.json` verify the original database and all 496 runtime and 17 research artifact hashes.
- `local-data-inventory.json` finds only synthetic research/demo chart data. `data-review.json` is the independent read-only source qualification, with the worker's own task context reporting Azure GPT-6 Luna at Max effort. The worker did not acquire data or run tests.

- `engineering-review.json` records the independent PARTIAL finding, including its restricted runtime access. The two documentation issues were corrected, and `documented-fixture-setup.txt` executes the exact guide command. `availability-final.json` is fresh authorized parent runtime evidence after that review. The gateway has HTTP probes rather than a declared Docker healthcheck; migration is completed, not a running healthchecked service. `runtime-dependencies.txt` records the packaged dependency check.

- `documentation-acceptance.json` accepts the two working-tree corrections while retaining the earlier-index snapshot failure. `index-correction-verification.json` verifies restaged content identity. `documented-fixture-setup.json` binds the actual stdin command/code hash and exit code 0. This is bounded documentation acceptance, not another global runtime review.

## Failed setup probes retained

`browser-missing-binary.txt` failed before page load because the chosen cache lacked the exact browser revision. The final browser receipt passes after an isolated matching Chromium installation. `linux-recovery-unit.txt` lacked `/app` on PYTHONPATH; `linux-recovery-unit-retry.txt` passes. `postgres-restore-invocation-before.txt` rejected an unsupported Compose CLI flag before touching the target; the supported Docker command completes restoration. These files are failure history, not additional passing gates. The initial excluded Windows port and local safety-hook rejection are described in the implementation record.

## Reproduction probes

`verify_upgrade.py`, `prepare_recovery.py` and `verify_restore.py` are the exact small probes piped into the current API image interpreter after explicit isolated database setup. They are evidence/verification tools, not new application endpoints or market-data adapters. Use only the named new qualification targets under normal Python execution, never an existing production store or optimized Python with disabled assertions. `verify_upgrade.py` refuses nonempty targets. The recovery comparison reads the non-secret `source-replay.json` summary mounted read-only at `/verification/source-summary.json`; the underlying raw fixtures/dumps remain private. [Operations](../../PHASE35-OPERATIONS.md) explains migration/runtime roles and backup/restore prerequisites.

Infrastructure passes locally. No qualified historical dataset, empirical forecasting performance, advanced-model promotion, hosted CI, production deployment, penetration test or certification is claimed. Strict replay matches the pinned environment; cross-platform bitwise identity is not claimed.
