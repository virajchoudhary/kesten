# Phase 5.3 follow-up qualification

Assessment date: 10 November 2026, Asia/Calcutta. **Release decision: NO-GO.** The corrected application builds, runs and recovers locally. All five final image gates still fail the unchanged medium threshold. Hosted CI, off-host recovery and actual production acceptance remain unexecuted.

## Accepted source and delivered fixes

Application candidate: `4862522e6a856882cc4916847ed6453307903e9d` on `codex/cadrisyn-foundation`. Starting HEAD was `91a0cc3bf36cbe28ff55faa101802911621258fe`. The later documentation commit does not change this tested application identity.

| Local commit | Change |
| --- | --- |
| `d4304f8f01682fed0700108c83296ab902bdebfe` | Canonical committed-source exporter and source-bound CI contexts. Validates extracted bytes against Git blobs and records a private hash manifest. |
| `2650696dfda4e0aea896a19fad8d88b088ff3199` | Stable signed-index Kerberos `1.22.3-r0` in the API and libxslt `1.1.43-r4` where already installed. Does not add libxslt to Redis. |
| `bc4fc19832b97882d25f2a26eb728c1ec250bc5d` | Rejects case-colliding directory prefixes before source export. A real failing-before test covers `A/foo` versus `a/bar`. |
| `5add654b7a389456a2b36a5c36a0fca4e84edfa2` | Normalizes exported layer timestamps with `rewrite-timestamp=true` and stops APK from adding build transaction timestamps. Keeps default provenance, package inventory and runtime logging. |
| `4862522e6a856882cc4916847ed6453307903e9d` | Installs and removes the API compiler toolchain within one layer. A failing-before regression prevents temporary build packages from persisting in a lower layer. |

The Windows TLS helper remains the integrated implementation from `54454ebbfc3e8a9fdc0a11ec75542fc76b9c5d33`. Its real owner/SYSTEM ACL checks and failure paths passed again. Both clean source and production startup now use that committed helper. None of the 22 unrelated starting changes were staged.

The new exporter disables Git EOL conversion and external attributes for the archive, rejects unsupported paths, and checks every archive file against its committed blob. An `export-subst` mutation fails rather than silently changing tested content. Independent review found and corrected a directory-prefix collision. An in-memory counterfactual rejects the earlier mixed-working-tree CI build. The archive and complete tree remain private; CI uploads only the sanitized source receipt.

| Service | Exact qualified image ID |
| --- | --- |
| api | `sha256:cf7233b38db1a072a51c0df41673c1f1179cfbdf70a8bd0d88f302fee7d0d920` |
| web | `sha256:a91d601ee6c5e440305d002e1edcc8591f751b633ff356721fadd2694cd2ea1c` |
| database | `sha256:5cb074c424af72768d239358b6c007b513c165e62ec6c8ac33825ec2625f13c1` |
| cache | `sha256:4f15261ed9b8aabbda48e94c09f3c421fa0e7e627215743478712e89073e39bc` |
| gateway | `sha256:328ac272576677f2f27d59e36dd84e1d446041452d4947d70bff81079860897d` |

The actual running images match these IDs. The API's backend Python files match the canonical source, web BUILD_ID is the full candidate hash, and all five main processes are non-root. The [runtime readback](evidence/phase53-followup/runtime-binding.json) and [tooling binding](evidence/phase53-followup/tooling-binding.json) distinguish actual byte verification from the collector's unchanged `source_binding: UNVERIFIED` field. The latter describes its dirty outer checkout, not a verified application-source claim.

## Five image failures and safe remediation limits

The accepted scans use a newly downloaded and validated Anchore `v6.1.10` database built `2026-11-10T06:21:20Z`. Publisher archive SHA-256 is `f536af5882d8e03ad3e3ea5b32b3fc1965d55321ddab67ad7a5d7aeec3725190`. Actual database-file SHA-256 is `6b578d6c5196d1164928c85d0d3a6335f08d54845f5e34705419b62d0325e824`. A new ACL-private task cache was created on D: for space headroom. No existing cache, volume or WSL distribution was moved. The collector's `advisory_database_sha256` hashes its status JSON; the separate freshness receipt records the actual database-file hash.

| Image | Critical | High | Medium | Low | Negligible | Policy |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| api | 0 | 4 | 15 | 2 | 1 | FAIL |
| web | 0 | 0 | 3 | 0 | 0 | FAIL |
| database | 3 | 129 | 110 | 44 | 113 | FAIL |
| cache | 0 | 0 | 3 | 1 | 0 | FAIL |
| gateway | 0 | 0 | 3 | 0 | 0 | FAIL |

There are 431 raw matches. Matches can repeat the same advisory across packages and are not a count of demonstrated exploits. All inventories and scans completed. Every image has zero ignored matches, no project suppressions and no `only-fixed` filter. The four built-in kernel-header rules match nothing. Scanner version is Grype 0.121.2; inventory version is Syft 1.57.0. The [complete finding table](evidence/phase53-followup/scan-findings.tsv) is unfiltered. SPDX and raw scanner JSON remain private with their recorded hashes.

Fresh before/after scans against the same November 10 database retain the same finding counts. The older original Phase 5.3 receipt had 411 matches using the November 8 snapshot. The increase is an advisory snapshot change, not a claimed dependency regression or patch benefit. Kerberos and libxslt maintenance releases were adopted without claiming they remove CVEs absent from this scanner's original matches.

| Image | Remaining blocker and verified action |
| --- | --- |
| API | Kerberos updated. Stable signed-index probes offer no newer BusyBox, SQLite or Python 3.12 candidate for the remaining matches. SQLite `3.53.4-r0`, Python `3.12.16` and BusyBox `1.37.0-r31` remain in the reports. |
| Web | Three BusyBox package matches for CVE-2025-60876 remain. The actual advisory identity was checked against raw JSON. No unrelated CVE was substituted as a fix rationale. |
| PostgreSQL | The previously signed gosu 1.20 update remains installed, with `moby/sys/user v0.4.1`; GHSA-mjcv-p78q-w5fw remains absent. Signed stable repository probe output reports zero upgrades, installations, removals or held packages. The [probe receipt](evidence/phase53-followup/vendor-probes.json) distinguishes retained successful retry exit codes from the PostgreSQL/cache output-only records after the original parallel aggregate was interrupted. Library and CPE findings remain, including the real stable libxml2 concern. |
| Redis | BusyBox `1.37.0-r30` blocks the medium gate. The additional low Redis match remains visible. No unused libxslt package was introduced. |
| Gateway | Existing libxslt updated to `1.1.43-r4`; the three BusyBox matches remain. |

Three pinned official Debian base variants were also inventoried and scanned, without changing application containers or starting services:

| Official base trial | Critical | High | Medium | Low | Negligible | Unknown | Policy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Node 22 Bookworm slim | 2 | 62 | 96 | 19 | 68 | 0 | FAIL |
| Redis 8.10.3 Trixie | 0 | 67 | 65 | 18 | 56 | 0 | FAIL |
| Nginx 1.30.6 Trixie | 31 | 198 | 113 | 25 | 118 | 1 | FAIL |

These are raw base-image trials, not application compatibility tests or proof about every possible Debian build. They provide no qualified green replacement. No OS switch, Python minor upgrade, unstable repository, custom BusyBox build, SQLite removal or scan waiver was used to bypass acceptance. Stable vendor fixes and a compatible, independently qualified replacement remain open paths.

## Reproduction result and its boundary

The Prove It Works principle changed acceptance here: cache reuse was replaced by actual uncached API rebuilds. The first trial failed filesystem-layer equality. Adding BuildKit timestamp rewriting removed general timestamp differences but exposed different APK transaction logs, while the installed package database and world file matched. Suppressing build-only APK log writes removed that difference. One intermediate layer still retained the temporary compiler package and its generated version. Installing and removing those tools in one RUN fixes the remaining layer difference and avoids shipping that lower-layer toolchain.

**The final independent uncached API rebuild passes runtime configuration, creation timestamp and every filesystem-layer hash.** Its first and cold image IDs differ because default provenance envelopes are retained. This is not a whole OCI-index equality PASS. Live signed package indexes remain input dependencies; cross-host, cross-architecture and cold determinism for the other four images remain unqualified. The [accepted cold comparison](evidence/phase53-followup/cold-api-qualified.json) is separate from retained failures [before timestamp rewriting](evidence/phase53-followup/cold-api.json), [after timestamp rewriting](evidence/phase53-followup/cold-api-rewrite.json) and [before single-layer compiler cleanup](evidence/phase53-followup/cold-api-final.json).

## Verification and preservation

| Verification | Actual result |
| --- | --- |
| Final committed-source builds | All five pass. API cold runtime comparison also passes; whole-index identity is not claimed. |
| PostgreSQL backend | 156 pass, zero skips, on the final images and an isolated test database. |
| Operational/research/Windows ACL guards | Canonical-source run executes 90 cases: 86 pass, four SQL cases explicitly skip without their administrator environment. All four then pass separately against isolated PostgreSQL with zero skips. |
| Production-profile gates | All 14 pass, including migrations, TLS, private watchlist/research boundaries, CSRF, four role drift/recovery checks, real dump/restore, source/populated-target refusal and cache/database outage recovery. |
| Real Chromium | Three workflows pass with no API stubs. Markets tested at 1440x900 and 390x844 in both themes, with no page overflow, page errors or Axe violations. Research replay/create/reload passes; responsive screenshots were visually reviewed. This is not a claim of complete application-wide WCAG certification. |
| Frontend | 125 pass across 35 files with two workers. TypeScript and ESLint pass. The initial default-concurrency run had one five-second account-test timeout; isolated account tests and the full bounded run passed without changing assertions or timeout. |
| Static checks | Actionlint 1.7.12 passes with ShellCheck unavailable. Ruff 0.17.3 E4/E7/E9/F checks pass for the four changed Python files. A broader optional style check reports 13 findings; it is not claimed clean. Hadolint was unavailable. |
| Scientific contracts | Exact one/five-session fixture outputs, provenance categories, immutable intake and replay remain intact. No genuine historical evaluation is claimed. |

The PostgreSQL suite uses a separate `test_cadrisyn` database and Redis database 2. Test-only TRUNCATE rights are not added to the serving or retained stores. Four SQL capability tests use a new one-off test container, verified internal TLS and the isolated database's administrator connection. Their role/schema writes roll back. The serving application remains non-root and unprivileged.

The fresh custom-format dump/restore preserves dataset, model and run identities, archived intake bytes, protocol hashes, strict table snapshots and exact replay. A restore-only marker observed and removed through HTTPS proves the app uses the restored database. One-session golden hash remains `9a45a5cca4ce69b11d0ae494f23679a278057ae61b995cf2957d7ea378c19e50`; five-session hash remains `995a224ce3925f972ca224ece6f548d45277ecdd364a50d13998b4649e5f33be`. The prior Phase 5.3 local encryption/tamper-rejection drill remains accepted as unchanged-code evidence, not a newly executed off-host drill.

Preservation verification passed for all **496 protected runtime files, 17 research artifacts, 22 unrelated starting paths, 22 previously inventoried SQLite files and both retained PostgreSQL logical snapshots**. The original database retains its pre-existing local change and SHA-256 `93745bfc1a3149a0f77bbcdd1a50f712195750879f3fb313728ab9811f99715b`. No database or protected file was replaced. No numerical lock, research implementation, authentication implementation or product frontend source was rewritten.

Docker Desktop was found stopped after an interrupted build. A normal CLI start recovered the engine after a long startup. WSL was running and the data filesystem had ample free space. Retained PostgreSQL completed normal crash recovery before logical snapshot checks passed. A frontend build timeout during this recovery was retained as a failure; the subsequent complete source cohort passed. The cause of the earlier stop is unknown. Sustained host/storage reliability is not qualified. No reset, prune, fsync weakening, volume deletion, WSL shutdown or distribution relocation occurred. Only this task's two completed intermediate cohorts were normally stopped, with every container and volume retained.

Bounded fresh reviews found the source-prefix defect, accepted its correction, and independently accepted the final build-layer changes. The [review record](evidence/phase53-followup/independent-review.md) identifies static versus executed scope and the unverified model/provider metadata boundary. Root acceptance separately verifies the actual images, tests and runtime.

## Remaining release requirements

| Requirement | Status and next acceptance |
| --- | --- |
| Five image security gates | **BLOCKED.** All five fail medium policy. Apply a real compatible stable fix, then rebuild and rescan the exact source-bound images without waivers. |
| Hosted CI | **NOT EXECUTED.** Windows ACL/source tests and Ubuntu canonical-source builds, real recovery/browser checks and exact-image scans are configured and locally parsed/tested. No push, dispatch or required-check settings change was authorized. Require real source-bound run URLs after separate approval. |
| Off-host recovery | **UNTESTED.** The operations guide specifies target isolation, encryption recipient/authentication, encrypted transfer, empty-target restore, strict snapshots, replay, browser checks and operator-approved RTO/RPO. No second host was contacted and no bundle transferred. |
| Production operations | **UNTESTED.** Trusted public ingress/PKI, production backup-key custody, registry signing/promotion, rotation, actual alert delivery, operator ownership, capacity and launch approval remain open. Local fixtures and local certificates do not satisfy them. |
| Reproducibility scope | **PARTIAL.** Actual cold API runtime content passes. Cold web/database/cache/gateway builds, identical provenance envelopes and other hosts/architectures are unqualified. |
| Scientific qualification | **NOT QUALIFIED.** No legitimate historical archive has passed rights/provenance/completeness acceptance. All evaluations exercised here are synthetic fixtures, with empirical performance false. No legacy ARIMA/GARCH, BiLSTM/HPO, mean fallback or RL promotion, training or live trading occurred. |

The running isolated application is [Markets](https://localhost:8460/app/markets/) and [Research](https://localhost:8460/app/research/). It uses a job-local certificate and disposable private accounts in the ignored qualification directory. This is a local rehearsal, not a deployment. Reproduction and separately approved hosted/off-host steps are in [Phase 5.3 operations](PHASE53-OPERATIONS.md). The [verification ledger](evidence/phase53-followup/verification.json), exact IDs, raw-finding table and checksums are the acceptance record.

Primary references consulted: [BuildKit reproduction mechanisms](https://raw.githubusercontent.com/moby/buildkit/master/docs/build-repro.md), [MIT Kerberos releases](https://web.mit.edu/kerberos/dist/), [Debian libxml2 advisory status](https://security-tracker.debian.org/tracker/CVE-2026-6653), [Anchore database publisher](https://grype.anchore.io/databases/v6/latest.json), [Docker Desktop daemon log location and limitations](https://docs.docker.com/engine/daemon/logs/) and [PostgreSQL 17 dump/restore semantics](https://www.postgresql.org/docs/17/backup-dump.html). Installed versions and current findings are established by signed-index probes, final SPDX inventories and raw scanner results rather than inferred from release notes.
