# Focused terminal UX pass

9 November 2026. Local development on `codex/cadrisyn-foundation`, starting at `5baa05edec30e14a3ce82f714de9728a39df7d09`. Existing backend contracts, financial calculations, data and model implementations are unchanged.

Implementation commits are `9d71927d365c6f3bc8a846184f1f4dd7de565e74` for the optional offline checker and `a170206d8614f5d72f1d1e3cf7f0045277fe0568` for the terminal and its regressions. The committed production preview is running at `http://127.0.0.1:3000/app/markets`; standalone research and account access remain at `/app/research` and `/app/account`.

## Changes

| Observed problem | Implemented correction |
| --- | --- |
| A 1440 x 720 viewport overflowed by 66px because the terminal required a 690px main area. | Reduce the minimum main/sidebar height while retaining a usable plot minimum. The browser checks the page fits at 720px, 900px and 1080px heights. |
| On a 1920px desktop, three watchlist rows stretched a 474px list area above the selected quote. | Content-size the list, cap long lists and retain scrolling. Quote details follow the actual rows. |
| Expanding the chart from 1440px to 1920px introduced empty leading time space. | Preserve the viewed period with the existing chart library's `lockVisibleTimeRangeOnResize` option. Pan, zoom, Fit and Latest remain available. |
| Mobile inherited conflicting viewport calculations. The initial correction exposed another 93px of unused space below the chart. | Give the phone terminal a flex-column viewport layout. The body receives the space remaining after its actual header and toolbar, including the extra toolbar row at 320px. |
| Small quote and research labels were difficult to read. | Raise compact snapshot/study/research metadata typography, preserve horizontal study scrolling and exact values, and separate chart configuration from comparison/range controls. |
| Secondary panes consumed substantial chart space. | Increase the price pane's share. A 320px research-dock trial left too little analytics visible, so the original 400px default is retained with existing resize and maximize controls. |
| An instrument selected through search could have a quote snapshot without being in the watchlist, leaving no per-row research action. | Add Open research to the selected snapshot. It uses the existing exact instrument route and drawer-dismiss behavior, including for an unsaved instrument. |

The design comparison considered retaining the vertical chart/research stack and introducing a wide-screen research sidecar. The existing stack won because a sidecar reduces both chart and research width and requires more layout behavior. The selected approach preserves the current navigation and resizer. The snapshot action is intentionally discoverable and works for unsaved instruments; it does not create a second research implementation.

The resize correction uses the [official Lightweight Charts time-scale option](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/TimeScaleOptions) and the installed 5.2.1 types. A separate real-browser renderer fixture reproduced the default expansion from 59 to about 80 logical intervals, while the locked chart retained 59. That is a synthetic UI fixture, not market research or a financial result.

## Verification

| Gate | Result |
| --- | --- |
| Frontend units | 125 passed in 35 files, two workers. |
| Lint and production build | Passed. Production build includes TypeScript checking. |
| Initial compiled browser suite | All 16 scenarios in seven suites passed, with existing API throttles and fresh disposable accounts. |
| Final mobile correction | A failing browser assertion recorded 93px of unused viewport. The revised layout was prototyped at 390px and 320px, then rebuilt. All eight affected scenarios passed on the final compiled source, including footer alignment at both phone widths. |
| PostgreSQL backend suite | All 136 tests passed, with no skips. Checks and migration-drift detection passed. |
| PostgreSQL preservation | All 26 public application tables have identical before/after row hashes. Backend source receipt unchanged. Only the dedicated `test_cadrisyn` database was exercised by the tests. |
| Legacy API regression suite | All 23 tests passed in the preserved `backend/venv` environment. |
| PyTorch mechanics | CPU forward shape, finite output, deterministic evaluation and finite backward gradients passed. No optimizer step or model artifact write. |
| Protected data | Original SQLite database, 496 runtime files, 17 research artifacts and 24 initially dirty/untracked unrelated files match retained hashes. |

The full browser pass used source `fdab309412e031528864f47ce8663a10277798643736560943e7b2d33d9f9fdb`. The viewport-only CSS and its new assertion were rebuilt at source `724647d5ff64d42e702acc3ea383435b1c069657e9332e6fe1fd70dfccf4f6ca` and passed all eight affected scenarios. A subsequent actual default-dock capture rejected the shorter dock because its analytics were mostly below the panel viewport. The original default and original keyboard-resize expectation were restored. The final build receipt and affected run are recorded separately in `evidence/build-source-after.json` and `evidence/browser-affected-source-after.json`.

The affected run repeats Markets, Terminal, Terminal depth and Product quality, eight scenarios, using the existing runner's pacing and source guard. Account lifecycle and standalone research logic did not change after the full run. Runs with different source receipts are reported separately rather than described as one final-source full-suite run.

The final eight scenarios passed on source `d508891c1f98c2de94a745bc581ae427ff115e8def54b8be60753fcb624ec263`, matching build and browser before/after receipts. A final geometry check of the running committed application passed at 1440 x 720, 1440 x 900, 1920 x 1080, 820 x 1180, 390 x 844 and 320 x 844. Page height and width match each viewport with no document overflow. The actual retained 400px default dock was separately captured with a saved synthetic result.

The [before/after gallery](screenshots.md) explains the final rendered states. Screenshots and receipts are in `evidence/`. Full raw logs, isolated fixtures, browser helpers and geometry measurements remain ignored under `.local/final-ux-nov9/`. Evidence text copies remove terminal color escapes and trailing whitespace; raw logs remain available. No credential files or database contents are committed.

## PostgreSQL and PyTorch gaps

Docker Desktop was stopped. An unrestricted diagnostic confirmed the missing engine pipe; WSL itself was available. Normal startup restored Docker 29.9.2. The retained Phase 3.5 database and cache were resumed with `--no-recreate`. PostgreSQL completed its own startup recovery. No reset, distribution relocation, volume deletion, password rotation or role change was required. Existing unrelated containers that auto-started with Desktop were left alone.

Current source tests ran on Windows against PostgreSQL 17 in the retained local container, using the existing constrained runtime role and provisioned test database. Application data was hashed read-only before and after. This closes the four previously skipped PostgreSQL concurrency cases. It does not claim a fresh qualification of every application container image or a deployment.

The running frontend preview remains attached to its isolated SQLite development API. PostgreSQL acceptance is a separate current-source test run. No user database was migrated or replaced.

The main API `.venv` intentionally omits the legacy quant stack. PyTorch 2.10.0 CPU was already installed in `backend/venv`; no dependency installation was needed. The new optional checker uses the preserved BiLSTM class and synthetic tensors only. It confirms that the directional penalty still adds no gradient. BiLSTM/HPO, ARIMA/GARCH and RL remain unqualified for promotion. No genuine historical archive, causal out-of-sample model result or calibrated uncertainty was established.

## Local reruns

From the repository root, use the already installed legacy environment:

```powershell
backend/venv/Scripts/python.exe scripts/check_research.py
backend/venv/Scripts/python.exe scripts/check_legacy_torch.py
```

Resume only the retained qualification dependencies:

```powershell
$taskComposeArgs = @('--project-name', 'cadrisyn-phase35', '--env-file', '.local/phase35/preview.env', '-f', 'compose.yaml', '-f', 'deploy/compose.qualification.yaml')
docker compose @taskComposeArgs up --detach --no-recreate --wait database cache
```

The exact host PostgreSQL wrapper remains at `.local/final-ux-nov9/run_pg_current.py`. Run it with `.venv/Scripts/python.exe` from this workspace to repeat checks, source/data hashes and the 136-test selection. It reads the retained private environment without printing secrets and requires the pre-existing test database. For a clean clone or different database, follow [Phase 3.5 operations](../../implementation/PHASE35-OPERATIONS.md) and provision an isolated test target first. Do not repoint these tests at a user's application database or grant test-only permissions there.

For UI verification, use `web`'s production Playwright profile, the existing disposable fixture procedure and `npm run test:e2e:terminal`. See [the earlier audit's reproduction instructions](../product-audit-nov9/verification.md#reproduction). The local affected runner is `.local/final-ux-nov9/verify-affected.mjs` and retains the same 60-second API-throttle pauses.

## Review and limits

A read-only design review compared the two layout choices. A separate verifier inspected the scoped source, initial compiled screenshots, 125-unit/23-legacy test receipts and the full 16-scenario result, and returned PASS with no actionable findings. A fresh independent delta review inspected the phone-height correction, matching source manifests and compiled 390px/320px images and returned PASS. The parent then rejected the smaller research default on its actual capture and restored the existing behavior; no new research implementation was introduced. Verifiers did not rerun the parent's suites. Agent model/provider routing was not independently attested.

The mobile review could not resolve the source hash as a Git ref because it is a source receipt, not a commit ID. Its verdict is bounded to the inspected files and artifacts. The recorded formatter write attempt failed on the test file; formatter success is not claimed. ESLint, TypeScript/build and whitespace checks passed. The vertical viewport assertion is automated; narrow-phone horizontal fit is checked in the rendered images and final browser geometry.

`review-coverage.json` records that the only differences between the reviewed mobile source and the final source are the two files restored to their starting behavior, the dock default and its existing keyboard expectation. The retained five-file web diff is covered by the source reviews. A dedicated comments-review persona was unavailable; the scoped verifier checked comments, suppressions and casts without editing files. No independent model-provider identity or hosted CI result is asserted.

Firefox, WebKit, physical devices and external usability testing remain unverified. Demo prices and synthetic research remain explicit. Future model promotion needs lawful qualified historical data and separate scientific acceptance. No repository rename, public rebrand, push, merge, purchase or deployment occurred.
