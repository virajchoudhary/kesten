# Phase 5.2 production-readiness qualification

Assessment date: 10 November 2026, Asia/Calcutta. **Release decision: NO-GO.** Local application qualification, a hosted CI result, vendor advisory disposition, public deployment acceptance and empirical research qualification are separate requirements.

This phase preserves the existing research protocol and data. It adds a production-profile acceptance harness and CI configuration, closes the demonstrated PostgreSQL readiness privilege gap, and pins available vendor zlib fixes. It does not deploy, publish images, push a branch, change repository settings, acquire market data or promote a legacy model.

## Scope and source identity

Starting branch: `codex/cadrisyn-foundation`; starting HEAD: `0dcd07ec0f16833a0a7a6afc34ba411f512d83da`. The 24 pre-existing modified/untracked paths were recorded separately and remain outside this phase's commits. These include the original SQLite database, existing workflow edits, the production Compose file and the Windows local-TLS helper.

Application/security candidate source: `6df28a13118c8af709742bfdf244599982bdffab`, exported with `git archive`. Local image labels and file hashes are evidence of the tested local artifact; they are not signed provenance or proof of an uploaded registry artifact. Qualification tooling and configuration hashes are recorded separately because local validation runs in a mixed working tree. In particular, the retained production Compose edits and TLS-helper ACL hardening must not be silently described as committed candidate source.

Focused implementation commits:

| Commit | Change |
| --- | --- |
| `d1239d249724ef79822c29dd0fe381733470e16e` | Readiness rejects database CREATE/TEMP, writable non-system schemas, current/shared catalog ownership and any role membership, in addition to the existing unsafe role attributes. |
| `6df28a13118c8af709742bfdf244599982bdffab` | Available vendor zlib security fixes in application images and explicit infrastructure refresh recipes; PostgreSQL stays on 17.11 and the numerical dependency lock is unchanged. |
| `38088351be52ed00707ee6ae4a16dbf0a379f796` | Production acceptance, safe resource guards, restore-route proof, separate overlay, exact-image CI policy and browser harness. |
| `ed297d99fd4b8134be9425d531459bf9981cae42` | Real-browser non-debug experiment creation, persistence after reload and unchanged five-session replay hash. |
| `17d7300a2bb1641c68435a2f946f3fdca9d9e1f0` | Reject ignored vulnerability matches in collected evidence and CI, with a reproduced false-PASS regression case. |

The final 14-gate run uses committed tooling from `17d7300a` and the five unchanged images built from `6df28a1`. All four execution-time tooling hashes match the current files; the runner, probe and PostgreSQL verifier also match their committed Git blobs. The preserved Windows TLS helper remains uncommitted and explicitly identified. See [tooling traceability](evidence/phase52/tooling-traceability.json). Only documentation and sanitized evidence changed after this run.

## Verification ledger

The final machine-readable evidence and exact candidate image identities accompany this report. A pending or unavailable gate is not counted as a pass.

| Requirement | Current evidence / limitation |
| --- | --- |
| Backend behavior and API contract | VERIFIED: SQLite collected 156 working-tree tests, with 152 passed and four PostgreSQL-specific skips; 156 tests then passed inside the candidate image on PostgreSQL with **zero skips**. The image suite includes 154 committed core tests plus two new readiness tests; the working-tree suite includes two pre-existing local bootstrap tests instead. Generated API schema matches the contract. Initial sandbox temp-directory failures were resolved with a run-local TEMP/TMP directory. |
| Frontend unit checks | 125 tests in 35 files passed; TypeScript and ESLint passed. |
| Readiness regression | VERIFIED: two focused tests and four actual PostgreSQL privilege-drift cases passed. Each live case produced readiness 503 and recovered to 200 after its test privilege was reverted. |
| Production browser behavior | VERIFIED: all three final Chromium workflows passed against the patched, restored HTTPS application: charts/provenance, light/dark themes at 1440 and 390 pixels, Axe checks with zero violations, saved synthetic replay, and a newly created evaluation persisted after reload with the unchanged five-session result hash. Screenshots accompany the evidence. |
| Advisory databases and dependency locks | Fresh Grype database downloaded; database built `2026-11-08T06:19:57Z`, valid. Python pinned-runtime audit and npm production audit found no known package advisories at acquisition time. This does not override OS-image findings. |
| CI configuration | Local actionlint passed for all three workflow files, with ShellCheck disabled because it is unavailable. Workflow guard tests passed. Hosted execution remains blocked. |
| Container, PostgreSQL and recovery | VERIFIED locally: all five candidate builds and 14 production acceptance gates passed. The real dump/restore preserved 27 tables, one archived synthetic intake and two exact saved replays. A restore-only marker was observed and removed through the actual HTTPS API, proving the serving application uses the restore. Source and populated targets were refused. |
| Scientific integrity | VERIFIED regression only: both existing synthetic horizon hashes are unchanged. No empirical dataset or qualified forecast was added. |
| Operational guards | VERIFIED: 49 recovery/qualification/workflow tests passed, including negative cases for source-copy replay, retained volumes, unavailable inventory, missing Windows ACL preparation, wrong image IDs, ignored vulnerability matches, scan waivers and preview-overlay preservation. |
| Preservation | VERIFIED: original SQLite bytes, 496 protected runtime files, 17 research artifacts, 24 pre-existing local changes, 22 retained SQLite files and both previously snapshotted application PostgreSQL stores are unchanged. |

The Django deployment check warns that HSTS preload is not enabled. Local loopback certificates do not justify asserting public-domain preload readiness; no preload certification or registration is claimed.

## Security findings and remediation

### Runtime database-role drift

The prior readiness query checked public relation ownership but missed role membership, routine/type ownership and writable schemas outside `public`. A `NOINHERIT` membership can still permit `SET ROLE`; checking only immediately inherited privileges is insufficient. The health query now uses the catalog boundary already established by the independent Phase 5.1 qualification: all role memberships are rejected, ownership dependencies are checked through `pg_shdepend`, and CREATE privileges are checked across non-system schemas. Database CREATE and TEMP privileges are also rejected.

The acceptance harness creates each representative condition only inside its new project, expects readiness 503, reverts that condition in `finally`, and expects 200 again. It does not grant these privileges in a retained application database.

### Fresh image scans

All five baseline images failed the existing medium-or-higher threshold. Counts below are **scanner matches**, which can include multiple artifacts for one CVE; they are not a count of exploitable application vulnerabilities.

| Baseline image | Critical | High | Medium | Low | Negligible |
| --- | ---: | ---: | ---: | ---: | ---: |
| API, `cb594a4e6753â€¦` | 1 | 4 | 15 | 2 | 1 |
| Web, `4788ee884375â€¦` | 1 | 0 | 3 | 0 | 0 |
| PostgreSQL, `748a18a54d38â€¦` | 3 | 115 | 112 | 40 | 113 |
| Redis, `71885d8cc6e4â€¦` | 1 | 0 | 3 | 1 | 0 |
| Nginx, `583b7f2fce1câ€¦` | 1 | 0 | 3 | 0 | 0 |

Signed Alpine package indexes offered `zlib=1.4-r0` for both selected stable branches, allowing a bounded fix for `CVE-2026-4738` without changing the Python or Node versions. Debian offered `zlib1g=1:1.3.dfsg+really1.3.1-1+deb13u1`, fixing the two zlib matches without upgrading PostgreSQL. These package candidates were checked in disposable containers before implementation. Final scan counts must come from the refreshed immutable images, not these baseline counts.

The exact accepted image IDs were rescanned with the same fresh advisory database, without suppressions. Seven matches were removed: four critical, two high and one medium. **All five images still fail the medium threshold.**

The final collector records zero ignored matches for every image. Grype reports four built-in kernel-header exclusion rules, none of which matched these inventories; no project waiver was configured. A demonstrated collector defect previously hardcoded an empty suppression list, which could mislabel a report with ignored critical findings. A boundary regression test reproduced that false PASS, the collector now rejects ignored findings, and CI checks each image's ignored count independently. All five reports were refreshed with the corrected committed collector.

| Refreshed image | Critical | High | Medium | Low | Negligible |
| --- | ---: | ---: | ---: | ---: | ---: |
| API, `f4e2b685f095â€¦` | 0 | 4 | 15 | 2 | 1 |
| Web, `db27f6fb66dbâ€¦` | 0 | 0 | 3 | 0 | 0 |
| PostgreSQL, `92d4f3d659a2â€¦` | 3 | 113 | 111 | 40 | 113 |
| Redis, `7061e7783118â€¦` | 0 | 0 | 3 | 1 | 0 |
| Nginx, `e0015249adf4â€¦` | 0 | 0 | 3 | 0 | 0 |

Some PostgreSQL OpenSSL hits use generic binary CPE versions. Debian records the installed `3.5.7-1~deb13u3` revision as fixed for examples including [CVE-2026-63073](https://security-tracker.debian.org/tracker/CVE-2026-63073) and [CVE-2026-75803](https://security-tracker.debian.org/tracker/CVE-2026-75803). That is vendor backport evidence, not permission to hide every OpenSSL match.

Debian still marks the selected stable-branch libxml2 vulnerable to [CVE-2026-6653](https://security-tracker.debian.org/tracker/CVE-2026-6653), despite differing vendor/scanner severity assessments. SQLite stable-branch findings and Python/BusyBox CPE applicability require further disposition. No unstable distribution, Python major/minor upgrade, blanket suppression, `only-fixed` filter or weakened severity gate was used to manufacture a green scan.

### Release profiles and research qualification

The independent security audit correctly identified that choosing `historical_research` is not a release-approval mechanism. It is also not a declaration that historical data exists. The existing private research API, operator-controlled intake, dataset provenance and synthetic disclosures remain intact. Requiring a hosted release receipt as a new startup dependency would change this established capability and was not introduced.

Production launch and historical-data/model qualification remain blocked independently. The rehearsal deliberately uses archived synthetic fixtures, validates their exact hashes, and rejects access from the other account. No empirical forecasting performance, calibrated uncertainty, investment recommendation or live-market capability is established by these tests.

## Hosted CI boundary

Read-only GitHub API checks found Actions enabled, `allowed_actions=all`, no SHA-pinning enforcement at repository level, and an empty hosted workflow catalog. GitHub returned HTTP 422 for the starting commit because it is absent remotely. No repository settings, branch, workflows or run were written remotely.

The additive workflow uses read-only permissions, full-SHA action pins, credential-free checkout and separate tested/PR-head/merge identifiers. It is configured locally for source-bound builds, isolated non-debug acceptance and fresh scans. Source-bound hosted execution and required-check enforcement cannot be verified under the no-push boundary. A local parser, actionlint result or workflow test must not be relabeled as hosted CI success. GitHub recommends full-SHA action pins and least privilege in its [secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use).

The final remote read again found zero registered workflows and returned HTTP 422 for application image source `6df28a1`. CI scans use the same five build IDs passed to acceptance, rather than rebuilding separate scan candidates. Artifact uploads explicitly allow only the sanitized receipt, scan summary, SPDX files and vulnerability reports. Hidden-file inclusion is enabled because these files live under `.local`; no secret directory or raw browser log is uploaded.

## Host reliability and operational limits

Docker Desktop exited during API image export. Normal hidden startup restored the daemon; no factory reset, prune, retained-volume deletion, fsync change or WSL relocation was performed. The interrupted export logs were retained. PostgreSQL reported startup data-directory fsync activity after recovery; a running Desktop/WSL process was not treated as database readiness. The exact cause of Desktop's exit is unestablished. This Windows host incident is not a validated production Linux reliability result.

The local rehearsal does not establish public ingress, trusted public TLS, encrypted off-host backups, a separate-host restoration, real alert delivery, secret-vault rotation, operator/on-call ownership, sustained load capacity, signed image promotion or launch approval. These requirements remain **UNTESTED or BLOCKED**, rather than passing through a configuration-only check.

The retained Phase 5.1 preview had no automatic restart policy and remained stopped after Desktop exited. Its original containers were started normally, recovered, and passed the final logical preservation comparison. No migration or fixture command was run against that retained stack.

Clean Windows setup is also **BLOCKED**: ACL-protected TLS preparation currently resides in a pre-existing, uncommitted helper change preserved outside this phase. The new harness refuses Windows secret generation when that hardening is absent. Ubuntu/POSIX preparation already restricts the directory; hosted execution is still untested. Other observed follow-ups are the existing root/peer `pg_isready` log noise (the API readiness probe separately proves actual database access), and the ESLint 9 support warning emitted during the otherwise successful web build.

The production overlay was moved to `compose.production-qualification.yaml` after detecting a collision with the existing preview overlay name. The preview file is restored to its committed bytes. An evidence receipt verifies that the relocation preserved all five earlier running service hashes. A regression test protects the preview ports. The final committed harness then passed all 14 gates in a fresh project using the separate overlay directly, including the Windows startup guard and restore-only route proof. Application image source and numerical behavior remain unchanged.

The final local application is running at `https://localhost:8456/app/markets/` and `/app/research/`, using a job-local CA and disposable accounts recorded privately in `.local/phase52/rehearsal-current/credentials.json`. This is a qualification instance, not a public service. The PostgreSQL application suite used a separate test database in an earlier isolated project with the same five immutable images; its 156-test result is not conflated with the final acceptance project's database.

Evidence: [verification ledger](evidence/phase52/verification.json), [production acceptance](evidence/phase52/production-acceptance.json), [running image/source binding](evidence/phase52/runtime-binding.json), [image scans](evidence/phase52/scan-summary.json), [independent review](evidence/phase52/independent-review.md), and [preservation](evidence/phase52/preservation.json). Full private logs and backup material remain in `.local/phase52`.

Reproduction and safe recovery instructions are in [PHASE52-OPERATIONS.md](PHASE52-OPERATIONS.md). Keep all raw private logs, secret material, databases and backup artifacts in their ignored run directories.
