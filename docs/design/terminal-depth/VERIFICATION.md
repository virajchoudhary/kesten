# Verification and review ledger

Historical local identity for the iteration through `41a33b7`: Kesten. Its evidence below retains the identity and source actually tested. The current identity and verification belong to [the Kerquant iteration](../kerquant/README.md). The earlier [conflict record](KESTEN.md) is historical. This ledger distinguishes checks on the UI from older infrastructure evidence. No hosted CI, deployment or empirical forecasting qualification is claimed.

## Checks

| Check | Executed result | Evidence |
| --- | --- | --- |
| Starting frontend baseline | 76 passed; one account-password test exceeded its 5-second timeout under startup load. Focused rerun passed all three account tests. | `.local/terminal-depth/baseline-unit.txt`; focused rerun output. No timeout limit was weakened. |
| Current frontend tests | 115 passed across 32 files, including numerical display studies, strict settings parsing, storage persistence, private research, export rights/escaping, compact inspector and revisable brand defaults. | `.local/terminal-depth/unit.txt`. |
| TypeScript / ESLint | Passed; final run repeated after review corrections. | `.local/terminal-depth/typecheck.txt`, `lint.txt`. |
| Backend, migrations, contract | 136 tests, 132 passed and four PostgreSQL-only skips. No model changes detected; API schema matches the committed contract. | `.local/terminal-depth/backend.txt`. Existing HSTS preload warning remains. |
| Production frontend build | Kesten build exited 0, including the generated icon route. Source hashes before and after the build match. Intermediate overlapping preview/build processes invalidated an earlier receipt with a Windows directory lock; only verified task-owned processes were stopped, and one build was then awaited to completion. | `.local/terminal-depth/build-release-review.txt`, `build-source-before.json`, `build-source-after.json`. |
| Focused Chromium terminal and depth paths | Both passed before brand integration; superseded visual evidence is retained. | `.local/terminal-depth/browser/terminal`, `browser/depth`. |
| Full compiled Kesten browser suite | **11 scenarios across six suites passed**, including eight real-API scenarios, two isolated UI scenarios and one public-page accessibility scenario. Build, browser-before and browser-after source hashes match. | [Browser log](evidence/browser-tests.txt), [machine-readable summary](evidence/verification.json), [source before](evidence/browser-source-before.json), [source after](evidence/browser-source-after.json). |
| Rendered route captures and metadata | Markets, research, account, data and methodology captured at 1440×900, 1920×1080, 820×1180 and 390×844. All 20 primary captures have no horizontal document overflow; Kesten titles/application-name metadata match and the icon loads with HTTP 200. Two additional sign-in captures are retained. | [Capture manifest](evidence/capture-manifest.json), full originals in `.local/terminal-depth/delivery/`. |
| Preservation | Original database hash matches; 496 protected runtime files and 17 artifacts match manifests; shared credentials match retained copy. | `.local/terminal-depth/preservation.json`. Rechecked at closeout. |

The first paced full-suite attempt passed four account workflows, then failed the markets readiness check because `PLAYWRIGHT_EXTERNAL_SERVER=1` selected the container health default on 8080 for a source preview. The corrected run uses the supported source profile and API health on 8000. This was a test-profile configuration failure, not a passing market check or a backend code defect. No health or authentication assertion was weakened.

## Independent review dispositions

Independent implementation lanes and read-only verifier agents were used. Their configured role is Azure Luna Max; there is no separate provider-routing attestation. Parent integration, actual file inspection and runtime acceptance remain separate from worker reports.

| Verified finding | Correction / verification |
| --- | --- |
| Comparison did not disclose the secondary snapshot's age. | Both instruments now disclose as-of and freshness in the comparison strip. Currency, provider, category and price basis checks remain. Browser scenario asserts disclosure. |
| Reset fit only the time axis. | Reset restores autoscaling on each pane and then fits the time extent. Independent follow-up confirmed the source correction. |
| Annotating a second symbol discarded the first symbol's levels. | In-memory levels are keyed by instrument/data mode. Browser scenario annotates two symbols and verifies the first survives switching back. |
| Normalized levels displayed raw prices without units. | Level labels explicitly identify raw currency values while positioning uses the common normalized anchor. |
| Historical CSV could bypass redistribution restrictions. | Historical generation/download fail before Blob creation; the interface explains the restriction. Negative tests pass. |
| Phone history hid actions outside the initial horizontal view. | Responsive stacked table records retain category, horizon, version and visible Open/Compare actions. [Current phone history](evidence/kesten-research-390.png). |
| Phone toolbar took excessive space and truncated labels. | Two compact rows, short visible symbol labels with unchanged accessible names, usable comparison label. [Current phone chart](evidence/kesten-markets-390-dark.png). |
| Initial dock showed an identifier dump before analytics. | Compact context column beside the research chart; full identities/source evidence in explicit disclosures. Full standalone review remains available. |
| Existing market browser test exposed toolbar overflow at 768 px. | The tablet toolbar now wraps into two controlled rows. The same unmodified 320/768/1024/1440 overflow assertion passed after the correction. |
| Measurement readout obscured library attribution. | A new geometry assertion [failed on the original position](evidence/attribution-failing-before.txt). The readout now sits below the chart legend, away from attribution. The same assertion passed in the final depth scenario; [the current image shows the attribution](evidence/kesten-analysis-1440.png). |
| Chart provenance remained visible when research hid the chart. | Research-only mobile/maximized states show a private-research footer; chart category/interval are hidden. Browser scenario asserts both states. |
| Evidence predated the Kesten revision and lacked source binding. | Final build, complete browser run and primary-route captures share source hash `ff60f80a36b5abc115a6dcd159b006bd046a756c5c771e211fd0e132ada49ffd`. The source guard rejects mismatched receipts. |

Earlier review verdicts were FAIL and are preserved as findings, not relabeled. A mismatched-source receipt was also explicitly rejected by the new source guard. The final read-only review disposition is recorded at closeout. A visual review is not a trademark decision, screen-reader certification, scientific acceptance, or owner product approval.

### Final independent disposition

**PASS for the bounded local UI evidence.** A fresh read-only verifier recomputed the current source hash, matched the build/browser/capture receipts, inspected the final desktop, tablet, mobile, light/dark and research images, and confirmed the earlier corrections. It found no verified remaining blocker in that scope. The scoped comment/suppression review also found no added constraint comments, unsafe casts or lint/TypeScript suppressions in the reviewed feature and harness paths. No code was changed by either review.

The verifier checked recorded test outcomes rather than rerunning the suites or performing additional click testing. It did not re-audit the unrelated dirty backend/release files, requalify containers, clear the trademark, or grant product-owner acceptance. Its initial Git observation preceded the parent's focused commits; the final source hash remained unchanged across those commits. The exact implementation commits are recorded in [implementation-commits.txt](evidence/implementation-commits.txt).

## Limits

PostgreSQL, container recovery, numerical replay and account isolation retain their existing code/contracts and earlier qualification, but the four database-specific skips are not newly executed PASS results. No full infrastructure requalification was requested in this UI phase. Real historical data, empirical skill, advanced model promotion, calibrated uncertainty and live trading remain unavailable. Non-Chromium browsers, comprehensive assistive-technology testing, production operations and public brand clearance remain release gates.
