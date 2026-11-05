# Security, data rights, and operating requirements

Status: release requirements, not completed controls. The current checkout must not be exposed as a public financial service. Source evidence for its gaps is in [the audit](01-repository-audit.md).

## Access model and threat boundaries

R1 is an invite-only, personal research workspace. A user owns watchlists, notes, scenario inputs, and runs. Ordinary users cannot train models, clear shared caches, select filesystem paths, fetch arbitrary URLs, manage entitlements, or access another user's artifacts. Operators have separately audited administrative access. Public pages contain no private research.

| Threat grounded in this repository | Required control | Acceptance evidence |
| --- | --- | --- |
| Anonymous expensive training/evolution requests | Authentication, explicit permissions, operator-only training, resource quotas, queue admission | Anonymous and ordinary-user requests cannot start training; denial creates no run or task |
| Caller-supplied RL session identifiers used in paths | Server-generated run IDs, owner lookup, storage keys built from internal IDs only | Traversal, encoded separators, and a different user's run ID cannot read/write outside the authorized object |
| Broad CORS, debug pages, development key and wildcard hosts | Environment-based secret, DEBUG false, exact hosts, same-origin API, restricted origins | Production settings check and hostile Host/Origin tests pass; debug exceptions reveal no internals |
| Long compute in web requests and daemon threads | Bounded persistent jobs with limits, cancellation, and worker isolation | Worker death/redelivery does not lose status, duplicate outputs, or block ordinary API reads |
| Remote/LLM content inserted into HTML or Markdown | Plain text or sanitized allowlist rendering, CSP, safe URL schemes | HTML/script fixtures do not execute in notes, research, report previews, or model explanations |
| Model files and global JSON progress artifacts | Private artifact store, trusted artifact digests, no arbitrary uploads or pickle loading | Untrusted/corrupt artifact is rejected before deserialization; owner authorization precedes download |
| Shared provider and inference costs | Per-user/day quotas, bounded requests, provider rate limits, operator kill switch | Repeated requests hit quota without additional provider work; no credentials reach browser/logs |

The path-traversal risk is inferred from source, not an exploit demonstrated in this task. The blueprint requires a regression test before any external use. Do not probe an active service or edit shared model files to prove it during discovery.

## Authentication and authorization

Use Django's user and session infrastructure. Secure HttpOnly session cookies, SameSite=Lax by default, session rotation at login, logout invalidation, explicit expiration, and CSRF protection cover the browser flow. Do not store bearer credentials in localStorage. Password reset tokens expire and are single-use. Invite, reset, and sign-in responses avoid account enumeration and have abuse limits. Account recovery cannot rely on displaying a long-lived recovery secret in logs.

Apply CSRF to login as well as authenticated mutations. DRF session authentication alone does not supply a complete safe login flow for anonymous requests. Enforce ownership in querysets and service boundaries, not only in React navigation. Re-check permission for artifact downloads, job status, cancellation, and exports. Role changes and session revocation take effect without a shared cache serving old authorized content.

Operator accounts require MFA before an external preview. An OIDC integration can replace the login method later while preserving Django's authorization model. Do not add parallel NextAuth/Auth.js credentials or a second password database just to obtain a login UI. [DRF authentication documentation](https://www.django-rest-framework.org/api-guide/authentication/) explains the session/CSRF boundary. [Django's deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/) is the release reference for secret, host, HTTPS, cookie, and debug settings.

## Data licensing and provenance

Open-source code licensing does not grant market-data redistribution rights. The [yfinance documentation](https://ranaroussi.github.io/yfinance/) describes personal/research use and directs users to Yahoo's data terms. Do not base a commercial display product on an assumption that the Python package's license permits redistribution.

The existing Polygon adapter is a technical integration, not proof of entitlement. [Massive's terms page](https://massive.com/legal/terms) distinguishes individual and business use; the [business terms](https://massive.com/legal/businesses-terms-of-service) must be evaluated against the actual proposed display, storage, derived-data, and export uses. No subscription or provider account was accessed. Treat the existing provider naming/client as legacy code until supported endpoints and contract terms are confirmed.

For India, the [NSE data usage policy](https://www.nseindia.com/static/market-data/nse-data-policy) governs usage/sharing principles. No direct exchange license, vendor sublicense, or real-time entitlement has been verified. Do not build a production chain feed by bypassing website protections or by treating an unofficial scraper as a data contract.

Before enabling each dataset, the owner records:

- Provider, exchange, instruments, geography, and named contracting entity.
- Display, non-display calculation, storage, derived outputs, model training, and redistribution rights separately.
- Per-user/organization entitlement, delayed/EOD/real-time terms, required attribution, and professional-user restrictions.
- Cache duration, historical retention, correction handling, export restrictions, and post-termination deletion obligations.
- News/fundamental text rights and whether it may be sent to an external LLM or stored as embeddings.
- Approved recurring cost and rate limits.

Only datasets with this record may leave the private research environment. Demo fixtures must be synthetic or owned/licensed for redistribution; a label does not grant rights to copied data. Export services enforce the same rights as the screen. Provider substitution must preserve the declared adjustment, calendar, and provenance or create a new snapshot and visible method change.

## Freshness contract

R1 promises daily historical bars, not live quotes. Display `Daily close`, exchange session date, fetched time, source, and adjustment basis. No blinking live dot appears. A quote timestamp is not equivalent to a fetch timestamp.

Define expected availability by exchange calendar and provider delivery contract. During market closure, the most recent completed session can be current for EOD. During ingestion delay beyond the provider's promised window, show stale. Use a configurable grace interval agreed with the provider; do not hardcode a universal 24-hour stale rule. Holidays, partial sessions, daylight saving changes, missing bars, splits, and symbol changes require fixtures.

`market_state`, `freshness_state`, `data_mode`, and `model_approval_state` remain independent. A provider failure can leave valid cached history, but no fresh market claim. Derived calculations retain the actual input snapshot. Never advance `as_of` just because the user clicked Refresh. Intraday and real-time status are P2 features requiring both feed and entitlement validation.

## Financial and regulatory presentation

The product is scoped as research software in this proposal. That description is not a legal exemption. Do not publish personalized advice, buy/sell/hold recommendations, copied broker branding, or claims of regulatory approval without a review of the actual product and market.

SEBI's [2026 research-analyst FAQ compilation](https://www.sebi.gov.in/sebi_data/attachdocs/feb-2026/1770375507051.pdf) discusses research services and technical-analysis recommendations. This is a reason for counsel to assess an India launch, not a conclusion that this repository is registered or exempt. Other jurisdictions require their own review. A `not financial advice` footer does not decide the classification.

Every result identifies observed, expected, hypothetical, simulated, and backtested values correctly. No published accuracy, Sharpe, return, or success rate comes from a code comment, training score, handpicked example, or in-sample RL history. The [quantitative gates](08-quantitative-verification.md) control model claims. No SOC 2, ISO, exchange approval, investment-adviser status, or accessibility certification is asserted by this blueprint.

## Errors and reliability

Use structured errors with safe messages and a request/run ID. Log the exception internally with a redacted context. Validation errors are permanent until inputs change. Provider timeouts and rate limits may retry with bounded backoff. Infeasible optimization, insufficient data, and unavailable model approval have distinct outcomes. Do not silently replace a failed requested method with another method under the same label.

Set explicit connect/read/total timeouts on provider and internal HTTP calls. A timed-out future is not necessarily stopped work. Isolate expensive tasks in worker processes with limits. Rate-limit both API entry and provider work. A circuit breaker may be added if observed provider failures warrant it; bounded retry and admission limits are required first.

Define separate liveness, readiness, and dependency status. Liveness tests the process. Readiness covers database and required configuration. A chart-data provider outage should degrade market data, not restart healthy API processes indefinitely. Health responses reveal no secrets or internal network topology.

## Observability and proposed service targets

Emit structured JSON logs with request ID, run ID, route, status, stage, duration, provider code, and safe user-scope identifier. Exclude cookies, auth headers, note bodies, prompts, full portfolios, and API keys. Trace API-to-worker execution with propagated correlation IDs. The [OpenTelemetry overview](https://opentelemetry.io/docs/what-is-opentelemetry/) supports a vendor-neutral collection direction; instrumentation selection and export destination need implementation validation.

Track API latency/error rate, queue wait, worker memory/CPU, job retries and timeouts, stale dataset count, last successful ingest per venue, provider quota consumption, cache hit ratio, database connections, artifact failures, and model-version use. Log forecast-origin and artifact identity without private values. Alerts page on meaningful failures, not expected market closure.

Initial operating targets are design budgets, not measured service levels or customer SLAs:

| Measure | Preview target and test |
| --- | --- |
| Cached instrument/bar metadata | API p95 under 500 ms in a 20-user fixture-backed load test |
| Common chart range | Visible data within 2 s at p95 on a defined midrange laptop and 50 Mbps connection, warm service |
| Main UI | LCP at most 2.5 s, INP at most 200 ms, CLS at most 0.1 on agreed test profiles; record sample/environment |
| Run admission | 202 or explicit rejection under 1 s without training in the request |
| Baseline jobs | p95 queue plus execution under 30 s for the curated fixture universe; verify on chosen CPU host |
| Preview availability | 99.5% monthly target for app availability; data-provider freshness is reported separately |
| Recovery | RPO 24 h and RTO 4 h for preview; prove with an actual restore rehearsal |

Rerun capacity tests when the universe, bar frequency, workers, or model family changes. A benchmark must report limiter, work performed, error rate, and environment. None of the targets above is a benchmark result.

## Test strategy and CI/CD

CI has explicit gates for Python import/syntax, lint, selected typing, unit/numeric fixtures, API contracts, PostgreSQL migrations, ownership/CSRF tests, job lifecycle/retry tests, frontend typecheck/lint/build, component behavior, Playwright journeys, both-theme accessibility checks, dependency/secret scans, and container smoke tests. Do not substitute `next build` for lint, or an AST parse for model validation.

Keep deterministic offline checks mandatory on pull requests. Provider contract checks use licensed accounts in a separate controlled environment with capped quotas; they do not call paid services on untrusted PRs. Quantitative evaluation runs use frozen data and pinned code. Any retraining result must pass the approval policy before promotion.

Build immutable images with locked dependencies and recorded image digests. Store no secrets in source, images, or public CI artifacts. Use short-lived deployment credentials, protected environments, and separate development/staging/production configuration. Review migrations and run them once as a controlled release step. Test the previous application against additive schema changes and retain the previous image and configuration for rollback.

Production settings must pass `manage.py check --deploy` in the target environment, with documented disposition for each warning. Smoke tests exercise sign-in, authorized bars, note persistence, owner denial, baseline status, and a stale-provider path. Deploy, DNS, domain purchase, repository rename, production data migration, and customer communication each require the user's authorization.

## Deployment and cost envelope

Use Linux containers for Next, Django/Gunicorn, Celery, and one scheduler. Start with managed PostgreSQL where budget permits, a private Redis broker and cache, private artifact storage, HTTPS termination, and encrypted backups. An 8 GB CPU staging host is a sizing hypothesis for the bounded preview, not measured capacity. Run the smoke/load test before choosing a plan. GPU training, HA clusters, multi-region failover, paid LLMs, and real-time market data are outside R1.

Local discovery has no new service purchase. Proposed recurring budget constraints are at most USD 200/month for preview infrastructure and a separately approved market-data contract. This is a product budget, not a vendor quote or a claim that production can be operated at that price. Data may dominate cost. If rights or capacity cannot fit the approved cap, release only the explicitly synthetic demo variant or reduce scope.

Use one bounded baseline job per user at a time, a configurable daily quota, a curated universe capped initially at 20 instruments, up to five years of daily bars where licensed, and no public retraining. Alert at 50%, 80%, and 100% of approved quotas. At the cap, reject optional new work clearly; never silently incur extra charges. Confirm owner approval before any provider or cloud purchase.

Back up PostgreSQL daily with encrypted off-host copies and test restores. Retention, research-note deletion, audit-log duration, and provider data cleanup need an owner-approved policy before external preview. Proposed defaults are 30-day backup retention and 90-day operational logs with redaction, subject to actual data terms and jurisdiction. Backups and retention do not create a disaster-recovery certification.
