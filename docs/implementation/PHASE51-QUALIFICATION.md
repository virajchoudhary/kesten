# Phase 5.1 container and recovery qualification

The committed application at `348d78ecad3a5a01f72299975e7f80f781f56a27` has passed current-image builds, a PostgreSQL intake-schema upgrade, actual backup/restore, replay and restored-application browser integration. Historical forecasting qualification remains blocked. All research in this verification is the existing explicit synthetic fixture; market charts use Demo data.

## Source and environment boundary

Both images were built from an immutable `git archive` of that revision. The 24 unrelated dirty/untracked paths were excluded and preserved, including pre-existing release-engineering changes. The Phase 5.1 changes add verification tools, browser-driver corrections and documentation. They do not change backend application modules, numerical code, runtime UI, dependencies or contracts.

The new Compose project is `kerquant-phase51-62a1f1`. Its PostgreSQL, Redis and static volumes are separate from retained projects. Test access is loopback-only on database port 15451, cache port 16391 and gateway port 8091. The profile is an isolated development qualification environment, not a production deployment or production-profile acceptance.

The [image receipt](evidence/phase51/images.json) records actual image IDs, source labels, non-root users and source-archive SHA-256. Images remain local. A future application-code change requires a new source-bound build and acceptance run; these receipts do not qualify arbitrary newer code or the excluded dirty work.

## Verified results

| Gate | Current result |
| --- | --- |
| API and Next.js application image builds | Both passed from the frozen source; the Next.js build also generated API types. |
| API-image dependency consistency | `pip check` passed. |
| PostgreSQL upgrade | Created saved synthetic dataset/runs under `research.0001`, applied `0002_researchintakereceipt` with the migrator, checked the migration record and retained original dataset/run IDs, versions and result hashes. |
| Intake with runtime role | Actual CSV command stored one receipt with exact CSV, terms and availability bytes. Dataset identity was reused. |
| Current-image backend selection | 154 tests passed against the separately provisioned `test_cadrisyn` database, with zero skips. The earlier 156-test working-tree run included two pre-existing untracked tests absent from the committed archive. |
| Actual PostgreSQL backup/restore | Existing recovery CLI created a custom-format dump and manifest, then restored into a separate empty database using the migrator. All 27 application-table row counts/hashes, intake bytes/identities and 13 saved run replays matched. Both horizons were present. |
| Source preservation | The complete source snapshot still matched after restoration. It was not served for the restored browser pass. |
| Recovery refusal safeguards | Actual CLI refused the source endpoint and a populated target, both with exit code 2 before restore. |
| Runtime privileges | Role flags, database CREATE/TEMP, writable user schemas, role membership and catalog-object ownership checks passed. Restore received DML/sequence grants, without application TRUNCATE or CREATE grants. |
| Recovery unit/guard checks | 23 tests passed, including five new qualification checks. Four additional transactional PostgreSQL tests exercised the actual privilege SQL. |
| Real Chromium against restored database | All 16 existing workflows passed in one final run. This includes real account activation/reset, private research isolation across tabs/accounts, watchlists, charts, comparison, synthetic exports and replay. Two existing account UI tests use stubs; they are not counted as additional live backend lifecycle evidence. |
| TypeScript and lint | Passed after browser-driver corrections. |

The source-backup snapshot comparison occurred before browser activity wrote new disposable records into the restored database. Later test writes are expected on that restored target. The original source database remains frozen and separate.

## Findings corrected

Review found that partial privilege enumeration missed database-level CREATE, role-switch membership and ownership outside relations. The final probe checks the simpler dedicated-role invariant. The runtime must belong to no other roles and own no catalog objects in the database or shared catalogs. It uses `pg_auth_members` and PostgreSQL's `pg_shdepend` ownership dependencies, alongside explicit role/CREATE/TEMP/schema checks. This corrected verification gaps; no configured application-role overprivilege was found.

Four real PostgreSQL tests verify a benign role, NOINHERIT membership with SET TRUE, routine ownership and custom-type ownership. Every role/schema/object used by these tests is newly created in a transaction and rolled back. Existing runtime roles and application data are not altered. The final qualification snapshot has schema version 2; it is an engineering proof version, separate from the unchanged research protocol and dataset versions. A fresh second restore target validates that final proof without overwriting the first restored database used for browser acceptance.

An empty account exposed an ambiguous browser locator. The chart search and watchlist both have an Add instrument control. The market workflow now selects the watchlist region explicitly and passed with an empty watchlist. The populated-terminal tests receive an explicit three-instrument Demo watchlist fixture rather than relying on old user state.

Rapid full-suite logins triggered the unchanged server throttles. The research browser driver now validates a server Retry-After of 1 to 60 seconds and retries once after that cooldown. It checks HTTP status before parsing the session. No application limit, permission, CSRF requirement or security assertion was relaxed. Separate Redis logical databases isolate acceptance attempts without clearing earlier cache databases.

## Host interruptions and recovery

Docker Desktop's automatic updater interrupted the first web build. The recorded engine version changed from 29.9.2 to 29.9.3. The retry built successfully. Desktop subsequently exited gracefully during a browser run; that exit's cause was not established. Those incomplete/failed attempts are retained and do not count as passing runs.

A normal hidden Desktop start recovered the engine. PostgreSQL completed its durable filesystem synchronization before qualification resumed. No reset, volume deletion, storage relocation, WSL reset or durability-setting change was used. Retained Kerquant database/cache containers were returned to their prior running state after the host interruptions. Local host stability and unattended maintenance remain operational concerns, separate from the application's successful recovery proof.

## Evidence and remaining gates

[Verification receipt](evidence/phase51/verification.json), [independent review](evidence/phase51/independent-review.md), [operations](PHASE51-OPERATIONS.md) and [historical-source review](PHASE51-MARKET-DATA.md) contain the scoped results and instructions. Raw dumps, private credentials, account tokens and complete database copies remain ignored under `.local/phase51`.

No genuine historical archive was acquired or qualified. No empirical accuracy, calibrated uncertainty, model promotion or investment-performance conclusion follows from these tests. Production-profile/TLS acceptance, hosted CI, signed image provenance and licensed-data entitlements are not established by this local development-profile run. No push, merge, public deployment or purchase was performed.
