# Kerquant verification record

This record covers the local UI refinement after `41a33b7` on `codex/cadrisyn-foundation`. It does not renew earlier infrastructure qualifications or authorize publication. Full local receipts are under `.local/kerquant/`; selected non-secret evidence is retained beside this document.

## Executed checks

| Check | Result |
| --- | --- |
| TypeScript and ESLint | Passed after the independent-review corrections. |
| Frontend behavior tests | 119 tests across 33 files passed with `--maxWorkers=2`. The unrestricted concurrent run had one existing account test exceed its five-second timeout; 118 tests passed. Assertions and timeout limits were unchanged. The bounded run passed again after the navigation correction. |
| Django checks, migration drift, API contract, backend security/research tests | 136 tests executed, 132 passed and four PostgreSQL-only tests skipped. No migration changes. Contract matches the Kerquant display title. Existing HSTS preload warning remains. |
| Recovery | 18 existing isolated tests passed. These test recovery logic; no actual PostgreSQL restore was performed in this iteration. |
| Workspace migration | Seven existing isolated tests passed, including research/result preservation and SQLite snapshot handling. |
| Legacy research client | Two existing credential-boundary tests passed. |
| Development environment | Two existing isolation/configuration tests passed. |
| Legacy branding and page syntax | Two new tests passed, including three display-name cases and compilation of the preserved page files without importing experimental models. |
| Production frontend build | Reviewed build exited 0. Source receipts before and after match. The preceding successful build was superseded after the independently reproduced mobile-navigation defect was corrected. |
| Compiled Chromium workflows | All 11 scenarios across six paced suites passed. Eight scenarios use the real isolated API, two exercise isolated UI responses, and one checks public-page accessibility. Includes actual account lifecycle, private watchlists, research comparisons/replay/exports, chart controls and the mobile regression. |
| Browser captures and metadata | Five primary routes at 1440×900, 1920×1080, 820×1180, and 390×844, plus two sign-in captures. No horizontal document overflow or captured HTTP/page errors. Kerquant titles/application-name match; icon HTTP 200. Functional scenarios also check 375 px and both themes with axe. |
| Preservation | Original database SHA-256 matches; all 496 runtime files and 17 research artifacts match their retained manifests. Shared credentials match the retained copy. |

Build, full browser run, and final route captures share frontend source hash `eeabc7906ce7f035866866955f557e9a4d274dbdc53f31a29f1994b686755561`. These receipts cover the user-selected measured-frame identity and shared account header. Earlier successful pre-selection runs remain in separate local directories and are not relabeled as this revision. The [evidence index](evidence/README.md) links actual images, before/after references, logs, and machine-readable receipts. Parent visual review inspected configured desktop analysis, the 1920 research dock, phone dark/light charting, phone research, and standalone research. The study legend scrolls within its own bounds on phones; it does not increase document width. A full-page image can include scrollable research content beyond the initial viewport.

The current local review entry points are [markets](http://127.0.0.1:3000/app/markets), [research](http://127.0.0.1:3000/app/research), and [account](http://127.0.0.1:3000/app/account). This preview uses `.local/terminal-depth/preview.sqlite3`; its login is retained in `.local/terminal-depth/credentials.json`. The richer screenshot account is in `.local/terminal-depth/visual-final-credentials.json`. Do not commit or print these files. The ordinary development launcher uses a different isolated database and credentials as described below.

## Review corrections

An independent read-only verifier reviewed the actual diff. Its initial verdict was FAIL with three findings. The mobile watchlist research link changed the route but left the dialog over the research view. A Chromium assertion reproduced the failure against the compiled preview. The link now uses Next.js `onNavigate` to dismiss the mobile panel only for navigation in the current tab. The assertion remains in the terminal scenario.

The old terminal README, verification ledger, and design system now identify their Kesten-era scope explicitly and link to this iteration. Their numerical outcomes, images, and source receipts remain unchanged. New typography overrides use zero tracking. No new suppression, unsafe cast, or unnecessary constraint comment was found in the bounded review.

During the legacy display pass, the preserved SWOT page was found to contain the invalid statement `from api_client import client as requests as http_requests`. The original source at `41a33b7` fails compilation at line 15. The corrected alias and API URL reference compile without loading models. This fixes the import only; the legacy Streamlit/ML runtime has not been fully qualified.

A second read-only source/visual review passed the bounded engineering standards but failed naming consistency because the direct API export attachment still used `cadrisyn-run-<id>.json`. That filename is now `research-<id>.json`, matching the application's neutral download name. The `cadrisyn-research-v1` payload format, identities, canonical numerical results, ownership checks, and redistribution restrictions remain unchanged. The existing export integration test asserts the new attachment name and preserved content; the full backend suite passed again.

The user rejected both the thin K and the later split K. A broader R&D pass explored four distinct directions using the built-in image-generation tool. The user selected **02, Measured frame**. The selected direction is implemented as deterministic SVG, with neutral colors in both themes. The [R&D record](LOGO-RND.md), original board, prompt, and vector asset preserve that decision without implying trademark clearance.

A subsequent independent review found an old three-bar glyph in the account header. That header now uses `BrandMark`, as do the public and terminal headers. A new browser assertion failed against the previous compiled account page and passed on the measured-frame build. This is recorded separately from the earlier mobile-dialog regression. A browser check also compared the actual compiled header path with the served favicon geometry and captured both themes. Frontend checks and the production build were repeated after the selected direction was integrated.

Implementation and review agents used the configured Azure Luna Max roles. No separate provider-routing attestation was obtained. Parent acceptance relies on actual source inspection, test receipts, and rendered browser evidence, not worker claims alone.

The final bounded identity-correction review returned **PASS** for the user-selected measured-frame direction. It inspected the actual dark/light header renders, matching favicon path, shared account-header component, and absence of retired header JSX. Unused `.brand-mark` CSS remains as non-blocking residue; current markup uses `.product-mark`. The reviewer did not rerun tests or wait for the complete final browser run. Parent verification of the completed suite and source-bound captures is recorded separately above. No review grants legal clearance, production release, or product-owner acceptance beyond the user's direction selection.

## Run the local checks

Use the existing Python environment and installed frontend dependencies. Keep active preview ports free before starting another launcher. The normal development entry point is `.venv/Scripts/python.exe scripts/dev.py`, which uses `.local/cadrisyn.sqlite3` and preserves the original database. Its credentials remain in `.local/credentials.json`. The current review instance uses the separate `.local/terminal-depth/preview.sqlite3` and credentials described below.

```powershell
# Repository root.
.venv/Scripts/python.exe scripts/check_backend.py
.venv/Scripts/python.exe -m unittest discover -s tests -p test_display_branding.py -v
.venv/Scripts/python.exe -m unittest discover -s tests -p test_recovery.py -v
.venv/Scripts/python.exe -m unittest discover -s tests -p test_workspace_migration.py -v
.venv/Scripts/python.exe -m unittest discover -s tests -p test_research_client.py -v
.venv/Scripts/python.exe -m unittest discover -s tests -p test_dev_environment.py -v

# Frontend directory.
npm run typecheck
npm run lint
npm test -- --maxWorkers=2
npm run build
```

Stop the task-owned frontend launcher and its verified server child before rebuilding on Windows. Await the build's actual exit status before starting `npm start`; a compilation message alone is not completion. The production preview uses `DJANGO_API_URL=http://127.0.0.1:8000`, `HOSTNAME=127.0.0.1`, and `PORT=3000`. Keep both source receipts from `web/scripts/terminal-source.mjs` and reject a source mismatch.

For a new browser run against normal source development, prepare a fresh private fixture directory using `scripts/prepare_browser_fixture.py --output-directory .local/<new-unique-directory>` and set `CADRISYN_E2E_FIXTURE_DIR` to it. The script seeds synthetic fixtures and new disposable accounts in the development database. Do not substitute the original database or an external database. Invitation and reset tokens are single-use; allocate a new directory for each full run.

```powershell
# Frontend directory, with the local API and frontend already running.
$env:PLAYWRIGHT_EXTERNAL_SERVER='0'
$env:PLAYWRIGHT_BASE_URL='http://127.0.0.1:3000'
$env:CADRISYN_E2E_FIXTURE_DIR='C:\stock price predictor\.local\<new-unique-directory>'
$env:TERMINAL_EVIDENCE_DIR='C:\stock price predictor\.local\<new-evidence-directory>'
npm run test:e2e:terminal
```

The runner preserves API throttles by waiting 60 seconds between suites. It copies each suite's screenshots before Playwright replaces its output directory. The terminal scenario creates the synthetic saved run inspected by the following depth scenario. Source-profile health checks target port 8000. `PLAYWRIGHT_EXTERNAL_SERVER=1` selects the separate container-profile health default and is inappropriate for this source preview.

## Remaining release boundaries

Trademark registries have not produced a completed, verified result set. Domain RDAP responses and GitHub search do not establish availability or legal clearance. No domain, repository, package, protocol, database, or saved research identity was renamed.

No historical dataset is newly qualified, no empirical forecasting performance is established, and no legacy model is promoted. Browser research results are synthetic pipeline checks. Data licensing and redistribution rights remain release gates.

PostgreSQL/container execution, real database restoration, hosted CI, image scans, non-Chromium browsers, and assistive-technology testing were not rerun for this presentation-only iteration. Existing PostgreSQL-only backend skips remain explicit. Phase 5 release engineering is paused. The local application is reviewable; production release and parity with a commercial financial terminal are not claimed.
