# Verification record

Local implementation commits on `codex/cadrisyn-foundation`:

- `f21699d8b96f1941f114e572e5db671ecef861ed` fixes market search, mobile chart settings and account navigation.
- `6e9390e94b85354749d8e2cb29dd0ea731c8b039` fixes research tab continuity and saved-result navigation, with the compiled browser regressions.

No push, merge, deployment, paid service, domain purchase or original-data migration was performed. The local compiled preview uses `http://127.0.0.1:3000/app/markets`, with standalone research at `/app/research` and account security at `/app/account`. Its API health endpoint is `http://127.0.0.1:8000/health/`. Preview credentials remain in ignored local files.

## Build and test scope

The production build and all final browser tests must refer to the same source receipt. The completed build receipt is `f4cbfbbd3f14247c286ef0cc5fd964b40018c8e4b72b57f3208b6377bf077f55`. Documentation and screenshots are outside that frontend receipt. No backend, schema, numerical model or dependency changed in this task.

| Gate | Current evidence |
| --- | --- |
| Baseline frontend | 119 tests passed across 33 files, with two workers. |
| Final frontend | 124 tests passed across 35 files, with two workers. |
| TypeScript | `npm run typecheck` passed. |
| Lint | `npm run lint` passed. |
| Production compilation | `npm run build` passed; source receipts before and after match. |
| Backend/security/research baseline | `scripts/check_backend.py` executed 136 tests. 132 passed and four PostgreSQL-only cases skipped. Migration drift absent; API contract matches. The existing HSTS preload warning remains. |
| Recovery regressions | 18 tests passed in the isolated existing harness. No actual PostgreSQL restoration was attempted. |
| Workspace migration regressions | Seven tests passed, including preservation behavior. No migration was applied to the original database. |
| Preserved legacy research suite | Blocked at import by missing `torch` in the existing environment. One loader test errored; no model evaluation ran. |
| Full compiled Chromium acceptance | All 15 scenarios across seven suites passed. Production profile, actual isolated API, unchanged API limits, no retries. Build and browser before/after source receipts match. |
| Final rendered review | 22 final captures across primary routes and four viewport sizes, plus focused mobile/settings/history and chart-depth images. All 20 authenticated/public route captures report no document overflow; no captured HTTP or page errors. The two sign-in images supplement that 20-route manifest. |
| Independent final review | Separate read-only verifier returned PASS for the five scoped fixes and tests, with no actionable findings. This is a source-review verdict; the reviewer did not run or independently verify suites or browsers. |
| Protected and unrelated files | Original database, all 496 runtime files, all 17 research artifacts and all 24 initially dirty/untracked unrelated files match their retained hashes. Shared credentials match the retained copy. |

## Reproduction

Use the existing installation instructions in [web/README](../../../web/README.md) and [root README](../../../README.md). This audit did not change installation or deployment configuration.

Run from the repository root with the project Python environment:

```powershell
.venv/Scripts/python.exe scripts/check_backend.py
.venv/Scripts/python.exe -m unittest discover -s tests -p test_recovery.py
.venv/Scripts/python.exe -m unittest discover -s tests -p test_workspace_migration.py
.venv/Scripts/python.exe scripts/check_research.py
```

Run from `web`:

```powershell
npm run typecheck
npm run lint
npm test -- --maxWorkers=2
npm run build
$env:PLAYWRIGHT_PRODUCTION = '1'
$env:PLAYWRIGHT_EXTERNAL_SERVER = '0'
$env:PLAYWRIGHT_BASE_URL = 'http://127.0.0.1:3000'
$env:DJANGO_API_URL = 'http://127.0.0.1:8000'
$env:CADRISYN_E2E_FIXTURE_DIR = '<absolute isolated fixture directory>'
$env:PLAYWRIGHT_BROWSERS_PATH = '<absolute installed Playwright browsers directory>'
$env:TERMINAL_EVIDENCE_DIR = '<absolute ignored evidence directory>'
npm run test:e2e:terminal
```

Start the isolated API on port 8000 first. Leave port 3000 free. The production Playwright profile starts the compiled server and refuses to reuse an existing preview. Existing fixture preparation and account token requirements are documented in `web/README.md` and the account suite. Use disposable accounts. Do not point fixture setup at the original database. The paced runner waits 60 seconds between suites to retain the actual API throttle policy.

The product-quality history scenario intentionally follows suites that create saved runs for the same fixture owner. For a standalone invocation, provision at least one saved synthetic evaluation first. It must not silently skip an empty fixture. The delayed-response scenario calls the actual API and delays transport only; its response and IDs are not fabricated.

## Failed attempts and environmental limits

- All four new behavioral browser scenarios failed against the baseline for the documented defects. The search unit regression and account navigation assertion also failed before correction. Original failure logs are retained.
- A browser tooling/runtime interruption removed access to the prior in-app browser session. Firefox app-access approval timed out, so that engine remains unverified. The original live Chromium audit and screenshots predate that interruption.
- The first resumed smoke invocation ran without valid access to the API and returned an HTML error instead of JSON. It is an invalid environmental attempt, not an accepted application result. Subsequent acceptance uses explicit production mode and verified local API health.
- A compiled standalone smoke run passed three cases but failed the history precondition because that fresh fixture had no saved evaluations. The prescribed full runner creates saved results before this scenario. No assertion or fixture requirement was weakened.
- The first full compiled run passed accounts, market and research-quality suites, then the older research scenario timed out because its exact URL expected no fragment. The browser had reached the correct exact run with `#research-results`. Its expected URL now includes that exact fragment. Numerical, provenance, identity and export assertions remain unchanged. Final acceptance reruns this test.
- A fresh runner was started prematurely while the replacement build was still compiling. It was stopped with its task-owned process tree, and its log retained. It is excluded from final acceptance. A completed build exit and matching receipt are required before restarting.
- The system Python did not have Django when preparing fresh fixtures. Repeating with the existing `.venv/Scripts/python.exe` resolved this setup error without package installation or dependency changes.
- `scripts/check_research.py` cannot import the preserved legacy API tests because `torch` is absent. This is an unresolved legacy-environment blocker, not a scientific rejection or a passing legacy-model test. No packages were installed and no legacy model code changed.
- PostgreSQL, containers, hosted CI, physical devices and deployment were not newly qualified here. A successful SQLite preview does not replace those gates.

## Preservation

The original `backend/db.sqlite3` must retain SHA-256 `93745bfc1a3149a0f77bbcdd1a50f712195750879f3fb313728ab9811f99715b`. The retained manifests cover 496 runtime files and 17 research artifacts. Each file that was already dirty or untracked at task start also has a separate hash snapshot, including unrelated release engineering work. Final commits stage only explicit frontend fixes, behavioral checks and this audit evidence.

Saved IDs, dataset versions, canonical exports, model references, cutoff semantics and account isolation are unchanged. Market prices remain Demo; research fixtures remain synthetic. No historical archive was acquired or qualified, no model was promoted, and no financial performance claim follows from these product checks.

## Independent review

Independent read-only market and research inspections identified the accepted defects. The parent reproduced each before implementation. A separate final verifier reviewed only this task's frontend diff against `163fd042`, excluding unrelated release engineering changes. It checked the five fixes, tests, Next Link hash-navigation documentation, focus/hidden behavior, identity preservation and sign-out boundaries. It reported no actionable code, security, research-integrity, accessibility or maintainability findings.

The final verifier also found no added comments, suppressions, unsafe `any` casts or workaround guards in this scope. No comment deletions, restorations, new constraint encodings or suppression exceptions were required. The unavailable dedicated comment-review role was replaced by this explicitly bounded read-only inspection. `git diff --check` reported line-ending notices but no whitespace errors.

The verifier did not execute tests or inspect final browser evidence. One sentence in its response inferred that final browser acceptance had already passed; that inference is excluded. Only the parent-run final receipts establish runtime results. Separate agent context is established; independent provider routing and backend identity were not attested. This review is not a certification, legal clearance or production release approval.

A separate visual verifier inspected final market screenshots in dark desktop and both phone themes, four research screenshots at 1440/375px and the public Supercharts reference. It returned FAIL for one low-severity finding, a cropped mobile study legend. Its proposed horizontal-scroll solution already exists in the source. The parent verified the actual interaction at 390px: the region is focusable, has `overflow-x: auto`, and native ArrowRight moves from 0px to the full 123px scroll range, with the final RSI value within bounds. The claim that remaining values are inaccessible is therefore rejected. Discoverability of horizontal scrolling remains a possible future usability refinement, not a newly hidden or lost feature. The original visual verdict is retained here rather than relabeled as an independent PASS.

The visual verifier finished before the focused settings/account images arrived. The parent subsequently inspected those images, the selected-result destination, the complete contact sheet and the 1920px customized chart and research dock. No further rendered blocker was observed. Native keyboard/scroll evidence is in `legend-proof.json` and `legend-keyboard-390.png`; the focused actual-browser helper remains ignored under `.local/product-audit-nov9/legend-proof.cjs`. To repeat manually, focus the Selected session studies region on a 390px market workspace and use ArrowRight until RSI enters view.

Text evidence copies normalize terminal color escapes and trailing whitespace only. Original logs remain in `.local/product-audit-nov9/`. The evidence manifest records SHA-256 values. A scan against known local preview credential values passed before staging; secrets, fixture credentials, invitation/reset tokens and databases are not included.
