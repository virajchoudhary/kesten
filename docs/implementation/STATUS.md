# Cadrisyn implementation status

On 2026-11-06 the private foundation milestone passes local runtime acceptance on `codex/cadrisyn-foundation`. Cadrisyn remains a temporary working name. External release, merge, deployment, domains and spending remain unapproved.

The running container entry point is [daily markets](http://127.0.0.1:8080/app/markets). [Account security](http://127.0.0.1:8080/app/account) supports password changes and other-session revocation. Operator-issued invitation/reset links use one-use fragment credentials. Existing analyst credentials stay in ignored `.local/credentials.json`.

The workspace retains candles, volume, SMA20/SMA50, Wilder RSI14, curated instrument search, price tables, private watchlists, themes and responsive navigation. Demo provenance is explicit. No licensed live feed is configured. Personal historical data is gated and unavailable outside development; failures never substitute demo data.

PostgreSQL, Redis, one-shot migrations, API, standalone Next frontend and gateway now run locally. Separate runtime/migration roles, retained-volume upgrades, safe backup/restore, readiness and revocable sessions have executable evidence. The original database and all 496 preserved runtime files remain unchanged. Existing quantitative research remains preserved with its original verification limits.

Current checks pass: 78 PostgreSQL tests, 23 offline legacy tests, 29 frontend tests, 17 recovery tests on each OS, 6 transfer tests, 13 gateway checks and 5 browser scenarios. The browser total comprises 3 actual API journeys and 2 isolated UI scenarios. Static checks, optimized builds, cold startup, 20-object transfer and PostgreSQL restore/sign-in pass. SQLite skips three PostgreSQL-only concurrency cases. Optional HSTS preload warning remains.

Use [phase-two results and receipts](PHASE2.md), [foundation operations](FOUNDATION-OPERATIONS.md), and [independent review dispositions](REVIEW.md). Earlier receipts remain historical; their earlier Docker/account/recovery blockers are superseded by phase two.

External release still requires TLS, production secrets/ingress, licensed data rights, hosted CI, image scanning, off-host backup/recovery policy and cutover rehearsal, host qualification, observability ownership, load/cost budgets and broader accessibility/browser checks. Quant tools require the separate [model-verification gates](../rebrand/08-quantitative-verification.md). This is a verified local foundation without a production deployment or certification claim.
