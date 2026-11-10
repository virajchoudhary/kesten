# Reproduce Phase 5.3 and prepare off-host acceptance

This procedure uses new local containers and a clean source archive. It does not authorize a remote write, deployment, data transfer, service purchase or change to an existing database. Keep keys, account credentials, URLs, dumps and raw failure logs in ignored private directories.

## Build and qualify the committed source

The latest Phase 5.3 follow-up application candidate is `4862522e6a856882cc4916847ed6453307903e9d`. The earlier acceptance is retained in [the original report](PHASE53-READINESS.md). Use the validated canonical exporter for a new private source bundle:

```powershell
$revision = git rev-parse HEAD
.venv/Scripts/python.exe scripts/ops/freeze_source.py `
  --revision $revision --directory .local/my-new-source
```

Use a full committed hash. Keep the outer checkout at that hash while the harness records its tooling revision. The exporter refuses an existing destination, unsafe archive paths, unsupported symlinks, case collisions and altered archive bytes. It validates each extracted file against the Git blob, normalizes Git export line endings and records the archive and per-file hashes. The new directory is private. Do not upload its source archive or extracted tree; existing tracked history can contain data that is excluded from Docker by `.dockerignore`. CI uploads only the sanitized source receipt.

Use `.local/my-new-source/tree` as the context and the Dockerfiles inside that tree. Build the five pinned bases documented in [Phase 5.2 operations](PHASE52-OPERATIONS.md). Set `SOURCE_DATE_EPOCH` to the source receipt's `commit_epoch` and API/web `CADRISYN_SOURCE_REVISION` to its `commit`. Include `--output type=image,push=false,rewrite-timestamp=true` on every build. Keep default BuildKit provenance enabled. An attestation envelope can differ even when runtime content matches.

The Alpine recipes use APK's `--no-logfile` only during image construction. This avoids wall-clock transaction entries in a build layer. Compiler installation, pip installation and compiler removal share one API build layer. This prevents a temporary virtual-package version and the removed compiler toolchain from persisting in a lower image layer. Package inventory, `/etc/apk/world`, runtime application logging and build stdout remain available. Do not remove scanner metadata or change policy to obtain a reproducibility result. Live package indexes remain external inputs; retain the signed index versions, SBOM and exact image IDs. The follow-up report distinguishes an actual uncached API rebuild from untested cold builds of the other images.

The PostgreSQL recipe now downloads gosu 1.20 in a build-only Python stage. The architecture mapping preserves the upstream release names for x86, ARM and PowerPC. The final stage imports the public release key, checks primary fingerprint `B42F6819007F00F88E364FD4036A9C25BF357DD4`, verifies the detached binary signature and exercises `gosu nobody true` before accepting the layer. It does not add a Python interpreter to PostgreSQL or change PostgreSQL's version, roles, data-directory layout or collation provider. A failed download, signature or privilege switch fails the build.

Record the five immutable image IDs. Run the production harness **from the archived source**, using a new directory beneath that archive's `.local`. This also tests the committed TLS helper and Compose files rather than their pre-existing local variants:

```powershell
.venv/Scripts/python.exe .local/my-new-source/tree/scripts/ops/qualify_production.py `
  --directory .local/my-new-source/tree/.local/my-new-qualification `
  --api-image <immutable API ID> --web-image <immutable web ID> `
  --database-image <immutable PostgreSQL ID> `
  --cache-image <immutable Redis ID> --gateway-image <immutable gateway ID> `
  --tls-port 8461 --http-port 8101 `
  --openssl 'C:/Program Files/Git/usr/bin/openssl.exe'
```

Choose unused ports. The harness refuses existing directories and Compose resources and has no volume deletion mode. Its private accounts and archived synthetic intake are qualification fixtures. `historical_research` does not grant data rights or establish empirical validity.

Re-run the production Chromium config against that exact gateway, certificate and credentials, following the three-test procedure in Phase 5.2 operations. Capture the resulting receipt, tooling/configuration hashes and exact running image IDs. For a repeat build, keep the archive, epoch, architecture, toolchain and package inputs fixed. Cache reuse and matching image IDs do not prove an independent cold build. The live apt/apk indexes and build output must be accounted for before claiming byte-identical reproduction.

## Collect honest security evidence

Scan those same five IDs using `scripts/ops/image_evidence.py`, a validated advisory database and the existing medium threshold. Retain SPDX and raw JSON reports privately. Require zero ignored matches and no project waivers; a vendor backport explanation does not erase a scanner finding.

Check the current [Anchore database pointer](https://grype.anchore.io/databases/v6/latest.json). An existing verified database may be reused when its source archive checksum matches the current publisher pointer and its actual file hash remains valid. Record that reuse explicitly. Never use a partially extracted cache or describe an old database as newly built. The first Phase 5.3 download timed out and remains excluded. The follow-up downloaded and validated the 10 November database into a new private directory on D:, without moving an existing cache. Record the actual database hash and publisher archive checksum for every accepted scan cohort. A new advisory snapshot may add findings without any application change.

The collector intentionally returns 1 even for `REVIEW_REQUIRED`. Read the policy, execution results and identities. Neither that exit convention nor successful application tests grants a scan exemption.

## Prepare hosted CI without publishing

The additive `production-qualification.yml` has separate Windows ACL and Ubuntu production-stack jobs. The Windows job uses only standard-library tests and new temporary directories. The Ubuntu job validates a canonical committed source bundle, builds five images with normalized layer timestamps, passes their exact IDs into recovery/browser acceptance and scans those same IDs. Actions remain pinned to full commits, checkout does not persist credentials, and artifact upload has an explicit sanitized allowlist.

Before an authorized hosted run, review the precise branch commit, workflow diff, runner access and repository required-check settings. After publication is separately approved, require both jobs and retain source-bound run URLs and receipts. A local YAML parser, actionlint result or Windows test is not a hosted CI result. This phase does not push, dispatch or alter repository settings.

## Execute off-host acceptance only after a target is approved

1. Record the approved second host, operator, access boundary, image architecture, storage ownership, retention period and encryption recipient fingerprint. Confirm there is no route to the source database from the restore target. No external target is provisioned or contacted by this phase.
2. Use the existing recovery utility to produce a new custom-format PostgreSQL dump and adjacent manifest. Supply the source connection through a named environment variable with verified TLS, never a command-line URL. Freeze writes if exact comparison to a separately acquired application snapshot is required. PostgreSQL dumps are internally consistent, but a later independent snapshot is not automatically the same transaction.
3. Encrypt the dump and manifest to the approved backup recipient. Authenticate their origin using an approved signing key or authenticated transfer channel. A checksum detects corruption and does not authenticate the manifest. Keep recovery keys and credentials separate from backup storage. The local disposable AES256 roundtrip is a test of encryption/integrity only, not production key custody.
4. Transfer only that approved encrypted bundle over the approved authenticated channel. Record ciphertext hashes before and after transfer. Do not copy a local rehearsal CA private key or upload raw browser/session logs. Historical-data terms may restrict even private transfer; confirm rights before transferring a future genuine archive.
5. On the second host, verify the authenticated bundle before decrypting into a new private directory. Reject any failed integrity result even if a decryptor left partial plaintext. Verify plaintext size/hash against the authenticated manifest before invoking restoration.
6. Create an isolated empty PostgreSQL 17 target using the reviewed role and TLS configuration. Do not attach, replace, rename or clean any source volume. Execute `recovery.py restore-postgres --manifest <verified manifest> --target-database-url-env KERQUANT_RESTORE_URL`. The utility rejects source identities and populated targets; it does not create or delete databases. The named environment variable must contain the separately approved target URL.
7. Compare the strict application snapshot, table hashes, migrations, archived intake bytes/terms/availability, run identities, dependency lock and deterministic replays. Intake attachments are stored in database binary fields. The 17 preserved legacy research artifacts and other filesystem assets need their own approved encrypted inventory/backup procedure; a successful application database restore does not cover them.
8. Start only the isolated restored application. Prove its HTTP connection with a restore-only disposable marker, remove that marker through the owning account, and run cross-account denial, CSRF, secure-cookie, provenance, saved-result and replay browser checks. Repeat dependency outage/recovery checks. Use exact source/image IDs and keep fixture research separate from empirical results.
9. Measure recovery timing and record the observed data-loss window against operator-approved RTO/RPO targets. No timing target or production capacity is invented here. Confirm alert delivery and a named operator can repeat the drill without access to the original machine.
10. Retain a sanitized acceptance receipt with source/target fingerprints, artifact/image hashes, results and reviewer identity. Mark off-host acceptance VERIFIED only after the real second-host drill succeeds. Leave it UNTESTED otherwise. Keep launch NO-GO while image policy, hosted CI, trusted ingress, operational ownership or other release gates lack acceptance.

The PostgreSQL dump/restore semantics follow the [PostgreSQL 17 backup documentation](https://www.postgresql.org/docs/17/backup-dump.html). Timestamp handling follows [Docker's reproducible-build guidance](https://docs.docker.com/build/ci/github-actions/reproducible-builds/). These references describe mechanisms; they do not certify this installation.
