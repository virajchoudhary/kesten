# Production foundation implementation

Completed locally on 2026-11-06 from `codex/cadrisyn-foundation` at `0b94770`. This is a tested private foundation. External production release remains blocked by the gates below. No merge, deployment, purchase, paid provider or public naming decision occurred.

## Delivered behavior

The existing Next.js -> same-origin Django session API -> workspace services boundary remains. Research settings, dependencies, quantitative modules and the original database remain separate. No scientific algorithm was rewritten or given a new performance claim.

PostgreSQL 17 runs actual migrations in a one-shot service before API readiness. A separately credentialed schema owner runs migrations; the runtime credential has table CRUD and sequence usage/read without permanent or temporary DDL. Readiness rejects privileged roles, database/schema/relation ownership and pending migrations. The retained-volume upgrade handles the baseline image's original superuser identity without deleting rows or erasing volumes.

Closed registration uses operator-issued invitations and resets, hashed one-use credentials, bounded expiry, password validation and transactional redemption. Users change passwords and revoke other sessions at `/app/account`. Session epochs invalidate stale sessions, including an already open workspace after reset. CSRF protects login and mutations. Private watchlists remain account-owned. Login cooldowns use the normalized account and trusted peer address; failures from one peer do not lock out another globally.

Provider policy is checked before cached observations. Demo and personal historical data have separate permissions, cache namespaces and immutable content identities. The Yahoo adapter requires personal-use acknowledgement and is blocked outside development. No licensed live provider is configured. Provider/cache failures return an unavailable state and never substitute synthetic prices. Validation rejects malformed, inconsistent, non-finite, excessive, unordered or future daily observations and corrupted cached content.

Safe JSON logs correlate request IDs without raw bodies, headers, query strings or exception text. Liveness is independent of database/cache readiness, including with a session cookie. Backup tools produce checksummed archives and require a separate empty restoration target. Workspace transfer snapshots SQLite read-only, refuses the research database, excludes restricted observations and unused account tokens, omits sessions, and compares copied fields before committing.

## Completed work units

- [x] Baseline, working-tree inspection and preservation receipts.
- [x] PostgreSQL migrations, restricted runtime role, new-volume startup and retained-volume upgrade.
- [x] Invitations, password lifecycle, session invalidation, CSRF and private-account isolation.
- [x] Provider policy, cache validation, safe errors, logging and health checks.
- [x] Windows/Linux recovery and actual PostgreSQL backup, restore and sign-in.
- [x] Typed frontend integration, optimized build, packaged browser acceptance and review corrections.
- [x] Focused local commits, reproducible operations and explicit release gates.

## Verification evidence

Receipts are under [evidence/phase2](evidence/phase2/README.md). Test counts are software evidence, not financial performance measurements.

| Gate | Observed result |
| --- | --- |
| Initial supported baseline | [29 tests pass](evidence/phase2/baseline.txt); optional HSTS preload warning |
| Final PostgreSQL suite | [78 pass, no skips](evidence/phase2/separated-postgres-tests.txt), on named persistent PostgreSQL with the restricted runtime role, including concurrency cases |
| SQLite/backend contract | [78 collected, 75 pass, 3 PostgreSQL-only skips](evidence/phase2/separated-backend.txt); contract matches, no pending model migrations, only `security.W021` in settings probe |
| Preserved research | [23 pass offline](evidence/phase2/legacy-tests.txt) through the preserved research interpreter |
| Frontend | [29 tests pass](evidence/phase2/web-unit.txt), [TypeScript](evidence/phase2/web-final-types.txt), [ESLint](evidence/phase2/web-final-lint.txt), [optimized build](evidence/phase2/web-webpack-build.txt) pass |
| Packaged browser | [5 Chromium scenarios pass](evidence/phase2/container-browser-final.txt) against the final stack; 3 actual API/database journeys and 2 stubbed UI-state scenarios |
| Gateway/API smoke | [13 checks pass](evidence/phase2/separated-http-smoke.json), including readiness, CSRF, watchlists, hostile origins, provenance and logout |
| Recovery units | [17 Windows](evidence/phase2/windows-recovery-tests.txt) and [17 Linux](evidence/phase2/linux-recovery-tests.txt) pass, including corrupt archives, unsafe targets and no-overwrite restore |
| Workspace transfer | [6 tests pass](evidence/phase2/workspace-migration-tests.txt); [20 objects copied](evidence/phase2/final-workspace-transfer.txt) into fresh PostgreSQL with every copied fixture field compared |
| Real PostgreSQL recovery | [Runtime-role backup](evidence/phase2/runtime-backup.txt), [migration-role restore](evidence/phase2/separated-restore.txt), [20-object comparison, readiness, sign-in, watchlist and logout](evidence/phase2/separated-recovery-verification.txt) pass |
| Privilege boundary | [Permanent/temp DDL denied; administrator/migrator credentials absent from API](evidence/phase2/runtime-role-verification.json) |
| Retained-volume upgrade | [Legacy superuser transition, preserved rows, DML/default grants, DDL denial, idempotence and restart pass](evidence/phase2/legacy-role-upgrade-v2.txt) on an independent disposable volume |
| Containers | Actual API/web builds, [separated-role startup](evidence/phase2/separated-startup.txt), [independent cold-volume startup](evidence/phase2/cold-startup.txt) pass; [47 packaged Python sources match](evidence/phase2/image-source-final.json) |
| Dependency outages | [Redis stop/restart](evidence/phase2/cache-recovery.json) gives readiness/bars 503, liveness 200, then recovery with session retained; [session-cookie liveness regression](evidence/phase2/liveness-regression-after.txt) passes after recorded failure |
| Package advisories | [npm](evidence/phase2/npm-audit.json) and [pinned workspace/Linux Python inputs](evidence/phase2/pip-audit-runtime.txt) report zero known advisories at check time; this is not an image/OS scan |
| Preservation | [496 runtime files and original database unchanged](evidence/phase2/preservation-final.json) |

The original `backend/db.sqlite3` remains the pre-existing dirty Git change, SHA-256 `93745BFC1A3149A0F77BBCDD1A50F712195750879F3FB313728AB9811F99715B`. It was never migrated, overwritten or staged. The separate `.local/cadrisyn.sqlite3` received schema migrations and disposable test accounts. The existing analyst password was retained and authenticated after transfer/restoration. Ignored backups, secrets, account links and model artifacts remain private.

## Findings resolved during execution

Independent reviews found account-wide lockout risk, missing invitation revocation, bearer-token transfer, runtime schema ownership and the retained-volume bootstrap assumption. Targeted corrections and evidence are recorded in [REVIEW.md](REVIEW.md). Durable revoking-operator attribution is a nonblocking audit enhancement.

The old Node image tag did not exist. Replacement Node and Python bases use verified digests. Two Windows Turbopack CSS-worker attempts failed, including outside the sandbox. Next's supported Webpack option built on Windows and Linux and is now explicit. A slow dependency-layer copy was replaced with a read-only build-stage dependency mount; standalone output remains.

One test attempt overlapped a parent-initiated database restart and ended with connection failures. The serialized final 78-test run supersedes it. A first named-volume CREATE DATABASE operation also crashed PostgreSQL and recovered; the cause was not established. Subsequent retained-volume, cold-start, restore and restart checks passed without disabling durability. Host/storage qualification remains a release gate. An initial research invocation used the core environment without PyTorch; the preserved research interpreter passed all 23 tests.

## Entry points and release gates

Completed auxiliary Cadrisyn test containers are stopped with their volumes retained. The primary preview remains running; unrelated AtlasOps containers were left alone.

The retained container preview is `http://127.0.0.1:8080/app/markets`, account controls `/app/account`, liveness `/health/`, readiness `/health/ready/`. Analyst credentials remain in ignored `.local/credentials.json`. Source startup remains `scripts/dev.py`. [Foundation operations](FOUNDATION-OPERATIONS.md) gives reproducible setup, role upgrade and recovery commands.

External release requires TLS/real hosts, production secrets and ingress, Windows backup ACLs, encrypted/off-host storage, retention and a recovery cutover that invalidates restored sessions/tokens. Rehearse operational ownership, alerts, RPO/RTO, rollback and host/storage recovery. Hosted CI, image/OS scanning, runtime digest promotion, load/cost budgets and broader accessibility/browser testing remain unverified. The HTTP Compose preview must remain loopback-only.

No provider-success path or redistribution license is accepted. MFA/SSO, distributed abuse controls and durable audit attribution remain future identity work. The old research environment retains its FastEmbed/NumPy conflict and invalid distribution warning. Seven import-time diagnostics remain outside supported discovery. Scientific dependency resolution and the blueprint's model gates must precede promotion of quant tools. Arbitrary repository-wide discovery, all financial models and external production readiness are not claimed to pass.

## Commit trail

- `e0a5cad`: checksummed backups and isolated transactional restores.
- `99f51f5`: account lifecycle, API/session hardening, provider policy and safe workspace transfer.
- `baa51ca`: account frontend, typed contracts and packaged browser workflows.
- `8986a2f`: separated PostgreSQL roles, container/CI configuration and verified retained-volume upgrade.

The documentation/evidence commit follows those implementation commits on the same branch. The original database is intentionally excluded from every commit.
