# Research usability qualification — 12 November 2026

The private research workspace now exposes dataset coverage before execution, archived source evidence on demand, and saved baseline error comparisons. This is a usability qualification over synthetic fixtures, not empirical forecasting acceptance. **Production remains NO-GO.** No historical archive was newly admitted, downloaded or scored.

## Delivered behavior

- **Dataset discovery:** search the current private picker by name, instrument, source or category. Selection shows coverage dates, observation count, exchange calendar and source before execution. Filtering out a selected dataset disables execution. The picker explicitly discloses its existing limit of 100 newest datasets; this is not full-catalog search.
- **Source inspection:** lazy, owner-private `GET /api/v1/research/datasets/{id}/provenance/` exposes exact dataset and receipt identities, component hashes, acquisition time, source references and operator-declared permissions. The endpoint works for an older dataset even when it is outside the picker. It returns `private, no-store`, omits raw CSV/terms/availability documents and observations, and masks corrupt receipt metadata.
- **Honest categories:** historical observations remain exploratory and independently unqualified. Synthetic fixtures remain pipeline checks. A matching archive is described as byte integrity, never legal clearance, provider authentication or point-in-time qualification. The latest dataset receipt is explicitly not represented as a receipt bound to a particular saved run.
- **Result interpretation:** the shared comparison shows existing MAE, RMSE and `mae_difference_vs_last_close` without recalculation. It includes validation/test selection, target count, horizon, dates and USD per initial-share units. The interpretation explains the delta sign and five-session target overlap. It makes no return, significance or forecasting-validity claim.
- **Workflow continuity:** standalone results and the market research inspector use the same provenance and baseline components. Existing saved-run comparisons, chart inspection, exact export and replay remain available. The chart stays above the new error summary; a direct jump reaches the comparison without hiding its heading under mobile navigation.

Admission, numerical evaluation, comparison compatibility, source archive verification, export permissions, ownership and replay contracts are unchanged. No model, schema migration, background job, provider or infrastructure replacement was introduced. The only settings change names OpenAPI enums explicitly so strict schema generation remains warning-free.

## Findings and corrections

The initial independent audit identified hidden selection metadata, unavailable receipt inspection, older-run provenance depending on a capped list, and a computed baseline delta that users could not see. These changes address those workflows using existing services and read-only metadata.

The first independent implementation review reported two P2 issues:

1. Search appeared complete although the API returns only the 100 newest datasets. The UI now declares that limit and describes no-match results only within the current picker. Pagination remains a future improvement.
2. The generated TypeScript provenance type lost its status union through `Omit<union, "status">`. Removing the optional OpenAPI discriminator hint preserves read-only `oneOf` cases with required, distinct status values. Generated files were regenerated, not hand-patched. A type regression produced five errors before the correction and passes afterward.

The closure reviewer found zero Standards or Spec findings in that bounded scope. It independently regenerated TypeScript in memory and confirmed an exact match. The reviewer did not claim to rerun PostgreSQL or the final mobile offset check. The parent subsequently verified the offset in Chromium. Requested worker routing was Azure Luna Max; provider/model attribution was not independently attested (`ROUTING_UNVERIFIED`). This is an independent review, not a model-diversity claim.

Visual review also rejected an intermediate layout that put the summary above the chart. After moving it below, the parent found that the mobile jump hid the heading behind sticky navigation. A bounding-box regression failed at heading Y=0.296875 against navigation bottom Y=45, then passed after adding the scroll offset. Screenshots were inspected at desktop, wide desktop, tablet and mobile widths, including light and dark mobile views.

## Verification evidence

Artifacts are in [research-usability-20261112](evidence/research-usability-20261112/verification.json). The receipt records exact source and artifact hashes. Test results cover the task's affected paths; they are not a fresh hosted CI, whole-platform release or image-security qualification.

| Check | Result and scope |
| --- | --- |
| PostgreSQL research suite | 85 tests, zero skips/failures/errors; includes numerical fixtures, historical admission, provenance isolation, integrity, replay and concurrent idempotent persistence. Fresh PostgreSQL 17.11, cached official image, tmpfs, unique role, ephemeral loopback port. Test DB teardown and label-verified container removal passed. |
| PostgreSQL harness diagnosis | Initial 12 tests passed but teardown failed because thread connections remained open. `connections.close_all()` fixes cleanup. A bounded post-evaluation barrier forces both real evaluations to reach persistence concurrently. Corrected selected run: 12 passed, zero skips, successful teardown. No production service was changed. |
| Backend follow-up | Six provenance API tests passed after the subsequent OpenAPI annotation-only correction. The 85-test PostgreSQL run predates that annotation change; its source hashes are retained. |
| Frontend unit/integration | 38 files, 134 tests passed with two workers. A run concurrent with a build hit three five-second timeouts; rerun passed without timeout or assertion weakening. A separate obsolete heading expectation was updated to the deliberate UI label. |
| TypeScript / ESLint | Full checks passed. Final build rechecked TypeScript; scoped ESLint covers the subsequent browser assertion and scroll-offset edit. |
| OpenAPI | `spectacular --validate --fail-on-warn --format openapi-json` passed and matched `contracts/openapi.json`. The unused database path remained absent. |
| Local optimized build | Next.js standalone build passed after the mobile offset correction. The compiled preview used loopback API rewrites. This is not a container image or deployment claim. |
| Chromium workflows | Four distinct browser cases passed across the recorded runs: public page accessibility/themes; research inspection/comparison/export/replay; cross-tab account isolation; new dataset/provenance/baseline workflow. The existing research case initially failed on obsolete empty-state wording and passed after its selector update. |
| Final mobile regression | New workflow passed again against the final compiled application with unobscured heading assertions in both mobile themes. Screenshots: 1440×900, 1920×1080, 768×1024, 375×812. Overflow checks and mobile WCAG A/AA scans reported zero violations; no page errors. |
| Preservation | SHA-256 matches for all 496 protected runtime files, 17 research artifacts and 22 pre-existing modified/untracked paths. Original database hash preserved. |

The PostgreSQL image identity is `sha256:748a18a54d3842d43bc156f0840d78029b8d349e0feca98c12b9c4ce3404a6b3` (`postgres:17.11`). No pull, rebuild, volume deletion or existing database/role modification was needed. Docker Desktop was started normally after its Linux engine pipe was initially unavailable.

The desktop computer-use adapter failed during tab startup. Browser qualification used the repository Playwright harness with matching Chromium 156.0.8078.4 in a task-private cache. Existing browser caches were retained. The test application uses a new SQLite preview database and disposable synthetic accounts; PostgreSQL tests use a separate temporary container. No user database was used for test writes.

## Evidence views

All visible prices, curves and error values in these images are synthetic. Their purpose is interface verification.

- [Before setup](evidence/research-usability-20261112/before-setup-desktop.png)
- [Before results](evidence/research-usability-20261112/before-results-desktop.png)
- [Dataset source inspection](evidence/research-usability-20261112/after-provenance-desktop.png)
- [Final results, desktop](evidence/research-usability-20261112/after-results-desktop.png)
- [Final results, wide desktop](evidence/research-usability-20261112/after-results-wide.png)
- [Final results, tablet](evidence/research-usability-20261112/after-results-tablet.png)
- [Final baseline comparison, mobile dark](evidence/research-usability-20261112/after-baselines-mobile-dark-viewport.png)
- [Final baseline comparison, mobile light](evidence/research-usability-20261112/after-baselines-mobile-light-viewport.png)

## Remaining limits

No independently qualified historical archive exists. Provider rights, durable retention, corporate-action completeness and value-specific historical availability remain blockers under the fixed close-plus-60-minute protocol. The [source assessment](HISTORICAL-RESEARCH-PROGRESS.md) remains the relevant source decision; this task did not repeat it or relax it. No empirical scores or promoted legacy models are available.

The picker still searches only the 100 newest private datasets. Exact saved-run dataset inspection now avoids that cap. Archive inspection verifies the latest receipt at request time; it is not continuous monitoring or a newly persisted run-to-receipt binding. Existing admission rechecks current evidence before a new historical evaluation.

The unchanged image security findings, off-host acceptance and hosted CI limits remain release blockers. They were intentionally not re-investigated. No push, merge, deployment, purchase, live trading or public publication occurred. The operations below describe local verification only.
