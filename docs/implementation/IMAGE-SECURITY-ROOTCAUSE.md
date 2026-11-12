# Image security root cause and disposition

Assessment: 12 November 2026, Asia/Calcutta. **NO-GO.** No safe supported package update remains available for the recorded findings. All five existing image gates remain failed; this analysis does not waive them. No images were rebuilt, no application code changed, and previously passing application qualification was not repeated.

The starting checkout is `2e4627dc5a2441783d84f4cd1adc08e4ae6471f4`. The exact application images remain those built from `4862522e6a856882cc4916847ed6453307903e9d`. Current Docker readback verified all five immutable identities against the recorded cohort. The [identity receipt](evidence/image-security-rootcause/image-identities.json) includes filesystem layers and entrypoints.

## What the 431 rows mean

| Measure | Count | Meaning |
| --- | ---: | --- |
| Raw scanner matches | 431 | Every original row retained, including duplicated package and metadata representations. |
| Exact advisory identifiers | 169 | All are CVE identifiers. No fuzzy alias merging. |
| Source-name/advisory pairs | 179 | Distribution source names are retained; Alpine `sqlite` and Debian `sqlite3` remain separate fix targets. |
| Image/source/advisory pairs | 182 | One source issue can affect several images, including four BusyBox instances. |
| Source labels | 34 | Package source or inferred upstream identity, not 34 independently running services. |

Of the 431 rows, **270 meet the existing medium threshold**, spanning 102 advisory IDs and 111 source-name/advisory pairs. The other 161 rows are Low or Negligible, not independent reasons for a medium gate failure. This is a policy count before any explanatory assessment; it is not an exploit count. [Severity accounting](evidence/image-security-rootcause/severity-breakdown.json).

PostgreSQL accounts for 399 rows. Its 368 Debian-namespace matches contain 347 package-database matches and 21 additional source identities inferred from ELF metadata. For example, `systemd` can be inferred from libsystemd/libudev without an installed service manager; `gcc-14` is inferred from runtime libraries. Another 31 rows use generic NVD CPE versions. The other images contribute 32 rows, including twelve representations of one BusyBox CVE.

The [169-advisory index](evidence/image-security-rootcause/advisories.json), [179 case decisions](evidence/image-security-rootcause/case-decisions.tsv), [34-source dependency census](evidence/image-security-rootcause/dependency-census.tsv) and [431 normalized rows](evidence/image-security-rootcause/findings.json) provide complete cross-links to the original hash-bound reports. These are different counting units, not interchangeable estimates of exploitable vulnerabilities.

## Classification, without policy exemptions

| Disposition | Source/advisory pairs | Raw rows | Verified meaning |
| --- | ---: | ---: | --- |
| Debian vendor backport installed | 28 | 28 | Native source-package versions meet the vendor's fixed versions. Embedded binary version strings miss those revisions. |
| Debian stable source remains open | 129 | 370 | Current Trixie tracker still records open issues and signed package indexes offer no update. Individual affected components and reachability vary. |
| Required component absent | 2 | 2 | The sudo-specific Kerberos match and SQLite CLI `.recover` match do not describe installed affected executables. |
| SQLite upstream fix not packaged | 10 | 10 | Alpine still supplies 3.53.4-r0; selected vulnerable features are compiled in. |
| Python compatible fix unqualified | 7 | 7 | No verified 3.12 package remedy. Module/input prerequisites and incomplete transitive-call evidence are recorded individually. |
| Upstream-disputed Python advisory | 1 | 1 | `pkgutil.get_data` has the same trust boundary as filesystem opening; upstream reverted attempted restrictions. |
| Redis release source disagrees with CPE | 1 | 1 | The recorded wildcard match does not capture the guarded arithmetic in the Redis release source. |
| BusyBox fixed stable package unavailable | 1 | 12 | Native local-only probes reproduce the affected wget behavior in all four exact Alpine images. |
| **Total** | **179** | **431** | **Nothing removed or suppressed.** |

The [classifier summary](evidence/image-security-rootcause/summary.json) remains `NO_GO`, with `classification_changes_policy=false`. Explanatory assessments are not VEX waivers, allowlists or replacements for the medium-severity image policy. The original five raw scan results remain `FAIL`, with zero ignored matches.

## Confirmed backports and the three Critical rows

The exact PostgreSQL image contains OpenSSL `3.5.7-1~deb13u3`, gzip `1.13-1+deb13u1`, MIT Kerberos `1.21.3-5+deb13u1` and XZ `5.8.1-1+deb13u2`. Current Debian data plus native `dpkg --compare-versions` confirm 23 OpenSSL, two gzip, two Kerberos and one XZ fix already installed. [All 28 comparisons](evidence/image-security-rootcause/verified-backports.json) pass. Package verification reports only 402 inherited missing documentation/manpage files, with no content-checksum mismatches in the checked packages. This task removed no files or package metadata.

The two Critical OpenSSL matches, **CVE-2026-63073** and **CVE-2026-75803**, are fixed by Debian from `3.5.7-1~deb13u2`. Replacing the installed Debian build merely because its embedded string says 3.5.7 would ignore vendor backports. [Debian CMP advisory](https://security-tracker.debian.org/tracker/CVE-2026-63073), [Debian AEAD advisory](https://security-tracker.debian.org/tracker/CVE-2026-75803).

The remaining Critical, **libxml2 CVE-2026-6653**, is genuinely open in Trixie. Its installed version, `2.12.7+dfsg+really2.9.14-2.1+deb13u3`, contains a reverted 2.9.14 codebase. Its leading version cannot be compared naively with upstream 2.11. Debian's `no-dsa (Minor issue)` is a prioritization decision, not a patch. Newer source lines have a fix, but no supported installed-distribution candidate is available. [Debian status and version-reversion notes](https://security-tracker.debian.org/tracker/CVE-2026-6653).

The parser is linked into the actual PostgreSQL executable. An SQL caller can reach XML parsing; no application XML or raw-user-SQL endpoint was found. The qualified database has no published port, runs as UID 999 with zero effective capabilities, uses TLS/SCRAM and no-new-privileges, and is on the internal data network. SQL injection, stolen database credentials or future XML functionality would change exposure. These boundaries reduce access, not the underlying defect. [Actual process/network receipt](evidence/image-security-rootcause/qualified-database-exposure.json), [PostgreSQL XML behavior](https://www.postgresql.org/docs/17/datatype-xml.html).

## BusyBox, SQLite, Python and Redis

**BusyBox CVE-2025-60876 is reproduced.** Each exact Alpine image sent the harmless `X-Kerquant-Probe` header injected through URL control bytes to its own isolated loopback fixture. Docker networking was disabled; no external service, credentials or database were used. API/web/gateway use r31; Redis uses r30. The package trio `busybox`, `busybox-binsh`, `ssl_client` represents one source bug per image. No tracked application wget invocation was found. The applet remains usable by an operator or compromised process. [Native four-image evidence](evidence/image-security-rootcause/wget-loopback-evidence.json).

An [upstream rejection patch](https://lists.busybox.net/pipermail/busybox/2025-November/091840.html) and [later encoding proposal](https://lists.busybox.net/pipermail/busybox/2026-June/092347.html) exist. Neither establishes a fixed, signed Alpine 3.23/3.24 package. No newer stable candidate was found. A custom BusyBox fork would need its own package provenance, maintenance and compatibility qualification; changing a version label or adding GNU wget would not remove the vulnerable BusyBox applet. Those are not accepted remediations here.

**SQLite retains useful functionality.** The API library enables FTS3/4, FTS5, RTree, Session and secure-delete features. The ten library issues have crafted SQL, database, WAL or changeset prerequisites. Production requires PostgreSQL; local migration/recovery still opens operator-selected SQLite files. Read-only opening does not make parser flaws harmless. Removing SQLite to quiet the scan would lose supported functionality. The `.recover` issue, CVE-2026-119586, requires the absent native SQLite CLI and is distinct from library parsing. Upstream 3.54.0/3.54.1 exists, while signed Alpine candidates remain 3.53.4-r0. [Compile-feature evidence](evidence/image-security-rootcause/feature-evidence.json), [SQLite release history](https://sqlite.org/changes.html).

**Python's eight rows need module-level treatment.** Base64 alphabet/padding, IMAP/POP command input, malformed HTTP framing, NUL-containing host/port, inline JavaScript cookie helpers and resource paths are separate prerequisites. Native checks reproduce permissive alternate-alphabet decoding and numeric-host NUL truncation. A strict-padding test rejects the tested extra segment; that does not qualify every decoding mode. No direct application call to the affected decoder, IMAP/POP or JavaScript-cookie helper was found. A loopback urllib health probe is a known indirect HTTP consumer; framework/transitive paths were not exhaustively proved absent.

Python 3.12.16 remains the published 3.12 release. An interpreter-minor change is not an in-place patch for the current research environment: [replay.py](../../backend/research/replay.py) requires exact Python/dependency runtime equality. Some upstream Base64 changes deprecate behavior rather than eliminate it. No blanket "upgrade Python and all eight disappear" claim is made. [Python releases](https://www.python.org/downloads/source/), [alternate-alphabet advisory](https://mail.python.org/archives/list/security-announce%40python.org/thread/KRI7GC6S27YV5NJ4FPDALS2WI5ENAFJ6/), [pkgutil clarification](https://github.com/python/cpython/pull/148197).

**Redis CVE-2025-49112 is not established in this release.** The description concerns Valkey, while Grype applies a wildcard Redis CPE with no version bound. The tagged Redis 8.10.3 `setDeferredReply` source checks `prev->used < prev->size` before subtraction. This is release-source evidence, not a live exploit test or permission to remove the finding. [Exact release code](https://github.com/redis/redis/blob/8.10.3/src/networking.c#L3845-L3852), [maintainer discussion](https://github.com/redis/redis/issues/14199).

Other Debian sources remain represented individually in the census. Runtime libstdc++ issues must not be dismissed as an absent compiler. KDC/kadmind, systemd daemons, local privileged tools and architecture-specific code have different prerequisites from a linked library. Four old scanner rows lacked descriptions; current Debian records identify KDC/kadmind paths. SCRAM authentication does not itself prove GSS encryption negotiation unreachable, so no blanket Kerberos non-exposure claim is made. [PostgreSQL GSS encryption](https://www.postgresql.org/docs/17/gssapi-enc.html).

## Verification, scope and stop decision

The Prove It Works principle changed this audit from version guessing to native package comparisons and four isolated behavioral reproductions. Model the Domain kept fix availability separate from exposure and retained every image/package association.

Fresh checks include five immutable image readbacks, three successful signed-index probes, all 28 Debian version comparisons, compile/standard-library feature checks, process capabilities and the four wget fixtures. Apt updated all configured Debian/security/PGDG indexes and simulated **zero upgrades**. Alpine reported no upgradable packages. [Signed-policy receipt](evidence/image-security-rootcause/signed-policy.json).

The classifier and existing scanner-contract suite pass **eight tests**. Tests prove duplicate retention, cross-family links, config/index digest handling, tamper rejection, incomplete assessment rejection and failing-policy preservation. A fresh independent review found unresolved evidence references in the initial analysis; referenced receipts were materialized and a failing-before regression now rejects missing local evidence. Empty/null assessments are also rejected. The current full-corpus classification is byte-identical across two executions. A fresh bounded closure review returned PASS for the classification and report, while retaining release NO-GO; it independently replayed the corpus, verified 702 local evidence references and all canonical output hashes. [Verification](evidence/image-security-rootcause/verification.json), [classification replay](evidence/image-security-rootcause/classification-replay.json), [review record](evidence/image-security-rootcause/independent-review.md).

No new images or application scans were generated. The 431 baseline rows use the **10 November Grype database**. The publisher now advertises an 11 November snapshot; its counts have not been tested. Current vendor status is independently dated 12 November. These are deliberately separate claims. [Snapshot boundary](evidence/image-security-rootcause/advisory-snapshot-boundary.json).

Existing build, migration, backend/frontend, recovery and browser receipts remain historical passes, not newly executed tests. No application, authentication, scientific calculation, market-data behavior, dependency lock or scanner policy changed. Current hashes match all 496 protected runtime files, 17 research artifacts, 22 unrelated starting paths and 22 inventoried SQLite files. The original database hash is unchanged. The already-running retained PostgreSQL store also matches its logical snapshot. The stopped Phase 5.1 store was not started merely to repeat that check. [Preservation scope](evidence/image-security-rootcause/preservation.json).

**Stop here rather than rebuild identical packages.** Reopen image remediation when a supported signed fix appears, or when an explicitly qualified alternative can preserve functionality and replay contracts. Corrected upstream advisory metadata may change a later raw scan, but no current finding is waived. Before any GO decision, rerun the unchanged security policy against exact candidate images and a recorded current database. Hosted CI, off-host acceptance, production controls and legitimate historical-data qualification remain separate outstanding gates. No push, merge, deployment, purchase, custom OS fork or model promotion occurred.

## Reproduce the classification

Keep the private raw corpus in place and choose a new output directory:

```powershell
.venv/Scripts/python.exe -B scripts/security/triage_image_findings.py `
  --scan-directory .local/phase53-followup/qualified-scans `
  --images docs/implementation/evidence/phase53-followup/images.json `
  --assessments docs/implementation/evidence/image-security-rootcause/assessments.json `
  --output .local/my-new-image-triage
```

The tool validates raw artifact hashes, immutable image binding, counts and local evidence references before writing. Missing decisions produce `INCOMPLETE` and exit 2; a completed classification never grants a release PASS. Remote URLs are citations reviewed separately, not automatically authenticated by file existence. Do not publish the ignored raw logs, archive, credentials or existing databases.
