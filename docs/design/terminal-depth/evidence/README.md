# Rendered evidence

Historical evidence through `41a33b7`, when Kesten was the local name. “Current” in the original captions below refers to that tested iteration. See [the Kerquant evidence](../../kerquant/VERIFICATION.md) for the subsequent changes. Images and source receipts below are unchanged.

These are actual Chromium screenshots of the compiled local application. Prices and research results are synthetic demonstrations. No empirical forecasting performance is established.

| View | Rejected starting interface | Current Kesten interface |
| --- | --- | --- |
| Daily market, desktop | [Before](before-markets-1440.png) | [Configured analysis at 1440](kesten-analysis-1440.png), [1920](kesten-analysis-1920.png), [light mode](kesten-markets-1440-light.png) |
| Daily market, phone | [Before](before-markets-390.png) | [Dark](kesten-markets-390-dark.png), [light](kesten-markets-390-light.png) |
| Tablet analysis | Starting tablet capture retained locally | [Current 820 px workspace](kesten-markets-820.png) |
| Integrated research | Previous research replaced the chart | [Chart with inspector at 1440](kesten-integrated-1440.png), [1920](kesten-research-dock-1920.png), [focused phone research](kesten-research-dock-390.png) |
| Standalone history | [Before desktop](before-research-1440.png) | [Current stacked phone records](kesten-research-390.png) |
| Public identity and methodology | Earlier names are historical | [Kesten sign-in](kesten-sign-in-390.png), [calculation notes](kesten-methodology-390.png) |

[Verification summary](verification.json), [complete browser results](browser-tests.txt), [frontend tests](frontend-tests.txt), [backend tests and skips](backend.txt), [TypeScript](typecheck.txt), [lint](lint.txt), [build](build.txt), [preservation](preservation.json) and [primary capture metadata](capture-manifest.json) accompany these images.

Build and browser receipts describe the same frontend source. The full before/after source file hashes are retained in this folder. The guard's [negative check](source-guard-negative.json) rejects a mismatched receipt. [The attribution regression](attribution-failing-before.txt) demonstrates the failure before its correction; its final passing result is part of the complete browser run.

Full route captures remain in `.local/terminal-depth/before/` and `.local/terminal-depth/delivery/`, with per-suite screenshots in `.local/terminal-depth/browser-delivery/`. Runtime databases, credentials, cookies and invitation/reset tokens are excluded from this evidence package.
