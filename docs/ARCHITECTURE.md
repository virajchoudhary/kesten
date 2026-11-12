# Kerquant architecture

Kerquant has a supported terminal/API and a separate collection of preserved legacy research code. Its portfolio demonstration uses synthetic observations. Production is NO-GO.

## Runtime

The Next.js App Router frontend in `web/` uses React, TypeScript, Tailwind, Radix UI primitives, and Lightweight Charts. A same-origin rewrite forwards `/api/` requests to the Django API. Account authentication uses server-side Django sessions and CSRF tokens.

`backend/workspace/` owns instruments, market-provider responses, indicators, and owner-scoped watchlists. `backend/accounts/` owns invitations, password resets, session revocation, and account security. `backend/research/` owns immutable dataset versions, intake receipts, completed baseline runs, exports, and deterministic replay.

The single-command launcher uses an isolated SQLite database under `.local/portfolio-demo/`. It applies additive migrations, creates a random-password demo account, and seeds explicitly synthetic baseline examples. It disables external market providers and legacy scheduling. PostgreSQL support and role-separated migration/recovery tooling remain available.

## Data and computation

API payloads expose source identity, data mode, adjustment basis, and freshness semantics. A provider failure returns unavailable data. It does not silently fall back to synthetic prices.

Research datasets and runs belong to one account. The server validates dataset structure, chronological availability, horizons, and idempotency. Completed results bind dataset identity, engine source, protocol, dependency lock, and runtime versions. Replay checks those bindings instead of fetching mutable market observations.

The supported numerical baseline workload is bounded and synchronous. Optional Celery/Redis and legacy PyTorch research remain separate. No complex model is promoted into the terminal.

## Configuration and operations

Use `scripts/setup.ps1` or `scripts/setup.sh` once, then `scripts/demo.py`. The original `scripts/dev.py` remains for its existing development workspace. `scripts/legacy.py` requires a separately provisioned legacy environment and data; the public clone contains no original database or saved models.

`compose.yaml` defines the local container stack. `deploy/compose.production.yaml` and `scripts/ops/` retain TLS, readiness, recovery, and release qualification procedures. Their presence does not establish production acceptance.

Tests cover numerical behavior, authentication and account isolation, configuration, migration/recovery boundaries, UI behavior, and Chromium workflows. GitHub workflows retain dependency and medium-severity image-security gates. They must not be disabled to publish or deploy.

## Third-party components

Lightweight Charts requires attribution, retained visibly in the terminal, and is licensed separately from this application. Inter and IBM Plex Mono are self-hosted through the pinned font packages. Lucide and Radix packages retain their upstream licenses. See [third-party notices](THIRD-PARTY.md).
