# Implementation review record

These are independent read-only reviews by Azure GPT-6 Luna at Max effort, followed by parent-owned corrections and runtime acceptance. They are not a provider-diverse panel, penetration test, legal clearance, or quantitative-model certification.

## Backend review

The initial review returned FAIL. It identified a missing virtual environment in browser CI, browser-cached Basic credentials on research routes, wildcard-subdomain acceptance despite the exact-host policy, and generic cache-failure responses. It also identified the fixed freshness grace window as a contract limitation.

The corrections create and use `.venv` throughout CI, require a non-simple research-client header with staff Basic credentials while preserving session CSRF, reject wildcard host/origin forms, return sanitized 503 cache errors, and configure a bounded EOD grace window. Regression tests cover each case.

A fresh verifier returned PASS for those corrections. It independently ran 27 focused tests and both research-client tests, checked a hostile host startup, exercised session CSRF, and confirmed the original database hash before and after. The parent's final supported suite has 29 passing tests after adding a hand-computed Wilder RSI fixture and retaining the session-CSRF assertion.

The comment review suggested deleting purpose docstrings, manifest sections, and a generated Django migration timestamp. No comment deletions or application suppressions were accepted. The parent retained these conventional file/profile explanations and framework provenance; they do not conceal runtime workarounds or replace executable checks.

## Frontend review

One reviewer attempt failed upstream with HTTP 429 and produced no verdict. A subsequent independent review inspected the source and actual desktop/mobile screenshots and returned FAIL for two concrete issues.

The initial watchlist GET could arrive after a successful POST and visually restore an older list. The correction serializes reads and mutations through the existing loading and pending states. Search waits for the initial read; reload and other mutations wait for a pending mutation. Hook regression tests attempt the forbidden orderings and verify the saved list after completion. This avoids adding background queues or a second store for a private list.

The collapsed data-table control referenced an absent region. It now sets `aria-controls` only while the table region is mounted. A rendering regression checks both states.

The narrow follow-up review confirmed the read/mutation ordering and table ARIA corrections. It returned FAIL for one remaining UI issue: the failed-read Retry button stayed enabled during a save, although the hook correctly rejected that retry. The parent disabled this button during a mutation and added a rendering regression covering Retry, Reload, and Search in the failed/pending state. This last one-line UI correction has parent test acceptance, not a further independent PASS verdict.

The final unit, build, lint, and production-mode browser evidence supersedes earlier runs. The parent owns acceptance of the local milestone. No review verdict is represented as a production-release approval.

## Parent runtime findings

Actual Chromium verification found and fixed the Next-to-Django trailing-slash loop, an invalid Intl date formatter, currency formatting leaking into RSI, chart theme timing, a mobile drawer inheriting centered-dialog transforms, and table disclosure state resetting during range changes. The browser path checks rendered canvas output and table/API agreement, not merely a successful compilation.

The review accepts the initial local workspace only. PostgreSQL/container execution, licensed provider success, invitation/reset/revocation flows, observability, recovery rehearsals, and the blueprint's scientific gates remain open. The preserved legacy algorithms have not been promoted into accepted product calculations.
