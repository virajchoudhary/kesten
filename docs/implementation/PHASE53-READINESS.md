# Phase 5.3 security and release qualification

The later [Phase 5.3 follow-up](PHASE53-FOLLOWUP.md) supersedes advisory freshness, canonical-source and cold-build findings below. This original acceptance record remains historical.

Assessment: 10 November 2026, Asia/Calcutta. **Release decision: NO-GO.** One genuine image dependency defect and the Windows clean-source TLS blocker are fixed. All five images still fail the unchanged medium-severity policy. This report does not grant deployment, historical-data rights or model qualification.

## Accepted source and changes

Starting HEAD was `fa7fbc098684bce67377d8782af21193df54c3d6` on `codex/cadrisyn-foundation`. Focused local commits are:

| Commit | Verified change |
| --- | --- |
| `54454ebbfc3e8a9fdc0a11ec75542fc76b9c5d33` | Integrates the previously local Windows TLS ACL helper and tests. Validates SID output, restricts the newly created directory to its owner and SYSTEM, and stops before writing secrets when identity or ACL preparation fails. |
| `4a966faa4f945ed3fd56259db762dc39b2255298` | Updates PostgreSQL's gosu executable to 1.20 with an authenticated upstream public key and detached signature. Preserves PostgreSQL 17.11, its base, runtime UID and database configuration. |
| `2e5f63d60c37ea60e94b6368125a9f31bd2e0ce2` | Adds Windows ACL CI coverage and supplies the source timestamp to all five builds. This is the frozen application/qualification source used below. |

The five images were built from a Git archive, not the dirty working directory. Acceptance used that archive's committed helper and configuration content. The outer checkout retains 22 unrelated changes. The other two starting paths are the explicitly authorized TLS helper/test now integrated above.

The Windows archive exported seven tooling/configuration text files with CRLF. Every execution-time hash matches that exact archive, and normalized content matches the committed blobs. A separate `core.autocrlf=false` export matches all seven Git blobs byte for byte; it was not substituted into the already qualified images. [Tooling binding](evidence/phase53/tooling-binding.json) records this distinction. Cross-host byte identity is not inferred from semantic equality.

## All five image failures investigated

Signed Alpine stable indexes confirm that BusyBox `1.37.0-r31` on 3.24, `1.37.0-r30` on 3.23, SQLite `3.53.4-r0`, OpenSSL `3.5.9-r0` and the installed zlib fixes are current candidates. Debian's signed stable indexes offer no newer versions of the checked libxml2, OpenSSL, SQLite, libc or Perl packages. A full `apt-get --simulate upgrade` on the new PostgreSQL candidate reports **0 upgraded, 0 newly installed, 0 removed and 0 held back**. No package was installed in that probe.

The official Python, Node, Redis and Nginx indexes are unchanged. PostgreSQL's current index differs only for riscv64; its amd64 manifest is identical to the previously pinned one. Changing that index would not repair the qualified runtime and receives no security credit.

The actionable exception was `/usr/local/bin/gosu`. Its old Go module `github.com/moby/sys/user v0.1.0` matched [GHSA-mjcv-p78q-w5fw](https://github.com/moby/sys/security/advisories/GHSA-mjcv-p78q-w5fw). [Upstream gosu 1.20](https://github.com/tianon/gosu/releases/tag/1.20) embeds the fixed `v0.4.1` dependency. Both host and isolated Linux checks verified the release signature against fingerprint `B42F6819007F00F88E364FD4036A9C25BF357DD4`, rejected a deliberately corrupted binary, and the Linux check executed as UID 65534. The final SBOM reports `v0.4.1`, and the advisory is absent from the new scan.

Fresh scans of the exact five accepted image IDs show:

| Image | Critical | High | Medium | Low | Negligible | Medium policy |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| API | 0 | 4 | 15 | 2 | 1 | FAIL |
| Web | 0 | 0 | 3 | 0 | 0 | FAIL |
| PostgreSQL | 3 | 113 | 110 | 40 | 113 | FAIL |
| Redis | 0 | 0 | 3 | 1 | 0 | FAIL |
| Nginx | 0 | 0 | 3 | 0 | 0 | FAIL |

There are **411 raw matches**, one fewer than Phase 5.2. Matches can duplicate advisories across packages and do not equal exploitable application vulnerabilities. All reports completed, all inventories succeeded, and every image has zero ignored matches. Four built-in kernel-header rules matched none. There are no project waivers, `only-fixed` filters, weakened thresholds, metadata stripping or alternate unstable repositories.

Remaining API failures include SQLite findings and Python/BusyBox applicability. The three minimal Alpine services remain blocked by BusyBox matches. PostgreSQL has unresolved stable-library findings and generic CPE matches. Debian backports resolve some upstream-version OpenSSL matches, but [libxml2 CVE-2026-6653](https://security-tracker.debian.org/tracker/CVE-2026-6653) remains a real stable-branch concern; a backport explanation is not a blanket exemption. A database distribution switch, Python minor upgrade, custom BusyBox build or removal of supported SQLite functionality would require separate compatibility evidence. None was used to manufacture a green scan.

The publisher's current [Anchore database pointer](https://grype.anchore.io/databases/v6/latest.json) still identifies the 8 November database. A new download timed out during extraction and remains separate. Scans used the existing complete database only after its actual SHA-256 and current source checksum were verified. Direct Python metadata access returned HTTP 403; the publisher metadata was read through the available web tool, without disabling TLS or bypassing access controls. [Advisory freshness](evidence/phase53/advisory-freshness.json) records cache reuse honestly.

## Runtime and recovery acceptance

| Requirement | Current evidence |
| --- | --- |
| Builds and source | Five builds passed. The actual API's 126 Python source files match the frozen archive; web BUILD_ID matches `2e5f63d`. All five main processes are non-root. Image IDs are in [images.json](evidence/phase53/images.json). |
| Windows secret preparation | Three tests passed, including real ACL enforcement and malformed-SID/ACL-failure paths. The full production harness used the committed helper successfully. The former dependency on an uncommitted helper is resolved. |
| Application database | **156 PostgreSQL backend tests passed, zero skips**, in a separate `test_cadrisyn` database and Redis database 2. Test-only TRUNCATE permissions were not granted to the serving or retained stores. |
| Operational checks | **77 tests passed**, split into 59 recovery/release/qualification checks and 18 research/migration/preflight checks. Initial sandbox TEMP permission failures were retained; the passing run used workspace-local temporary directories. |
| Production profiles | **All 14 gates passed** from the frozen archive: new migrations, authenticated TLS, private watchlists/research, CSRF, provenance, four privilege-drift/recovery cases, real dump/restore, source/populated-target refusal and database/cache outage recovery. |
| Recovery and scientific identity | The actual dump/restore preserved 27 tables, one archived synthetic intake and two saved replays. A restore-only marker observed and removed through HTTPS proves the serving API uses the clone. Both one/five-session golden hashes are unchanged. |
| Browser and frontend | **Three real Chromium workflows passed** on the restored stack, including new non-debug evaluation creation and reload/replay. Desktop/mobile, both themes and zero Axe violations were checked. **125 frontend tests**, TypeScript and ESLint passed. Final screenshots were visually reviewed. |
| Static checks | Actionlint 1.7.12 and Ruff 0.15.17 passed. ShellCheck and hadolint were unavailable; neither is claimed passing. |
| Local encrypted recovery | A new ACL-private synthetic backup was encrypted with AES256, decrypted byte for byte and checked against its hash. Corrupted ciphertext failed decryption. No backup or key was transferred off-host. |
| Independent review | A fresh scoped read-only review passed the six changed source/test files with zero Standards/Spec findings and independently reconstructed the key fingerprint. It did not execute Docker or hosted CI. [Review scope](evidence/phase53/independent-review.md) separates that verdict from runtime acceptance. |
| Preservation | Original database bytes, 496 protected runtime files, 17 research artifacts, 22 unrelated paths, 22 previously inventoried SQLite files and both retained application PostgreSQL logical snapshots are unchanged. |

The SQLite full backend suite was not repeated; the current full PostgreSQL suite and SQLite recovery guards were run. No numerical dependency lock, research protocol, backend research/authentication implementation, frontend product code or historical artifact was changed. Synthetic checks establish reproducibility contracts, not empirical forecasting performance.

## Reproduction findings and remaining release gates

All five repeat builds have identical runtime configuration, creation timestamp and filesystem layer hashes. Their **top-level Docker IDs differ**. A streamed comparison of the Redis OCI export proves the runtime manifest is identical and the provenance attestation manifests differ. These results are retained rather than relabeled as an image-ID equality PASS. Independent cold-build determinism, whole-index identity and cross-host byte reproduction remain unqualified. The live apt/apk indexes are an additional input boundary.

Hosted CI is configured but **not executed**. No source or workflow was pushed, no run dispatched and no repository settings changed. The Windows job and Ubuntu source-bound qualification/scan job still need a real approved hosted run and required-check acceptance.

Actual off-host transfer/restore, production encryption-recipient custody, public PKI/ingress, capacity, secret rotation, real alert delivery, on-call ownership, signed registry promotion and launch approval remain **UNTESTED**. Local encryption and local TLS do not satisfy those gates. No historical archive has passed qualification and no legacy complex model is promoted.

Docker Desktop was initially stopped, became ready after normal startup, and later recorded an orderly shutdown of unknown origin. A normal CLI start recovered it. No reset, prune, retained-volume deletion, fsync change or WSL relocation occurred. Both retained database snapshots subsequently matched. Sustained host reliability is not established. Two automatic approval-review requests failed with router/service errors; the required final read-only preservation check succeeded through review on retry. These failures were not unsafe-action verdicts or bypassed gates.

The running local qualification application is [Markets](https://localhost:8457/app/markets/) and [Research](https://localhost:8457/app/research/), with a job-local certificate and disposable private accounts. This is not a public deployment. Reproduction, hosted CI and separately authorized off-host procedures are in [Phase 5.3 operations](PHASE53-OPERATIONS.md). The [machine-readable ledger](evidence/phase53/verification.json), unfiltered finding table and checksums provide the release evidence. Raw credentials, keys, logs and dumps remain private under `.local/phase53`.
