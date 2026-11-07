# Market terminal overhaul

Phase 5 release engineering is paused. This work changes the rendered frontend and its acceptance tests. It does not qualify a production release or a historical market dataset.

Implementation commit: `03c9cc4`. Final local checks pass: 77 frontend unit tests, 132 backend tests with four PostgreSQL-only skips, 18 recovery unit tests and ten Chromium scenarios. TypeScript, lint and the optimized production build pass. The browser runner covers seven real API workflows, two isolated account UI cases and one public-page accessibility case. Current [receipts and screenshots](evidence/ui-overhaul/README.md) define the exact scope and limitations.

The revised [design system](../rebrand/13-terminal-design-system.md) records the two rendered directions, brand recommendation, chart-library obligations and responsive rules. Evidence and final verification are collected under `docs/implementation/evidence/ui-overhaul/`.

## What changed

The old market workspace reserved 248px for a left watchlist and 320px for permanent evidence. It placed several stacked headings above a 430px chart and hid both side panels below 1440px. The new workspace gives charting the available width, uses one collapsible right watchlist and moves detailed provenance into a dialog. It provides daily range buttons, indicator controls, grid settings, fit-to-content, a crosshair OHLCV legend and viewport-dependent chart height.

Research now has a native Market/Research view inside the terminal. It reuses the existing private dataset, setup, history, result, comparison, export and replay components. Server-parsed URL identities remain the source of research and instrument selection. Clicking the active Research view preserves the selection. Switching back to Chart retains research identities in the URL, and deliberately selecting a different instrument clears that research context. Browser Back restores the URL's instrument. A redundant local selected-instrument state was removed after a browser regression demonstrated that it could override the restored URL.

The shared header, configurable wordmark, graphite palette and dark default replace inconsistent market/research headers. Light mode remains fully supported. Account and public pages use the same identity and semantic tokens. Existing session/authentication hooks, user-account services and numerical engines are retained.

The API client now rejects mismatched provenance in both directions. A delayed response cannot appear under a user-selected Demo label. The existing rejection of synthetic data returned for a delayed request remains in place. This frontend boundary correction adds no data provider or entitlement.

The Model the Domain principle led to one authoritative URL selection instead of competing local and route state. Experience First led to a full-width research view instead of a cramped bottom dock. Type System Discipline kept provenance validation at the API boundary and reused the existing parsed research contracts.

## Visual audit

| Observed weakness | Correction | Acceptance evidence |
| --- | --- | --- |
| The 1440px chart competed with 568px of persistent side panels. | One right dock; evidence on demand; dock can collapse. | Matched before/after desktop captures and browser geometry checks. |
| Fixed 430px chart left unused vertical space at 1080px. | Viewport-dependent height and smaller volume pane. | 1440x900 and 1920x1080 chart captures. |
| Instrument search was nested inside the mobile watchlist. | Direct symbol search in the command bar. | Search keyboard workflow and phone capture. |
| Crosshair lacked a readable exact OHLCV legend. | Legend resolves the actual returned observation. | Browser checks compare hovered OHLC values with the API's typed bars. |
| Evidence hashes and prose permanently displaced analysis. | Compact mandatory provenance strip plus full evidence dialog. | Modal and data-category assertions. |
| Research and markets had unrelated headers and navigation. | Shared header plus integrated research view. | Saved run reload, active-tab retention and standalone research acceptance. |
| Dataset names wrapped inside a fixed-height selector. | Wider research setup column and truncated selected value; full option remains available. | Research desktop and phone captures. |
| Account navigation disappeared from the phone header; an oversized empty result pushed history down the page. | A named Account icon remains visible, and the phone empty state is compact. | Account-link visibility and responsive browser checks. |
| Theme default and lavender/navy styling resembled a generic dashboard. | Dark-primary graphite with restrained steel-blue actions and neutral surfaces. | Dark/light captures and axe checks. |

Before captures come from both the actual initial running application and a separate source snapshot of commit `f50be38`. The latter completes matched desktop/tablet/mobile coverage without reverting the implementation. Snapshot captures must be labelled as such. They use the same isolated API and explicitly synthetic visual-review data. They are not retroactively described as pre-edit observations.

## Isolation and reproducibility

The UI review uses a new `.local/ui-overhaul/preview.sqlite3`, separate disposable browser/visual accounts and private fixture files. It does not use or overwrite the original database, shared local credentials, old snapshots, backup archives or research artifacts. One-use lifecycle fixtures are regenerated into new directories rather than reused after consumption.

The backend entry point remains the existing Django API. The frontend entry point remains `/app/markets/`; standalone research remains `/app/research/`. Local review uses `http://127.0.0.1:3000`, with API port 8000. The baseline snapshot runs temporarily on port 3001 and is stopped after capture.

Use the existing documented startup workflow for ordinary local development. The review process is an isolated temporary preview, not a replacement for deployment configuration. The committed browser suite accepts `CADRISYN_E2E_FIXTURE_DIR` and the existing loopback-only Playwright origin settings. Use fresh disposable lifecycle fixtures before a complete run.

```powershell
Set-Location 'C:\stock price predictor\web'
npm run typecheck
npm run lint
npm test
npm run build
$env:CADRISYN_E2E_FIXTURE_DIR = '<private isolated fixture directory>'
$env:PLAYWRIGHT_EXTERNAL_SERVER = '0'
$env:PLAYWRIGHT_PRODUCTION = '0'
npm run test:e2e:terminal
```

Do not point test-fixture creation or restoration at an existing user database. Do not weaken rate limits to run acceptance. Repeated exploratory runs exhausted the configured review API budgets. The production-mode frontend is fast enough that consecutive suites can exceed the anonymous session-read/login window. `test:e2e:terminal` runs the unchanged acceptance suites serially with a 60-second interval between suites. It does not intercept responses, retry failed assertions, change limits or clear the cache. Each suite must pass. For a direct Next.js preview, the regular Playwright configuration reuses the running server and probes the API on port 8000. External-server mode is for the existing gateway that exposes its own health route.

## Review corrections and boundaries

Independent source review found corrupted Unicode separators, loss of research query state on the active tab, and a missing reverse provenance check. All were accepted for correction. The provenance regression first reproduced the old client's acceptance of delayed data in Demo mode. A navigation regression checks exact run/comparison/instrument/method preservation. Responsive expanded-state reporting and an icon-only mobile indicator name were also corrected. A browser regression exposed watchlist Escape/focus behavior; the mobile control now uses the actual Radix dialog trigger, and keyboard acceptance verifies focus return.

The review asserted a zero-letter-spacing requirement. No such requirement exists in the repository's design-system typography section. Numeric compression was removed for price legibility; deliberate wordmark/heading spacing remains part of the new visual direction. No added comments, lint suppressions or TypeScript casts were required.

Source review is separate from executed browser acceptance. Reviewer route attestation was unavailable; no Azure-provider identity is inferred from the reviewer label.

Production blockers from the prior phases remain applicable. No qualified historical archive exists. Synthetic results establish pipeline behavior only. Hosted CI, production image/security qualification, lawful external data operation, production TLS/secrets and off-host recovery remain release work. This UI phase does not deploy, merge, push, purchase data, rename the repository or promote legacy models.
