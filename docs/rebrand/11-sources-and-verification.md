# Research sources and verification record

Research date: 5 November 2026. Source access is current to this task. Package versions, provider terms, registry status, and support windows must be rechecked when implementation starts. A source's availability does not prove this repository conforms to it.

## Primary-source register

| Subject | Official source read | Decision supported |
| --- | --- | --- |
| Next frontend | [Installation](https://nextjs.org/docs/app/getting-started/installation) | App Router/TypeScript setup, runtime minimum, explicit lint command |
| Next deployment | [Self-hosting](https://nextjs.org/docs/app/guides/self-hosting) | Reverse proxy and multi-instance cache considerations |
| Next trust boundary | [Data security](https://nextjs.org/docs/app/guides/data-security) | Retain Django HTTP API and enforce authorization at the data owner |
| Node | [Release schedule/status](https://nodejs.org/en/about/previous-releases) | Select an LTS runtime; proposed Node 24 rather than an EOL minimum |
| React | [Reference](https://react.dev/reference/react) | Client/server UI composition and ordinary React component boundaries |
| TypeScript | [Strict mode](https://www.typescriptlang.org/tsconfig/strict.html) | Enable strict checks; upgrades can introduce new checks |
| Django support | [Downloads/support table](https://www.djangoproject.com/download/) | Proposed 5.2 LTS lifecycle |
| Django compatibility | [5.2 installation FAQ](https://docs.djangoproject.com/en/5.2/faq/install/) | Python 3.12 is a supported target |
| Django production | [Deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/) | Secret/debug/hosts/HTTPS review and deployment checks |
| DRF | [Requirements](https://www.django-rest-framework.org/) and [authentication](https://www.django-rest-framework.org/api-guide/authentication/) | Supported Django line and session/CSRF boundary |
| PostgreSQL | [Versioning policy](https://www.postgresql.org/support/versioning/) | Proposed supported major and patch policy |
| Celery | [Redis transport](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html) and [tasks](https://docs.celeryq.dev/en/stable/userguide/tasks.html) | Broker visibility/redelivery, task idempotency, acknowledgement trade-offs |
| Celery Windows | [Support history](https://docs.celeryq.dev/en/latest/history/whatsnew-4.0.html) | Linux worker deployment; Windows launcher is not a production support claim |
| Redis | [Official licensing explanation](https://redis.io/de/legal/licenses/) | Version/license selection requires review. Redis 8 lists alternative license choices; no legal conclusion about this product is made |
| Price charts | [Lightweight Charts docs](https://tradingview.github.io/lightweight-charts/), [README](https://github.com/tradingview/lightweight-charts/blob/master/README.md?plain=1), and [LICENSE](https://github.com/tradingview/lightweight-charts/blob/master/LICENSE) | Financial chart engine, license/notice and attribution boundary |
| Other chart product | [Advanced Charts getting started](https://www.tradingview.com/charting-library-docs/latest/getting_started/) | Separate offering; no entitlement assumed |
| PyTorch | [2.10 reproducibility](https://docs.pytorch.org/docs/2.10/notes/randomness.html) and [2.10 serialization](https://docs.pytorch.org/docs/2.10/notes/serialization.html) | Environment-dependent reproducibility and trusted artifact loading, checked against the installed runtime series |
| Accessibility | [WCAG 2.2](https://www.w3.org/TR/WCAG22/) | Proposed AA criteria and manual/automated acceptance |
| Observability | [OpenTelemetry overview](https://opentelemetry.io/docs/what-is-opentelemetry/) | Vendor-neutral telemetry direction; exact SDK integration not tested |
| Yahoo data access | [yfinance documentation](https://ranaroussi.github.io/yfinance/) | Research/personal-use warning; package license is not redistribution permission |
| Vendor data rights | [Massive terms](https://massive.com/legal/terms) and [business terms](https://massive.com/legal/businesses-terms-of-service) | Review actual business contract/entitlements before display/export/training |
| India market data | [NSE data policy](https://www.nseindia.com/static/market-data/nse-data-policy) | Data-sharing/usage review required before India launch |
| India research services | [SEBI 2026 FAQ compilation](https://www.sebi.gov.in/sebi_data/attachdocs/feb-2026/1770375507051.pdf) | Counsel must assess actual research/recommendation scope; no registration/exemption asserted |
| Domain authority | [IANA RDAP bootstrap](https://data.iana.org/rdap/dns.json) | Corrected `.app` and `.in` lookup endpoints |

Use stable documentation lines/branches as compatibility evidence, not a mandate to install whatever `latest` resolves to. The live sites may show changing release banners or future roadmap information. This package chooses supported families, not a certified exact dependency combination. No packages were installed to validate those combinations.

The initial PyTorch `stable` URLs redirected to 2.15 pages in the web tool. Final review questioned that version against the inspected 2.10 runtime. The final references use the directly accessed official 2.10 pages, whose displayed update dates are October 2025. No inference about a 2.15 release date is needed for this blueprint.

## Naming evidence

[Name screening](02-brand-research.md) includes source links for observed conflicts and all four registry-access limitations. Machine receipts cover per-name GitHub search, `.com` status, corrected `.app`/`.in` records, and inconclusive direct Google/Bing checks. [general-name-searches.json](general-name-searches.json) preserves a per-name query and returned source URLs from the final general search pass. [name-variant-searches.json](name-variant-searches.json) records the preliminary variant queries and leads. The search tool's underlying engine coverage is not disclosed, and missing results do not establish business absence.

The package does not claim a completed multi-engine clearance, trademark search, company-registry clearance, package-name reservation, registrar checkout, social-handle availability, or ownership of any proposed brand.

## Local verification

Run the bounded probe from the repository root using the existing backend interpreter:

```powershell
& 'C:\stock price predictor\backend\venv\Scripts\python.exe' -B docs/rebrand/audit_probe.py
```

The script reads source and uses in-memory fixtures. It does not import the Django application, start services, call a provider, train a model, install a dependency, or write the database. The task redirected its JSON output to [audit-probe-results.json](audit-probe-results.json). It deliberately reproduces current defects as discovery evidence; a zero exit code does not mean the financial system passes its future acceptance gates.

The broader syntax sweep found an existing research-example syntax error after an earlier narrower application sweep had passed. The final receipt reports attempted and successful files separately. BSM parity/IV/delta checks and design token contrast passed only for the listed fixtures/pairs. Maximum drawdown, short-period CAGR labelling, and directional-loss gradient defects were reproduced. This evidence supports the recommendations to retain the BSM core and gate model/report claims.

[installed-package-versions.json](installed-package-versions.json) records selected distributions from `importlib.metadata` without importing the application. It identified the unsupported installed Django 5.0.14 line. This makes the proposed supported-version migration concrete, but does not validate a resolver solution or an upgrade.

The full Django suite, provider integrations, browser paths, dependency resolver, production settings check, security exploit test, deployment, backup restore, and out-of-sample evaluation were not run. Import-side effects and the documentation-only boundary explain the distinction; no overall test PASS is claimed.

The two source-audit workers used the `verifier` role. Their own tools did not expose execution identity. The parent correlated each child session's metadata with this chat and its final `turn_context`, which recorded `azure-kmamc/gpt-6-luna` and `max`. This is runtime route evidence, not an independent certification of provider billing/backend internals. Sol owns the consequential synthesis and checked key source sections and offline probes directly.

## Completion checks

The final package check verifies relative links, source-reference bounds, JSON readability, requirement coverage, the application diff, and the preserved database hash. Its result and remaining caveats belong in [package-validation.json](package-validation.json). Independent final review is recorded in [review-notes.md](review-notes.md). Both are package checks; neither changes the production-readiness verdict.

To repeat the integrity check without writing a report, run `python -B docs/rebrand/validate_package.py` from the repository root. It uses only the standard library and Git. The final run passed, with the original database hash unchanged and all new files confined to this directory. Source-reference checks validate paths and line bounds; they do not replace source interpretation.
