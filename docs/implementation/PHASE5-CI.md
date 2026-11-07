# Phase 5 CI and release profile checks

This page defines the automated checks and the local evidence gate for the
demo and historical research profiles. These tools check receipt consistency. They cannot approve a release,
scientific result, hosted CI run, or production operation.

## Workflow jobs

`.github/workflows/workspace.yml` runs backend, numerical, recovery, frontend,
browser, PostgreSQL, and container checks as separate jobs. A failure in one
job does not skip the others. `.github/workflows/security.yml` runs the runtime
Python audit, workspace Python audit, npm audit, and API/web image scans as
separate jobs. The image scan matrix keeps `fail-fast` disabled so both images
are checked.

Both workflows grant only `contents: read`, disable persisted checkout
credentials, use per-workflow and per-ref concurrency, and bound each job with
a timeout. Action commit pins reuse the versions recorded as verified in the
[Phase 4 scanner pin receipt](evidence/phase4/scanner-pins.json). The workflows
do not deploy. Only allowlisted image metadata, SPDX SBOMs and vulnerability reports are uploaded,
with seven-day retention. Browser screenshots, traces, database files,
environment files, dumps and tokens are excluded.

Hosted checks have not been run from this checkout. The existing Phase 4 image
scan found Medium-or-higher matches, and the project has no qualified
historical archive. These remain release blockers; workflow configuration
alone does not change either result.

## Evidence manifest

Run the local release gate from the repository root:

```powershell
& .\.venv\Scripts\python.exe scripts\ops\release_gate.py `
  --profile demo `
  --evidence .local\release\demo-manifest.json `
  --output .local\release\demo-report.json
```

Use `--profile historical_research` only after the dataset and evaluation pass
the existing rights, input, and scientific review. The manifest schema version
is `1`. Its top-level fields are `schema_version`, `profile`, `source_commit`,
`checks`, and `research`. The CLI profile must match the manifest profile.

`checks` contains exactly these named records:

| Group | Required check names |
| --- | --- |
| Local engineering | `backend_tests`, `frontend_tests`, `numerical_tests`, `browser_tests`, `postgresql_tests`, `auth_isolation`, `recovery_restore` |
| Security and containers | `container_migrations`, `dependency_scan`, `image_scan`, `sbom` |
| Demo qualification | `operational_health`, `accessibility`, `performance`, `production_preflight`, `hosted_ci` |
| Scientific qualification | `dataset_rights`, `dataset_provenance`, `point_in_time_qualification`, `scientific_evaluation` |
| Production readiness | `trusted_tls`, `secret_provisioning`, `offhost_restore`, `operator_qualification` |

Each check record has `status`, `exit_code`, `source_commit`, and `artifacts`.
Use only `PASS`, `FAIL`, or `NOT_RUN` for `status`. A `PASS` needs exit code `0`
and at least one existing, hash-verified artifact. A `FAIL` needs a non-zero
exit code and a hash-verified result file. A `NOT_RUN` check needs a null exit
code and an empty artifact list. Every check must use the manifest's exact
`source_commit`.

Each artifact has only `path` and `sha256`. The path is relative to the
manifest's directory. The gate rejects absolute paths, traversal, symbolic
links, missing files, directories, digest mismatches, unknown checks, missing
checks, unknown fields, duplicate JSON keys, and unsupported schema versions.
The gate streams artifact bytes through SHA-256. It never runs a command from
the manifest.

The CLI writes a new report without replacing an existing file. It returns
`1` for every valid manifest, including one whose declared checks all pass,
and `2` when the manifest is invalid or an output cannot be created. Aggregate
PASS declarations become `REVIEW_REQUIRED`. There is no approval exit code. A valid source-drift report is written with failed
verdicts and exit code `1`.

## Source binding

`source_commit` must be a full 40-character Git commit ID and an ancestor of
the current `HEAD`. That commit must track the `.github`, `backend`, `deploy`,
`scripts`, `tests`, and `web` source areas. The gate rejects tracked or
untracked source changes in those areas between the tested commit and `HEAD`,
and rejects relevant dirty or untracked source in the current working tree.
Changes under documentation and evidence paths may follow the tested commit.
Local database files and `.local` runtime files are excluded from this source
check.

The release report records the tested commit, current `HEAD`, evidence
manifest digest, source-binding result, and six verdicts: local engineering,
security and containers, hosted CI, demo qualification, scientific
qualification, and actual production readiness. Any source-binding failure
prevents every verdict from passing. Even with valid source binding and declared
PASS checks, this tool reports `REVIEW_REQUIRED`, never approval.

## Profile requirements

For `demo`, set `research.kind` to `none` or `synthetic_fixture`. Set
`contains_synthetic` to match that value, and set `dataset` and `evaluation` to
null. All four scientific check records must be `NOT_RUN`. A demo can satisfy the declared receipt requirements while its scientific
status remains `NOT_QUALIFIED`; satisfactory receipts still require independent review.

The demo verdict requires all local engineering and security/container checks,
plus `operational_health`, `accessibility`, `performance`,
`production_preflight`, and `hosted_ci`. This proves the named demo checks
only. It does not claim real market data, empirical forecasting skill, or
production readiness.

For `historical_research`, set `research.kind` to
`qualified_historical` and `contains_synthetic` to false. The dataset object
must include a non-empty ID and provider, a UTC `acquired_at`, an
`internal_research` permitted-use entry, unadjusted closes, complete split and
dividend records, the `XNYS` calendar, an increasing coverage interval, 120 to
1,500 sessions, and a raw artifact reference. The `dataset_provenance` check
must include the raw artifact with the same digest.

The evaluation object must name that dataset ID, use
`chronological_walk_forward`, fit preprocessing on `train_only` rows, align
targets to `forward_h_session_close`, report horizons `[1, 5]`, include the
`naive_persistence`, `last_close`, and `expanding_log_mean` benchmarks, declare
no synthetic mixing, and use the existing 60-minute availability cutoff. The
`scientific_evaluation` check must include the evaluation artifact with the
same digest. All four scientific checks must pass.

Actual production readiness also needs passing `trusted_tls`,
`secret_provisioning`, `offhost_restore`, and `operator_qualification` checks.
The current CLI has no `production` profile. It reports production readiness
separately and does not mark that verdict as passing from local demo checks
alone.

The gate checks receipt structure, file identity, hashes, status, exit codes,
and source binding. It does not authenticate a provider, license statement,
operator, hosted run, test process, production TLS endpoint, or restore
operator. The manifest and its SHA-256 values are not signed attestations.
Scientific reviewers still need to inspect source terms, raw acquisition
evidence, availability history, adjustment methodology, evaluation rows,
target alignment, and leakage controls. Keep licensed source bytes and
credentials private; do not commit them or add them to CI artifacts.

## Local validation

Run the focused gate and workflow tests with the workspace Python environment:

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests -p test_release_gate.py
```

These tests use synthetic receipt files to check gate behavior. They do not
qualify a historical dataset or constitute release evidence.


## Production rehearsal and current evidence

The container job now starts a second, isolated non-debug demo stack with local
TLS, private PostgreSQL/Redis networks, restricted database roles and file-mounted
secrets. Its CA exists only inside the disposable job; it does not install trust
or qualify externally trusted certificates. The exact runtime configuration is
checked inside the API container:

```powershell
docker compose --project-name cadrisyn-phase5-prod --env-file .local/phase5/tls-qualification/rehearsal.env -f deploy/compose.production.yaml exec -T api python /app/scripts/ops/preflight.py --environment
```

`rehearsal.env` deliberately contains container secret paths. Do not pass it to a
host-side file preflight. Use `--environment` inside the configured container,
or provide a separately authored host-readable environment file. Online HTTPS
probes must also validate the correct CA and actual release policy.

The numerical job runs the supported `research.tests.test_quant` suite using the
workspace lock. The preserved Torch/legacy regression suite is a separate local
check in `backend/venv`; the lightweight hosted numerical job does not cover that
environment or promote its models.

The SBOM action pin `e22c389904149dbc22b58101806040fa8d37a610` and artifact action
pin `ea165f8d65b6e75b540449e92b4886f43607fa02` were resolved from the official
repositories and their input manifests inspected on 2026-11-07. Builds pass the
source revision and commit timestamp, request maximum BuildKit provenance, and
retain build metadata. None of these local changes proves hosted execution or a
signed attestation. See the [official SBOM action](https://github.com/anchore/sbom-action)
and [Docker attestation documentation](https://docs.docker.com/build/metadata/attestations/).

`scripts/ops/image_evidence.py` inventories immutable local image IDs and scans
sequentially against a pre-initialized advisory database with auto-update disabled.
Initialize/update that database once, before scans. The collector distinguishes
scanner execution from findings, retains all severities without suppressions,
and labels source binding `UNVERIFIED`. Its checkout identity is the collector's
checkout, not proof of image build origin. A clean advisory policy remains
`REVIEW_REQUIRED` overall and exits 1; callers must not interpret it as release
approval. SPDX hashes and recorded image IDs support human review.
