# Product blueprint and approval gate

**Historical package.** The architecture was subsequently provisionally approved and implemented. The user selected **Kesten** on 8 November 2026 for the local redesign. Current identity and unresolved public-use conflicts are recorded in [the Kesten decision](../design/terminal-depth/KESTEN.md). The original proposals below are retained as history, not current naming recommendations or clearance.

Status: discovery complete, awaiting brand and architecture approval. Research date: 5 November 2026, Asia/Calcutta. No implementation, deployment, repository rename, purchase, training run, or certification is authorized or claimed by this package.

## Recommendation

Develop **Cadrisyn** as the leading brand concept, with Basisfold and Apertane as alternatives. The five screened proposals also include Lattivor and Tessivane. A preliminary software soundalike lead lowers Apertane's rank. No proposed name has trademark clearance. Exact-name GitHub searches and registry responses are recorded, while direct Google/Bing checks and trademark databases have explicit limitations.

Build a daily-market research workspace that connects an instrument's chart, dated evidence, a plainly labelled baseline, and saved private research. Use Next.js, React, and TypeScript for the product interface; retain Django and reviewed Python/PyTorch code behind versioned APIs. Add PostgreSQL, durable Celery jobs on Linux, separate broker/cache processes, and immutable data/model records.

The first release is deliberately narrow. It contains sign-in, a curated daily chart workspace, watchlists, source/freshness inspection, notes, and a next-session last-close baseline. ML, allocations, full backtesting, and derivatives follow only as their calculations and user paths pass acceptance. Licensed EOD data or explicitly synthetic demo fixtures are the only proposed R1 data modes. No real-time feed is assumed.

## Why this scope

The source audit found useful BSM, BL, indicator, optimizer, and reporting work. It also found deployment configuration gaps, unauthenticated expensive paths, caller-controlled file identifiers, historical-scaler leakage, target/metric mismatch, in-sample RL evaluation, and incorrect report metrics. A new visual shell cannot repair those problems by itself.

The bounded offline probes reproduced a missed initial drawdown, a short-period CAGR-label problem, and an ineffective directional-gradient penalty. European BSM parity, IV recovery, and delta matched their fixture expectations. A broader syntax sweep found an existing error in one research example. These are discovery findings, not a full-suite or model-performance verdict.

## Read the package

| Artifact | What it decides or records |
| --- | --- |
| [01 Repository audit](01-repository-audit.md) | Current features, architecture, dependencies, source findings, preservation choices, tests, and deployment blockers |
| [02 Brand research](02-brand-research.md) | Five ranked names, conflicts, domain/GitHub evidence, registry access, and unverified checks |
| [03 Brand concepts](03-brand-concepts.md) | Positioning, voice, tagline, typography, palette, icons, and logo directions for three names |
| [04 Design system](04-design-system.md) | Light/dark tokens, components, chart language, responsive behavior, and accessibility |
| [05 Product specification](05-product-specification.md) | Audience, site map, page specifications, journeys, and interactive states |
| [06 Architecture](06-architecture.md) | Target stack, alternatives, domain records, API/job contracts, and migration boundaries |
| [07 Security, data, and operations](07-security-data-operations.md) | Auth, threat controls, licensing, freshness, errors, telemetry, CI/CD, deployment, and budget |
| [08 Quantitative verification](08-quantitative-verification.md) | Financial conventions and objective data/model/portfolio/backtest/derivatives gates |
| [09 Migration roadmap](09-migration-roadmap.md) | P0/P1/P2 scope, dependencies, acceptance, risks, estimates, and R1 definition |
| [10 Approval gate](10-approval-gate.md) | Concrete owner decisions and separate external-action approvals |
| [11 Sources and verification](11-sources-and-verification.md) | Current official-documentation register, local check scope, and evidence limitations |
| [Review notes](review-notes.md) | Independent package review and dispositions |
| [Decision trail](decisions.tsv) | Choices, reasons, evidence, and outcomes |

## Discovery workflow and completion predicate

- [x] Read the Principles section of the poteto-mode skill.
- [x] Phase A: Frame. Define a code-grounded product specification and preserve existing application work.
- [x] Phase B: Design the workflow. Separate application/quant source audits from parent-owned research and decisions.
- [x] Phase C: Run the loop. Confirm consequential findings against source, current official documentation, and bounded numerical probes.
- [x] Phase D: Keep the audit trail. Record decisions and their evidence in `decisions.tsv`.
- [x] Phase E: Verify and hand back. Validate links, references, requirement coverage, independent review, and unchanged application/database bytes. Stop at approval.

The completion predicate is a reviewable specification covering all nine requested subjects with a concrete decision, supporting evidence, or a named unresolved approval dependency. It does not require making the existing application production-ready. The Experience First principle narrowed R1 to a coherent workflow. The Prove It Works principle required actual source/fixture checks and separate unverified gates.

Two read-only source-audit lanes covered application/security and quant correctness. The parent retained naming, product/architecture decisions, documentation, and final acceptance. All task-created artifacts live under `docs/rebrand/`. The pre-existing database change is preserved. No broad refactor or cleanup has been performed.

The [final package check](package-validation.json) passed for link/reference integrity, required artifacts, JSON readability, and preservation. The [independent review](review-notes.md) initially required four evidence corrections, which the parent applied and checked. This is discovery-package acceptance, not application or quantitative release acceptance. The full application suite and UI paths remain unverified.

## What needs approval

Choose the brand concept and accept or revise the proposed architecture and R1 scope using [the approval gate](10-approval-gate.md). Legal naming clearance, intended launch market/entity, data rights, budget, retention, and actual deployment remain separate decisions. Discovery stops here.
