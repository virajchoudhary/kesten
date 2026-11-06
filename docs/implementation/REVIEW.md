# Implementation review record

These are independent read-only reviews by Azure GPT-6 Luna at Max effort, followed by parent-owned corrections and runtime acceptance. They are not a provider-diverse panel, penetration test, legal clearance, or quantitative-model certification.

## Backend review

The initial review returned FAIL. It identified a missing virtual environment in browser CI, browser-cached Basic credentials on research routes, wildcard-subdomain acceptance despite the exact-host policy, and generic cache-failure responses. It also identified the fixed freshness grace window as a contract limitation.

The corrections create and use `.venv` throughout CI, require a non-simple research-client header with staff Basic credentials while preserving session CSRF, reject wildcard host/origin forms, return sanitized 503 cache errors, and configure a bounded EOD grace window. Regression tests cover each case.

A fresh verifier returned PASS for those corrections. It independently ran 27 focused tests and both research-client tests, checked a hostile host startup, exercised session CSRF, and confirmed the original database hash before and after. The parent's final supported suite has 29 passing tests after adding a hand-computed Wilder RSI fixture and retaining the session-CSRF assertion.

The comment review suggested deleting purpose docstrings, manifest sections, and a generated Django migration timestamp. No comment deletions or application suppressions were accepted. The parent retained these conventional file/profile explanations and framework provenance; they do not conceal runtime workarounds or replace executable checks.

## Frontend review

One reviewer attempt failed upstream with HTTP 429 and produced no verdict. A subsequent independent review inspected the source and actual desktop/mobile screenshots and returned FAIL for two concrete issues.

The initial watchlist GET could arrive after a successful POST and visually restore an older list. The correction serializes reads and mutations through the existing loading and pending states. Search waits for the initial read; reload and other mutations wait for a pending mutation. Hook regression tests attempt the forbidden orderings and verify the saved list after completion. This avoids adding background queues or a second store for a private list.

The collapsed data-table control referenced an absent region. It now sets `aria-controls` only while the table region is mounted. A rendering regression checks both states.

The narrow follow-up review confirmed the read/mutation ordering and table ARIA corrections. It returned FAIL for one remaining UI issue: the failed-read Retry button stayed enabled during a save, although the hook correctly rejected that retry. The parent disabled this button during a mutation and added a rendering regression covering Retry, Reload, and Search in the failed/pending state. This last one-line UI correction has parent test acceptance, not a further independent PASS verdict.

The final unit, build, lint, and production-mode browser evidence supersedes earlier runs. The parent owns acceptance of the local milestone. No review verdict is represented as a production-release approval.

## Parent runtime findings

Actual Chromium verification found and fixed the Next-to-Django trailing-slash loop, an invalid Intl date formatter, currency formatting leaking into RSI, chart theme timing, a mobile drawer inheriting centered-dialog transforms, and table disclosure state resetting during range changes. The browser path checks rendered canvas output and table/API agreement, not merely a successful compilation.

The review accepts the initial local workspace only. PostgreSQL/container execution, licensed provider success, invitation/reset/revocation flows, observability, recovery rehearsals, and the blueprint's scientific gates remain open. The preserved legacy algorithms have not been promoted into accepted product calculations.
## Phase two: production foundation corrections

These reviews are independent Azure GPT-6 Luna Max contexts. The [routing receipt](evidence/phase2/worker-routes.json) uses each child's latest own turn context, excluding inherited parent contexts. This establishes requested runtime model/effort, not billing attribution, provider diversity, a penetration test or certification. The parent owns integration and observed runtime acceptance.

The initial account/UI review found an account-wide cooldown could deny an otherwise valid login from a different peer and that invitation issuance lacked an operator revocation path. The fix keys the cooldown by a secret HMAC of normalized username and canonical peer IP, ignores arbitrary forwarded chains, and adds locked/idempotent operator revocation. A fresh account acceptance review returned source-level PASS for those corrections, session epochs, migration backfill and frontend integration. It ran no database or browser tests. It noted durable revoking-operator attribution as a nonblocking audit follow-up. The parent subsequently ran the final PostgreSQL and packaged-browser gates.

Operations reviews initially returned FAIL for sessions in an otherwise empty destination, restricted historical observations crossing transfer, non-atomic SQLite publication, and inconsistent error/request IDs. Corrections require an empty session table, filter non-demo observations, publish validated SQLite files atomically without overwrite, and propagate the safe request ID. Further review identified unused account bearer credentials crossing the transfer boundary and the runtime role owning its database/schema. Those were fixed with token exclusion regression fixtures, a migration owner separated from runtime DML, ownership-aware readiness and actual runtime DDL-denial probes.

A subsequent bounded foundation review found no additional blocker in provider policy, transfer filtering or SQLite recovery, but returned FAIL for the retained-volume upgrade. The baseline image initializes `cadrisyn` as its bootstrap superuser. Initialization variables cannot change a retained cluster. An actual disposable legacy-volume reproduction also proved that PostgreSQL refuses to demote its original bootstrap identity. The corrected transaction retains that original identity under a disabled-login, passwordless bootstrap name, creates a restricted runtime role with the original SCRAM verifier, and transfers the application schema to the separate migrator. The operator must reconnect as a separate administrator before applying it. The verifier proves preserved rows, the same runtime credential over TCP, default grants, DDL denial, idempotence and restart without targeting the working database.

The final bounded retained-volume correction review and its limits are recorded below. Earlier FAIL verdicts remain findings at their inspected snapshots, not descriptions of the corrected final tree. Review source snapshots are not all head-bound; final parent receipts establish the tested code/image relationship.

### Final retained-volume acceptance

A fresh verifier returned PASS for the bounded retained-volume correction. It confirmed the baseline superuser setup, preparation and transactional upgrade code, and the saved end-to-end receipt. Before the disposable container was stopped, it independently ran SELECT-only queries confirming runtime nonprivilege, migrator ownership, DML/sequence grants and preserved legacy/post-upgrade rows. It also checked Compose parsing using the example environment and the Compose diff whitespace.

It did not rerun the writing end-to-end verifier. The private example-path preview environment did not exist, so it used `config/.env.example` for Compose parsing. The container was stopped before its independent TCP credential recheck. The parent's full verifier did use TCP with the preserved runtime credential and passed; actual private-environment Compose parsing also passed. These are separate pieces of evidence. See [acceptance scope](evidence/phase2/review-acceptance.json) and [parent runtime proof](evidence/phase2/legacy-role-upgrade-v2.txt).

### Parent acceptance and limits

The final named-volume PostgreSQL suite passes 78 tests without skips. The packaged API source comparison matches 47 files. Five Chromium scenarios pass against the final separated-role stack, comprising three actual API journeys and two isolated UI cases. Actual backup/restore compares all fields of 20 copied fixture objects and verifies readiness, fresh sign-in, private watchlist and logout. Windows and Linux each pass 17 recovery tests. [PHASE2.md](PHASE2.md) links the current receipts and documents failed experiments and remaining release gates.

One earlier reviewer service attempt returned HTTP 429 and no verdict; it is not counted as a PASS. Behavioral read-only instructions were used for source reviewers; no claim is made of a separately enforced read-only sandbox. Review agreement does not authorize merge, deployment, public market-data use or scientific claims.
