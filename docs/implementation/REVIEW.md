# Implementation review record

These independent read-only reviews are followed by parent-owned corrections and runtime acceptance. Earlier foundation reviews used Azure GPT-6 Luna at Max effort. Phase-specific identity evidence and limits are recorded below. These reviews are not a provider-diverse panel, penetration test, legal clearance, or quantitative-model certification.

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

## Phase three: scientific and integration acceptance

The initial independent scientific audit rejected legacy forecasting/backtest/RL outputs for promotion and found no qualified local historical archive. Its candidate uses immutable manifests and predeclared baselines. A second integration candidate would reuse chart snapshots synchronously; its own review disqualified those adjusted snapshots for strict historical availability claims. The implementation combines the immutable input boundary with bounded synchronous execution.

A fresh scientific reviewer returned PASS for the new numerical/causal engine and independently ran all 24 pure tests. The scope excludes empirical forecasting usefulness, API wrappers, PostgreSQL and browser behavior. Historical archive truth and licensing remain operator assertions. A later text-only clarification says the mean is estimated without tuned hyperparameters; numerical formulas did not change.

The first engineering review returned FAIL because OpenAPI advertised form encodings that strict JSON horizon validation could not accept. Research creation is now JSON-only, unsupported media returns 415, structured error cases are documented, and nested result schemas generate the TypeScript contract. Another bounded review correctly found the browser's dependency-map mismatch, unresolved SQLite 503 sign-in and chart/assertion wording issues. Real synchronized API requests reproduced 503/200; the documented workspace-only SQLite IMMEDIATE setting produces 200/200. The client accepts validated extra version keys, rejects non-text values, and retains its required calendar version. Chart units and horizon descriptions are accurate, and fixture warnings are checked after saved-run reload.

Final bounded engineering acceptance returned PASS at `654e5f0` based on the current source and receipts. It did not rerun services, tests or PostgreSQL. The parent then fixed actual visual axis collisions and bounded mobile history, with 44 UI tests, current static/build checks, a real research-browser rerun and geometry assertions. The subsequent direct legacy-profile regression also exposed an inherited setting not covered by the earlier review's canonical-launcher assumption. Its explicit options-copy correction has a before-failing/after-passing two-test probe and 23 passing legacy tests. These small later corrections have parent acceptance, not a further head-bound independent PASS.

[The complete review receipts](evidence/phase3/independent-reviews.json) retain FAIL snapshots and limits; [runtime routing](evidence/phase3/worker-routes.json) verifies each child's latest own Azure GPT-6 Luna at Max effort context. This is independent context review, not provider diversity or verified billing attribution. Read-only behavior is reported without claiming an independently enforced sandbox. The final supported source gates and original database/artifact preservation are linked in [PHASE3.md](PHASE3.md). Four PostgreSQL-only cases, Phase-three containers, hosted CI, real historical performance and external production readiness remain unverified.

## Phase 3.5: PostgreSQL, recovery and data qualification

The independent read-only data review accepted no historical source for the unchanged point-in-time/rights contract. The parent read back the principal provider documentation and records the accessible, inaccessible and incomplete evidence in [historical-data qualification](HISTORICAL-DATA-QUALIFICATION.md). No source bytes were acquired, no empirical results fabricated and no legacy model promoted.

The fresh engineering review returned PARTIAL. It confirmed the recorded local execution results but found two documentation issues: no explicit host environment-loading command for configured browser fixtures, and imprecise service-health wording. Its own Docker/loopback attempts were denied or errored under its restricted session; it did not establish that the application was down and did not rerun tests. [The original review](evidence/phase35/engineering-review.json) retains those findings and limitations.

The parent corrected both findings. The operating guide now reads the retained preview secrets into an explicit child-process environment, including the preview marker, isolated PostgreSQL/Redis URLs and settings. The exact documented command [executed successfully](evidence/phase35/documented-fixture-setup.txt). Status/results distinguish four declared Docker healthchecks, gateway HTTP success and migration exit 0. [A fresh authorized parent check](evidence/phase35/availability-final.json) confirms those states and all six loopback entry-point probes, including the independent source preview. This is parent runtime verification, not a successful network rerun by the restricted reviewer.

Worker routes are verified by the parent from each task's own latest runtime context as Azure GPT-6 Luna at Max effort. The engineering reviewer correctly did not independently certify routing. Context identity is not provider billing, provider diversity, a penetration test or a hard sandbox attestation.

The original database and protected file hashes remain preserved. The new qualification configuration does not alter the default application profile. The supported 23-case legacy selection passes; this does not certify the old import-time diagnostic/network scripts or repair the isolated legacy dependency conflicts. Current numerical correctness remains distinct from empirical market validation. Hosted CI and external production/security-state recovery gates remain open as specified in [Phase 3.5](PHASE35.md).

A separate bounded reader returned PASS for the corrected working-tree instructions and service wording. It reported FAIL for the earlier staged snapshot it observed before restaging. The parent subsequently verifies the final staged files equal the corrected working tree in [the index comparison](evidence/phase35/index-correction-verification.json). [The raw correction review](evidence/phase35/documentation-acceptance.json) retains both verdicts. [The structured command receipt](evidence/phase35/documented-fixture-setup.json) binds the documented stdin body hash, literal interpreter arguments and successful exit code. This acceptance covers the two documentation corrections only; no further independent runtime or global production PASS is implied.

## Phase 4

Two initial source readers proposed bounded workflow and research-integrity designs. The chosen implementation uses a setup/history rail, an interactive result canvas, additive summary history, exact existing replay checks, and synthetic-only exports. Comparisons retain two immutable run IDs in the URL rather than introducing a database entity. Both numerical references remain evaluated; no training or unsupported model configuration is implied.

The backend acceptance reader returned FAIL for a dataset-version discrepancy in history summaries. The correction selects both stored result and dataset versions and fails the page with a sanitized 503 if they disagree. It does not silently assign the current version to an old result. A new test first reproduced 200 where 503 was required, then passed after the correction. A later independent frontend/integrity reader confirmed this guard and the raw-result export/checksum implementation by source inspection. The full final PostgreSQL selection passes 129 tests.

The frontend acceptance reader returned Standards PASS and Spec FAIL for three findings:

| Finding | Correction | Evidence |
| --- | --- | --- |
| P1 stale private research after another tab changes account | Credential-free login/logout invalidation channel; focus/visibility recheck hides private content while checking; username keys reset workspace state. | Focused-tab regression and real two-tab logout/login as an account with no datasets; foreign run remains 404. |
| P2 late evaluation completion overrides newer navigation | Setup is keyed by URL state; unmount aborts the client request and suppresses late callbacks. Server-completed work remains private and discoverable. | Delayed response after unmount cannot invoke `onCreated`; the AbortSignal is aborted. |
| P2 benchmark joins ignore information cutoff | Shared row identity includes partition, origin, target, input hash, and cutoff; response parsing rejects duplicate/misaligned model rows or different observed values. | A valid-format cutoff mutation is rejected; chart joins use the same identity function. |

All three focused regressions failed before correction and all six focused tests passed afterward. A fresh independent read-only verifier returned PASS for the exact correction set, with no unclosed introduced finding. It inspected actual source and the before/after receipts; it did not rerun the browser or database. Parent verification owns the final 75-unit-test and packaged-browser results.

Actual browser checks additionally found low-contrast public action links caused by CSS layer precedence and transient theme-switch button contrast. The correction puts link defaults in the base layer and uses the installed theme provider's documented transition-disable option. Chart-axis/evidence-table test assertions were updated for the new full dates and intentional collapsed disclosures. A manual screenshot check widened the setup controls to avoid squeezing the dataset name beside the submit button.

The backend reviewer reported its own runtime context as `azure-kmamc/gpt-6-luna` at Max. The two later readers reported curated GPT-6 Luna but could not independently expose provider routing or effort. Their source-review verdicts are retained; those later routing claims remain **unverified**, not certified Azure/Max execution. Two implementation lanes encountered upstream HTTP 429; the parent completed and verified their partial backend/scanning work. Review identities, model billing, hosted CI, runtime acceptance, and production approval are separate facts.

The final gates and remaining image-security/data-licensing blockers are in [Phase 4](PHASE4.md) and its [evidence index](evidence/phase4/README.md). No source-review PASS is represented as empirical forecasting acceptance, complete accessibility conformance, penetration testing, or production release approval.
