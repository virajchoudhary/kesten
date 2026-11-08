# Kerquant rendered evidence

These are real Chromium captures of the compiled local application. Market prices are Demo observations; research outputs are synthetic pipeline checks. Screens show different selected instruments and interaction states. They are UI evidence, not empirical forecasting results.

| Surface | Before | Kerquant |
| --- | --- | --- |
| Desktop analysis | [Previous accepted terminal at 41a33b7](../../terminal-depth/evidence/kesten-analysis-1440.png) | [Configured 1440×900](kerquant-analysis-1440.png), [1920×1080](kerquant-analysis-1920.png) |
| Phone chart | [Starting 390 px capture](before-markets-390.png) | [Dark](kerquant-markets-390-dark.png), [light](kerquant-markets-390-light.png) |
| Standard workspace | Previous terminal evidence remains archived | [1440 dark](kerquant-markets-1440-dark.png), [1920 dark](kerquant-markets-1920-dark.png), [1440 light](kerquant-markets-1440-light.png), [820 tablet](kerquant-markets-820.png) |
| Native research | [Previous dock](../../terminal-depth/evidence/kesten-research-dock-1920.png) | [1920 dock](kerquant-research-dock-1920.png), [390 focused research](kerquant-research-dock-390.png) |
| History and identity | Previous name remains historical | [Phone research history](kerquant-research-390.png), [sign-in](kerquant-sign-in-390.png) |

The [capture manifest](capture-manifest.json) records five primary routes at four viewport sizes, title/application-name checks, icon HTTP 200, no document overflow, and no captured browser/HTTP errors. It also verifies the served direct-export filename and preserved payload format. Two additional sign-in images and all twenty primary images remain in `.local/kerquant/delivery-frame/`. The functional suite also captures 375 px and light/dark states.

The [summary](verification.json), [browser log](browser-tests.txt), [frontend tests](frontend-tests.txt), [backend results and skips](backend.txt), [build](build.txt), [TypeScript](typecheck.txt), [lint](lint.txt), and [preservation](preservation.json) retain executed outcomes. [Build](build-source-after.json), [browser before](browser-source-before.json), [browser after](browser-source-after.json), and capture source hashes match.

The [mobile regression before correction](mobile-regression-before.txt) failed because the watchlist dialog remained over research. The same assertion passed in the final terminal scenario. The [legacy syntax regression](swot-regression.txt) records the original invalid import and corrected compilation. Recovery and migration receipts are unit checks, not a newly performed PostgreSQL restoration.

The [account-logo regression](account-logo-regression-before.txt) failed on the previous three-bar account glyph and passed after the account header adopted the shared logo. The current measured-frame symbol was selected by the user from the [four-direction R&D board](../assets/logo-rnd-directions.png). [Actual compiled dark](logo-dark.png) and [light](logo-light.png) wordmarks, plus the [header/favicon geometry check](logo-render.json), show the implemented identity. `logo-directions.png` retains the earlier rejected K study as history; it is not the selected design.

No runtime database, credential file, cookie, invitation/reset token, or market archive is included. The [verification record](../VERIFICATION.md) distinguishes executed checks from remaining release boundaries.

Curated text logs have trailing whitespace and redundant final blank lines removed for repository checks. Their messages and outcomes are unchanged. Original command output remains in `.local/kerquant/`.
