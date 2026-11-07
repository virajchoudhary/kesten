# Phase 4 evidence

These receipts record local execution on 2026-11-07. They do not establish a hosted CI result, production release, empirical prediction performance, or accessibility certification. Screenshots contain an explicitly labeled synthetic fixture and the disposable analyst preview account.

| Check | Executed evidence | Result and scope |
| --- | --- | --- |
| Backend, Linux/PostgreSQL | [Full supported selection](container-postgres-final.txt) | 129 passed, no skips. Includes existing numerical, security, isolation and concurrency checks. |
| Backend, Windows/SQLite | [Initial supported selection](backend-supported.txt), [affected final lineage tests](backend-lineage-after.txt) | Initial 128 tests with four PostgreSQL-only skips; final nine affected API tests pass. Deploy check retains the existing HSTS-preload warning. |
| Lineage defect | [Before](history-lineage-before.txt), [after](backend-lineage-after.txt) | Reproduced 200 instead of required 503; corrected guard passes. |
| Frontend | [Unit tests](web-tests-reviewed.txt), [TypeScript](web-typecheck-reviewed.txt), [lint](web-lint-reviewed.txt) | 75 tests in 24 files pass; TypeScript and lint exit 0. |
| Review regressions | [Initial reproduction](review-regressions-before.txt), [focused corrected tests](review-regressions-after.txt), [baseline cutoff comparison](cutoff-baseline-comparison.txt) | Session and late-callback failures reproduced; six final focused tests pass. The initial cutoff reproduction was corrected to change the timestamp rather than attempting a no-op text replacement. An isolated probe against the pre-UI-commit schema confirms it accepts that changed cutoff while the final schema rejects it. The committed final regression uses the actual timestamp mutation. |
| Browser | [Chromium gate](browser.txt) | Nine pass. Six actual API/browser workflows, public a11y scenario, two isolated account UI cases. Includes real two-tab account isolation, replay PASS, exact export bytes, compatibility guard, keyboard and 375/1440px theme checks. |
| HTTP | [Sequential smoke](smoke-final-sequential.txt), [availability](availability-final.json) | 19 smoke checks pass; six gateway probes return 200. Availability records actual service states, not inferred Docker healthchecks. |
| Recovery | [Restore/field/replay result](recovery-result.json), [restored HTTP](recovery-http.json) | New empty destination; all selected fields of 73 fixture objects match; both horizons replay; restored sign-in, private history, two result hashes and logout denial pass. |
| Contracts | [Contract comparison](contract-final.txt) | Generated OpenAPI equals the committed contract. Web type generation is checked with the application build. |
| Operations units | [Recovery](test_recovery.py.txt), [workspace migration](test_workspace_migration.py.txt), [environment isolation](test_dev_environment.py.txt), [research client](test_research_client.py.txt) | 17 + 7 + 2 + 2 tests pass. |
| Python dependencies | [Workspace lock](pip-audit-workspace.json), [runtime additions](pip-audit.json) | No known advisories in the 64 explicit workspace entries and two image additions. Separate file audits are intentional. |
| Web dependencies | [Production npm audit](npm-audit.json) | Zero reported production advisories. Does not cover all build/dev tooling or OS packages. |
| Images | [Exact image scan summary](image-scan-summary.json), [scanner installation](scanner-install.json), [official action pins](scanner-pins.json) | **FAIL** at Medium. API 283 matches; web three Medium package matches for one BusyBox CVE. No suppressions. See [triage limits](../../PHASE4-SCANNING.md). |
| Preservation | [Hash check](preservation.json) | Original database, 496 runtime files, 17 research artifacts, quant engine and numerical dependency lock preserved. |

The API and frontend images build successfully, run non-root, and pass runtime probes. Final API `pip check` reports no broken requirements; `makemigrations --check --dry-run` reports no changes. Both image IDs are recorded in the scan summary. Manually started Phase 4 application containers do not declare Docker healthchecks. The four original Phase 3.5 services retain their declared healthchecks.

The first browser attempts exposed theme-switch contrast and outdated chart/evidence assertions. Those were corrected. A later account-switch test expected an automatic redirect although the existing sign-in page correctly shows the new user and an **Open Markets** button; that assertion was corrected. One overlapping smoke/browser attempt hit the configured session rate limit. The final browser and smoke receipts are sequential, with rate limits intact.

Independent design/security/engineering findings and dispositions are in [the review record](../../REVIEW.md#phase-4). The final correction review is a read-only source PASS, not an independent rerun of these parent-owned executions. Later reviewers could not expose provider/effort routing metadata; no verified routing claim is inferred from their code verdicts.

## Rendered application

- [Desktop, dark](research-1440-dark.png).
- [Desktop, light](research-1440-light.png).
- [Mobile, dark](research-375-dark.png).
- [Mobile, light](research-375-light.png).

## Reproduce and protect private material

Use [Phase 4 operations](../../PHASE4-OPERATIONS.md). No database dump, credential, session cookie, reset token, private environment file, or model artifact is included here. Allowlisted text receipts were checked against the actual current private secret values before collection. Backup archives, older failed browser artifacts, unredacted scanner JSON and local probe scripts remain in ignored `.local/phase4/`.

[The inventory](inventory.json) records SHA-256 and size for collected receipts/screenshots. It excludes itself and this index to avoid self-reference. Collected text receipts normalize line endings and trailing blank lines; the original output files remain in private storage. Software and infrastructure PASS results do not qualify a historical dataset, advanced model, production security state, or investment claim.
