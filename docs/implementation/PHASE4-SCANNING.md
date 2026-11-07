# Phase 4 scanning

The security workflow runs the Python and npm dependency audits separately from the application image scan. It runs on each push and pull request with `contents: read` permission.

The workflow builds the API and web images from `backend/Dockerfile` and `web/Dockerfile`. It scans the resulting local images before any registry push. No image or scan report is uploaded. The root `.dockerignore` excludes `.local`, `.env*`, SQLite files, and local evidence from the build context.

Hosted CI has not run from this workspace. The workflow configuration does not establish a hosted scan result.

## Audited dependencies

The workflow installs `pip-audit==2.10.1` in a temporary virtual environment. It audits `backend/requirements-runtime.txt` and `backend/requirements-workspace.lock.txt` in separate commands. The runtime requirements include the workspace lock plus the API image additions.

The web job runs `npm audit --omit=dev` against `web/package-lock.json`. It checks production dependencies and does not run `npm audit fix` or change the lockfile. npm sends package names and versions to its configured registry to retrieve advisories.

Each audit exits non-zero when it finds a vulnerability or cannot complete. The workflow does not ignore audit failures.

## Image scan

The image matrix scans the final API and web images independently with fail-fast disabled, so an API finding does not skip the web scan. It pins `anchore/scan-action` to signed commit `27805bf3b4e84b4a5c980df22ed233c00390a439` from release `v7.4.2` and sets Grype to `v0.121.2`.

The Grype release is immutable and publishes a checksum file and Sigstore bundle. The local Windows binary matches the official GitHub release asset's SHA-256 digest. Its Sigstore bundle was not independently verified locally. The pinned scan action's Linux installer fetches the installer from the Grype release tag and checks the downloaded binary against that release's SHA-256 checksum. It does not ask Cosign to verify the Sigstore bundle.

The scan fails on Medium, High, or Critical findings. Lower severities remain in the table output. Build, database, or scanner errors also fail the job. The workflow has no ignore rules, `only-fixed` filter, `continue-on-error`, or SARIF upload.

This scan covers the final API and web images only. It does not scan discarded Docker build stages or the PostgreSQL, Redis, and nginx images in `compose.yaml`.

## Executed local results

The explicit workspace-lock audit covers 64 pinned Python dependencies; the separate runtime-addition audit covers gunicorn and packaging. Both report no known vulnerabilities. The production npm audit also reports zero advisories. The local pip-audit commands used `--disable-pip --no-deps` against each file separately; the runtime-only output must not be mistaken for an audit of the included workspace lock.

The API image initially reported six pip findings. Pinning its installer to pip 26.3 removes all six without changing the workspace lock or Python version. Requesting current vendor OpenSSL packages still installs `3.5.7-1~deb13u3` from the configured repository. The resulting API scan retains 283 matches: 2 Critical, 96 High, 90 Medium, 18 Low, and 77 Negligible. Many are OS-package or CPE matches with unknown/not-fixed/wont-fix status. They require source-specific triage, not a blanket exception.

The initial web image reported 26 matches. Twenty-three were in the base image's global npm installation, which the standalone Node server does not use. The final runner removes that installation after the build stages. Three Medium matches remain for `CVE-2025-60876` in BusyBox, busybox-binsh, and ssl_client, with no fixed version listed by the scanner. These are three package matches for one CVE.

Grype's NVD CPE records classify `CVE-2026-63073` and `CVE-2026-75803` in OpenSSL as Critical. [OpenSSL's own advisory index](https://openssl-library.org/news/vulnerabilities/) lists both as Low. Neither difference proves that this Debian revision is patched or exploitable in this application. Vendor backport and reachability evidence remain required. The configured Medium threshold still fails; no findings are suppressed. Application tests, replay results, and package audits do not override that image gate.

The local scanner used Grype 0.121.2 and a valid schema-6 database built on 2026-11-06. The [evidence index](evidence/phase4/README.md) retains package/CVE/fix-state summaries and the verified scanner asset digest. This is a local result, not a hosted CI run or certification.

## Run locally

From the repository root in PowerShell, run the dependency audits with an isolated Python tool environment:

```powershell
$scannerEnv = Join-Path $env:TEMP 'cadrisyn-security-tools'
py -3.12 -m venv $scannerEnv
$scannerPython = Join-Path $scannerEnv 'Scripts\python.exe'
& $scannerPython -m pip install --disable-pip-version-check 'pip-audit==2.10.1'
& $scannerPython -m pip_audit -r backend/requirements-runtime.txt
& $scannerPython -m pip_audit -r backend/requirements-workspace.lock.txt
npm --prefix web audit --omit=dev
```

Build and scan both application images from the repository root. Install Grype `v0.121.2` from the [official release](https://github.com/anchore/grype/releases/tag/v0.121.2) first.

```powershell
docker build --pull --file backend/Dockerfile --tag cadrisyn-api:security .
docker build --pull --file web/Dockerfile --tag cadrisyn-web:security .
grype --version
grype cadrisyn-api:security --fail-on medium
grype cadrisyn-web:security --fail-on medium
```

Grype downloads its vulnerability database from Anchore. npm and pip-audit also query public advisory services. These commands do not upload the local environment or database.

## Sources

- [GitHub Actions security hardening](https://docs.github.com/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions), including full-length commit SHA pins.
- [actions/checkout v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1), [actions/setup-python v7.1.0](https://github.com/actions/setup-python/releases/tag/v7.1.0), and [actions/setup-node v7.1.0](https://github.com/actions/setup-node/releases/tag/v7.1.0).
- [pip-audit v2.10.1 on PyPI](https://pypi.org/project/pip-audit/2.10.1/) and the [PyPA release](https://github.com/pypa/pip-audit/releases/tag/v2.10.1).
- [pip 26.3 release](https://github.com/pypa/pip/releases/tag/26.3) and [Node's official release index](https://nodejs.org/dist/index.json), used to verify the pinned installer and CI Node version.
- [npm audit documentation](https://docs.npmjs.com/cli/v11/commands/npm-audit/).
- [Anchore scan-action v7.4.2](https://github.com/anchore/scan-action/releases/tag/v7.4.2) and [Grype v0.121.2](https://github.com/anchore/grype/releases/tag/v0.121.2).
- [Trivy supply-chain advisory GHSA-69fq-xp46-6x23](https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23) and [Aqua's investigation update](https://www.aquasec.com/blog/trivy-supply-chain-attack-what-you-need-to-know/). This workflow does not use Trivy.
