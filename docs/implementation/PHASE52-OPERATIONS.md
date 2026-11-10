# Reproduce Phase 5.2 qualification

This is a local rehearsal, not a deployment command. It creates a new Compose project, new PostgreSQL volume, disposable accounts and a seven-day job-local certificate authority. It never installs that CA into the host trust store. Keep every retained database, earlier qualification directory and Docker volume.

## Build an isolated candidate

Freeze the intended commit with `git archive` into a **new** directory under `.local`. Use that directory as the Docker build context. Do not build release candidates from a working directory containing unrelated changes. The repository's `.dockerignore` excludes databases, environments, credentials, model runtime output and local evidence.

Build these five images from the frozen source, retaining the full source commit and each resulting `docker image inspect --format '{{.Id}}'` value:

| Service | Dockerfile | Additional build argument |
| --- | --- | --- |
| API | `backend/Dockerfile` | `CADRISYN_SOURCE_REVISION=<full commit>` |
| Web | `web/Dockerfile` | `CADRISYN_SOURCE_REVISION=<full commit>` |
| PostgreSQL | `deploy/Dockerfile.debian-security` | `BASE_IMAGE=postgres:17.11@sha256:748a18a54d3842d43bc156f0840d78029b8d349e0feca98c12b9c4ce3404a6b3` |
| Redis | `deploy/Dockerfile.alpine-security` | `BASE_IMAGE=redis:8.10.3-alpine3.23@sha256:71885d8cc6e42f2bc0aa2eb853bfc4be200b5108a46ac50e117ae1df0531fb80` |
| Gateway | `deploy/Dockerfile.alpine-security` | `BASE_IMAGE=nginx:1.30.6-alpine3.24@sha256:583b7f2fce1cdb8da5ad5c39ebd3c33b98b87d493190e548bdee1fa8c619c311` |

For example, from the frozen source directory:

```sh
docker build --file backend/Dockerfile --build-arg CADRISYN_SOURCE_REVISION="$revision" --tag kerquant-api:qualification .
```

Set `SOURCE_DATE_EPOCH` to that commit's timestamp when collecting reproducibility evidence. These builds pin the available zlib vendor fixes; they do **not** imply that all other scanner findings are resolved. Debian and Alpine stable-branch availability are separate from generic upstream version comparisons.

## Run the production-profile acceptance harness

Use Python 3.12 with `backend/requirements-workspace.lock.txt`, Docker Compose with `!override` support, OpenSSL and two unused unprivileged ports. Run the harness from the same frozen source revision used for qualification tooling. Supply immutable image IDs, not mutable tags:

```sh
python scripts/ops/qualify_production.py \
  --directory .local/my-new-production-qualification \
  --api-image "$api_image_id" --web-image "$web_image_id" \
  --database-image "$database_image_id" \
  --cache-image "$cache_image_id" --gateway-image "$gateway_image_id" \
  --tls-port 8452 --http-port 8092
```

On Windows, use `.venv/Scripts/python.exe` and, if OpenSSL is not on PATH, `--openssl 'C:/Program Files/Git/usr/bin/openssl.exe'`. Use a new directory and unused ports for every run. The command refuses an existing directory or a directory outside repository `.local`; it has no cleanup, reset or volume-deletion mode.

Windows additionally requires the ACL-protected TLS helper. That hardening is currently a preserved pre-existing local change; a clean Windows checkout without it is refused **before** secret generation. Use a supported POSIX runner or reconcile that helper change through review before claiming clean Windows reproducibility.

The harness uses `deploy/compose.production.yaml` plus the explicit `deploy/compose.production-qualification.yaml` overlay. It creates its own private gateway config so HTTP redirects match the selected HTTPS port. Never substitute a retained project's name or env file.

The older `deploy/compose.qualification.yaml` remains the HTTP preview overlay with ports 8085/15435/16385. Do not use it for production-profile qualification. The final accepted local application is at `https://localhost:8456/app/markets/` and `/app/research/`; its private run directory is `.local/phase52/rehearsal-current`. Browser trust remains limited to the supplied local certificate. This final run uses the separate production overlay directly. The relocation receipt documents the earlier run's unchanged service hashes, rather than changing its original annotation.

The acceptance sequence is:

1. Start the non-debug demo profile with verified PostgreSQL/Redis TLS, file-injected secrets and the constrained runtime role.
2. Use an explicitly marked, disposable development one-shot container to bootstrap two accounts and an **archived synthetic** intake. Verify the existing one- and five-session result hashes. The serving API stays non-debug.
3. Exercise HTTPS authentication, secure cookies, CSRF rejection, private watchlists, unavailable market-provider failure and demo research exclusion.
4. Switch that same disposable stack to non-debug `historical_research`. Exercise private saved research, exports, exact replay and cross-account denial. This profile name grants no historical-data rights and establishes no empirical forecasting validity.
5. Check live readiness rejection of role membership, routine/type ownership and a writable non-public schema. Revert each test privilege in `finally` and confirm recovery.
6. Freeze only this stack's API/web/gateway, run the existing actual PostgreSQL dump/restore utility and strict schema-2 snapshot verifier, and reject source/populated restore targets. Retain the dump and adjacent checksum manifest privately.
7. Restart the disposable application against its restored database and repeat the HTTPS privacy/replay checks. Then test cache/database outages, liveness/readiness separation and recovery.

`receipt.json` contains sanitized results, source/configuration identifiers and image IDs. `credentials.json`, `stack.env`, certificates, keys, database URLs, `commands.log`, backups and raw browser failures are private. Do not commit or upload the entire directory. A failed run retains partial evidence and all volumes; start a fresh run after correcting its cause.

## Browser acceptance

After a successful historical/recovery rehearsal, set these environment variables to that run's absolute paths:

```text
PLAYWRIGHT_BASE_URL=https://localhost:8452
CADRISYN_REHEARSAL_CERT=<new directory>/gateway_cert
CADRISYN_RELEASE_CREDENTIALS=<new directory>/credentials.json
KERQUANT_BROWSER_OUTPUT=<new private directory for screenshots>
```

From `web`, run `npx playwright test --config playwright.qualification.config.ts`. The config pins only the supplied local certificate's public key in Chromium. It does not set global `ignoreHTTPSErrors`. API reads in these tests use that browser transport. Install the repository's Chromium version beforehand; an existing private `PLAYWRIGHT_BROWSERS_PATH` can be reused.

The three tests log in through the actual UI, render the daily chart, inspect demo attribution, verify both themes at desktop/mobile widths, run Axe checks, open an existing five-session synthetic result, and create/reload/replay a new evaluation through the non-debug API. They do not establish production capacity or empirical forecast accuracy. Review the screenshots as well as the exit code. Raw browser errors can contain disposable session cookies; keep them private.

## Advisory and CI evidence

Use a new Grype database cache and perform `grype db update`. Retain the database build/retrieval metadata, scanner versions, image IDs, SPDX inventory and unfiltered JSON findings. Run `scripts/ops/image_evidence.py` against the **same immutable IDs** used for acceptance, with `--fail-on medium` unchanged and no suppressions.

The collector intentionally returns 1 for an all-green scan set because local evidence still needs release review. Inspect `scan_policy`, individual scan/SBOM exit codes, image identities and `ignored_match_count`; never convert an execution error, missing report, ignored finding or different image into a PASS. Record configured ignore rules as well as matched exclusions. The final five reports have zero ignored matches; the four built-in kernel-header rules matched none. A scanner match is not proof of exploitability. Vendor backport analysis belongs beside the raw findings; it must not silently remove them.

The additive `production-qualification.yml` workflow is a local candidate until this source is authorized for publication. Read-only Actions settings and workflow listings do not prove a hosted run. Required checks, trusted ingress, public PKI, an encrypted off-host restore drill, secret rotation, monitoring/alerts, operator ownership and final launch approval remain separate release requirements.

## Recovering an interrupted local Docker session

Inspect `docker info`, container health and PostgreSQL logs before retrying. Docker Desktop being open does not mean its daemon is ready; a running PostgreSQL process can still be syncing its data directory after an interruption. Let recovery finish. Do not disable fsync, delete volumes, prune research data, reset Desktop, relocate WSL or repeatedly restart recovering databases.

If Desktop has exited, a normal hidden application start is a reversible recovery action. Retain the interrupted build log, check the daemon and retained stores, then rerun the build from the same frozen source and record its resulting ID again. Do not assume a partially exported image is qualified. The Phase 5.2 run encountered this host interruption; its root cause must not be relabeled as an application fix without evidence.
