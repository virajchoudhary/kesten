# Phase 3.5 qualification record

Completed the feasible qualification on 2026-11-07 from `codex/cadrisyn-foundation` at `8817617`. Infrastructure acceptance passes locally. Empirical forecasting qualification remains blocked because no reviewed dataset meets the unchanged rights and point-in-time input contract. Cadrisyn remains a working name. No merge, deployment, data purchase, account purchase, model training or trading execution occurred.

## Changes and preservation

The application and numerical algorithms needed no correction during this phase. The new [qualification Compose profile](../../deploy/compose.qualification.yaml) records the exact isolated port/origin configuration exercised here. It leaves the default Compose profile unchanged. Source assessment, operational instructions and current receipts are added below. Existing original database, runtime files, research artifacts and unrelated local modifications are preserved.

The original `backend/db.sqlite3` remains outside commits with its pre-existing modification and unchanged recorded hash. All 496 protected runtime files and 17 recorded research artifact/progress files match their original hashes. Saved model ZIPs were not loaded or rewritten. The active SQLite workspace was read through a read-only backup for a separate-target transfer; no migration or password change was made to that source. Disposable accounts and synthetic results were created only in new PostgreSQL qualification databases. Prior browser-token files were retained under ignored `.local/phase35/previous-*` before preparing new disposable fixtures.

## Docker fault and targeted repair

The failure occurred before any application container could start. Docker Desktop 4.98.0 reported missing `docker-desktop` registration and an existing-path error while creating `%LOCALAPPDATA%\Docker\wsl\main`. WSL could execute Ubuntu. Inspection found the existing WSL storage root is a junction to `D:\Docker\wsl`, with its existing data VHD present and the `main` child absent.

A normal startup reproduced the error. Creating the child through the configured junction did not leave a usable directory. With Desktop stopped, creating only the missing empty `D:\Docker\wsl\main` directory through its real target and starting Desktop allowed its bootstrap distribution and engine to initialize. A further normal start completed engine readiness. This is observed recovery of a Desktop/WSL bootstrap-path problem, not proof of a particular Docker/Go defect or disk corruption.

No junction or WSL distribution was relocated, no VHD/volume was removed, no Docker factory reset/prune/reinstallation was performed, and no manual distro unregister/import was used. Docker created its own bootstrap VHD and used the existing data disk. Its normal startup/shutdown can write that disk, so no unchanged-VHD-bytes claim is made. The Windows helper-service start was denied, but the WSL engine subsequently ran without it; that service denial is not an outstanding application blocker. Existing unrelated containers restarted with Desktop and were not operated individually.

The engine/server API now responds and all previously visible volumes are retained. Docker's [WSL backend](https://docs.docker.com/desktop/features/wsl/) and [VM backup guidance](https://docs.docker.com/desktop/settings-and-maintenance/backup-and-restore/) support treating its data disk separately from application images. This host-specific repair is not an automatic storage repair command for other machines.

## Current evidence

The [evidence index](evidence/phase35/README.md) distinguishes failures of test setup from final results.

| Gate | Verified result |
| --- | --- |
| Source baseline | 120 backend tests, 116 pass and four PostgreSQL-only skips; matching OpenAPI and no missing migrations. Optional HSTS preload warning remains |
| PostgreSQL from Windows | All 120 supported backend tests pass with no skips, including account and research concurrency/isolation checks |
| Linux API image and PostgreSQL | All 120 pass with no skips; 112 packaged Python/requirements files match the checkout; packaged dependency check passes |
| Container startup | Current API and Next images build. API/web/database/cache pass Docker healthchecks, gateway HTTP probes pass, and one-shot migration exits 0 |
| Migration upgrade | Linux creates a pre-research schema in another new database, preserves all fields of two account/watchlist fixture objects through the research migration, repeats migration without changes, and accepts explicit synthetic research storage |
| Role boundary | Actual runtime role has no superuser, createdb, createrole, replication or bypass-RLS flags, public CREATE or database TEMP privilege. A temporary-table creation attempt is denied |
| Frontend | 44 unit tests pass, TypeScript/ESLint pass, and optimized Next container build passes |
| Browser | Six Chromium scenarios pass through the actual PostgreSQL-backed gateway: four real API journeys and two isolated account UI cases. Research includes five-session creation, provenance, reload, mobile geometry and private saved links |
| Actual HTTP | 19 smoke checks pass, including market/watchlist behavior, synthetic research persistence/idempotency, hostile-origin denial and synchronized 200/200 sign-ins/logouts |
| Backup/restore/replay | A PostgreSQL 17.11 custom-format dump restores only into a separate empty target. All fields of 23 fixture objects match; one- and five-session results replay exactly in Linux with matching source/lock/runtime/result evidence |
| Restored access | Fresh HTTP sign-in/logout and readiness pass. Both private result responses equal the source; a new outsider gets 404 for both and no datasets. Temporary restored API is stopped afterward |
| Workspace transfer | Read-only SQLite backup transfers 87 allowed fixture objects into a separate migrated PostgreSQL database with all copied fields equal; active sessions are not transferred |
| Existing tools/research | 23 offline legacy tests, 17 recovery-unit tests on each OS, seven transfer-unit tests, two profile-isolation tests and two client-safety tests pass |

The source and container test totals each include the same 24 numerical and 18 PostgreSQL-enabled research cases. They are separate execution environments, not 240 distinct tests. No synthetic MAE/RMSE is presented as empirical performance. Exact replay is qualified within the matching pinned execution environment, not across arbitrary Python/OS/library versions.

The first test port 55435 was rejected by Windows before database startup; verified free loopback port 15435 worked. Browser execution initially failed before page load because the selected cache lacked Chromium revision 1248; installing the locked package's matching browser into ignored workspace storage resolved it. A Linux recovery-unit invocation lacked `/app` on `PYTHONPATH`; its corrected invocation passes all 17. Compose `run` does not support Docker `run`'s secret `--env-file` option; separate-target recovery used the supported Docker command. A local safety hook blocked one combined verification call; a named retained container completed it without cleanup operations. These failures are not hidden or labelled as application successes.

## Historical data and model acceptance

[The source-by-source assessment](HISTORICAL-DATA-QUALIFICATION.md) covers Alpha Vantage, Tiingo, Nasdaq WIKI, NYSE, CRSP and Stooq, with primary links and access limitations. No source was accepted and no raw market data acquired. Thus there are no market raw-file hashes/acquisition dates, empirical error tables by asset/horizon, calibrated intervals or validated forecasting improvement to report. The local workspace contains only one synthetic fixture dataset and two demo snapshots.

The accepted methods remain numerical references: last-close persistence and the expanding historical-log-mean geometric path, at one/five sessions. The existing fixed chronological/walk-forward protocol and availability checks are unchanged. No new simple or complex model is promoted without observations that can support an empirical comparison. The preserved mean fallback, ARIMA/GARCH, BiLSTM/HPO and RL remain experimental and unpromoted for the [previous source-level reasons](PHASE3.md#model-disposition).

## Reproduce and operate

See [qualification operations](PHASE35-OPERATIONS.md). The current container entry point is `http://127.0.0.1:8085/app/research`, with `/app/markets` and `/app/account`. Existing local analyst credentials remain in ignored `.local/credentials.json`. The source preview on 3000/8000 remains separate. The default 8080 Compose configuration is preserved; the new qualification project uses 8085 to avoid older previews.

## Commit trail

- `1c1155a`: historical-source qualification findings, independent source review and local data inventory.
- The tested container qualification profile and operational/review evidence follow as a separate focused commit on the same branch. No application or quant module was rewritten.

## Independent acceptance

The independent engineering review returned PARTIAL for two documentation defects and its inability to access Docker/loopback from its restricted session. Both documented defects were corrected and the exact host-fixture command executed successfully. The parent reverified current service states and six HTTP probes with authorized access. [Review dispositions](REVIEW.md#phase-35-postgresql-recovery-and-data-qualification) preserve that distinction. A separate bounded reader accepted the two working-tree corrections; its earlier-index finding is closed by the final staged-content comparison. The raw verdicts remain recorded. The data reviewer accepted no dataset. These are independent context reviews, not a production certification.

## Remaining gates

Infrastructure is locally qualified; the Phase-three Docker/PostgreSQL execution blocker is resolved. Historical qualification remains blocked on rights-approved source bytes and independently supported original price/action availability. The parser and staff acknowledgement cannot authenticate external rights or publication assertions, and a normalized dataset hash/import time is not a raw acquisition receipt. No contract was weakened to manufacture acceptance.

Hosted CI was not run and nothing was pushed. This is a loopback HTTP development profile, not a production deployment. Production TLS/secrets/ingress, current image/OS vulnerability scanning, off-host encrypted backups/retention, recovery of post-backup security decisions, host/load/cost qualification, observability ownership and wider browser/accessibility coverage remain separate gates. Restoration proves data fidelity and fresh private access, not preservation of revocations made after a backup or an RPO/RTO. No production or empirical readiness PASS is claimed.
