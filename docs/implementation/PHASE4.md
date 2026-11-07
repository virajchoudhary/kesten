# Phase 4 research workspace

Phase 4 continues `ae0d028` on `codex/cadrisyn-foundation`. It adds a usable private research workflow without changing the numerical engine, dependency lock, database schema, PostgreSQL roles, or historical-data qualification rules. Cadrisyn remains a temporary working name.

The implementation commits are `a617f5a` for the private research API/contracts and `8aa05cc` for the research UI, session corrections, and browser harness. Operational evidence and image/scanning changes are recorded in the following local commit.

The working packaged application is [research](http://127.0.0.1:8086/app/research), [markets](http://127.0.0.1:8086/app/markets), and [account security](http://127.0.0.1:8086/app/account). These separate application containers reuse the isolated qualification database and Redis service. The Phase 3.5 application remains available at port 8085. Neither preview is a production deployment.

## Delivered behavior

The research setup selects an account-private immutable dataset and a one-session or five-session horizon. Every evaluation still computes both last-close and expanding historical-log-mean references. **Reference focus** changes the inspected series, not the evaluated model or training configuration. Unsupported legacy models have no launch controls.

Saved evaluations have server-backed search, instrument/horizon/data-kind filters, pagination, loading and retry states, and explicit filtered-empty states. A watchlist's research link preserves the exact instrument ID. An instrument without an imported private dataset cannot silently select an unrelated fixture.

Forecast, walk-forward, and signed-error views use the saved numerical values. Charts show training, validation, and test dates; distinguish future forecasts from observations; retain the last-close benchmark; and support pointer and keyboard session inspection. Exact evaluation rows are paginated. Missing observations never become invented prices or connecting fitted paths. Five-session target overlap is disclosed. No uncertainty band, significance test, recommendation, or empirical improvement is claimed.

Run comparison is a bookmarkable `?run=<UUID>&compare=<UUID>` view, not a new database entity. Both IDs are resolved under the current account. The server checks dataset version, complete target/protocol, method versions, runtime, and aligned row identities/actual values before allowing descriptive metric differences. Incompatible runs retain their identities and show reasons instead of deltas. Identical deterministic runs do not demonstrate a forecasting improvement.

**Verify exact replay** uses the existing CLI's five checks without modifying the saved run. A completed mismatch is different from an unavailable request. **Download synthetic run JSON** validates the envelope and saves the original server JSON text. Reserializing parsed JavaScript numbers would change the canonical Python checksum representation. Historical exports remain forbidden because a free-text license reference does not establish redistribution rights.

## API and integrity boundaries

The original full `GET /api/v1/research/runs/` endpoint is retained. Additive endpoints are:

| Endpoint | Contract |
| --- | --- |
| `GET /api/v1/research/history/` | Private summaries, default 20 and maximum 50 items, bounded filters, stable ordering, total/offset/limit. No full result or runtime JSON. |
| `POST /api/v1/research/runs/{id}/replay/` | Empty JSON object, session CSRF, existing research throttle, read-only PASS/FAIL flags. |
| `GET /api/v1/research/runs/{id}/compare/{other}/` | Both runs private; authoritative compatibility reasons. |
| `GET /api/v1/research/runs/{id}/export/` | Consistent synthetic results only; fixed filename, private/no-store, nosniff, original result and checksum. |

An inconsistent saved/current dataset version makes the requested history page return a sanitized 503. It does not replace a saved version with a mutable current value. Foreign IDs return 404. SQLite and PostgreSQL UUID searching normalize hyphens consistently. Generated OpenAPI and TypeScript contracts are updated together.

## Verification

The [evidence index](evidence/phase4/README.md) records executed checks and their limits. The final Linux/PostgreSQL selection passes **129 tests without skips**, including existing account isolation/concurrency and 24 numerical tests. The earlier Windows/SQLite supported selection passed 128 tests with four PostgreSQL-only skips; the added lineage guard then passed all nine affected API tests on SQLite. The final PostgreSQL run includes that guard.

All **75 frontend unit tests**, TypeScript, lint, production image builds, and nine Chromium scenarios pass. The browser scenarios include six actual API/browser workflows, one public-page accessibility scenario, and two isolated account UI cases. Automated WCAG 2 A/AA and 2.1 AA checks cover public pages in both themes at 375px, research at 375px and 1440px in both themes, and authenticated markets/account screens. They also check viewport overflow, keyboard chart inspection, comparison reload, exact download bytes, replay PASS, and a real two-tab switch to an account without the first account's research. This does not certify accessibility or cover every browser, assistive technology, or modal state.

Recovery creates a new PostgreSQL destination, restores a new checksum-verified backup, compares every selected field of **73 fixture objects**, and replays both horizons exactly in Linux. Existing source/restore databases and archives are retained. No original user database is a restore target.

A temporary API against that restored database passes readiness, fresh sign-in, owner history reads, both saved-result hash comparisons, logout, and anonymous-history denial. It is stopped after verification. Nineteen HTTP smoke checks also pass against the main Phase 4 preview; they are separate from browser acceptance.

Independent reviews found and drove four corrections: the dataset-lineage guard, stale private state across account changes, late evaluation navigation, and mismatched cutoff joins. All three frontend regressions failed before the fixes and pass afterward. A fresh read-only verifier accepted the three frontend corrections; the earlier reviewer independently confirmed the backend lineage/export fix. See [review dispositions](REVIEW.md#phase-4).

The original SQLite hash remains `93745BFC1A3149A0F77BBCDD1A50F712195750879F3FB313728AB9811F99715B`. All 496 protected runtime files and 17 recorded research artifacts match their preserved manifests. The pre-existing SQLite modification remains outside the commits.

## Performance scope

Five alternating warm requests compared the same four saved run identities on the same current API process. Median uncompressed response size was **215,033 bytes** for full runs and **1,675 bytes** for summaries. This measures history payload reduction, not a general latency, load, or forecasting-performance improvement. Details are fetched on demand. History pages and exact-row tables are bounded; chart paths use linear maps rather than repeated timeline searches. No measured need justified a new queue or worker architecture.

## Release blockers

- **No qualified historical archive.** Only explicitly labeled synthetic pipeline checks are available. No historical observations were acquired or mixed into empirical evaluation. Existing data-source decisions and model rejection/promotion gates remain in [historical qualification](HISTORICAL-DATA-QUALIFICATION.md).
- **Image security gates fail.** Final API Grype output has 283 matches, including 2 Critical, 96 High, and 90 Medium classifications. Final web output has three Medium matches for the same BusyBox CVE across three installed packages. These are scanner matches, not 286 distinct exploitable defects. Vendor backports, reachability, and remaining base-image/runtime findings require triage and qualification. No ignore rule or weakened threshold conceals them.
- **Hosted CI has not run.** Workflow YAML and official action pins were checked locally. Local tests and scans do not establish a hosted result.
- Production TLS, ingress, secrets rotation, off-host encrypted backups and retention, restoration of post-backup security revocations, capacity/cost/load testing, broader browser/assistive-technology acceptance, and lawful market-data operation still require their own release evidence.

The local research experience is functional. Production release and empirical forecasting acceptance remain blocked. No merge, deployment, purchase, live trading, advanced-model promotion, or repository rename occurred.

## Next milestones

1. Resolve the image findings with vendor backport/reachability evidence or compatible pinned patches. Requalify affected runtime changes against retained results and recovery copies; preserve the original numerical/runtime identities rather than rewriting old runs.
2. Run the configured hosted gates after a separately authorized publication step. Complete broader browser/assistive-technology and realistic multi-user load acceptance before a release decision.
3. Admit a historical archive only through the existing rights, adjustment, calendar, completeness and point-in-time gates. Reproduce chronological/walk-forward baselines before enabling empirical comparisons or qualifying another model.
