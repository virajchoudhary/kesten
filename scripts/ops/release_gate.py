"""Validate local release evidence without running commands from that evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = 1
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
GIT_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")

CHECK_IDS = (
    "backend_tests",
    "frontend_tests",
    "numerical_tests",
    "browser_tests",
    "postgresql_tests",
    "auth_isolation",
    "recovery_restore",
    "container_migrations",
    "dependency_scan",
    "image_scan",
    "sbom",
    "operational_health",
    "accessibility",
    "performance",
    "production_preflight",
    "hosted_ci",
    "dataset_rights",
    "dataset_provenance",
    "point_in_time_qualification",
    "scientific_evaluation",
    "trusted_tls",
    "secret_provisioning",
    "offhost_restore",
    "operator_qualification",
)

ENGINEERING_CHECKS = (
    "backend_tests",
    "frontend_tests",
    "numerical_tests",
    "browser_tests",
    "postgresql_tests",
    "auth_isolation",
    "recovery_restore",
)
SECURITY_CONTAINER_CHECKS = (
    "container_migrations",
    "dependency_scan",
    "image_scan",
    "sbom",
)
SCIENCE_CHECKS = (
    "dataset_rights",
    "dataset_provenance",
    "point_in_time_qualification",
    "scientific_evaluation",
)
PRODUCTION_CHECKS = (
    "trusted_tls",
    "secret_provisioning",
    "offhost_restore",
    "operator_qualification",
)
DEMO_CHECKS = (
    *ENGINEERING_CHECKS,
    *SECURITY_CONTAINER_CHECKS,
    "operational_health",
    "accessibility",
    "performance",
    "production_preflight",
    "hosted_ci",
)

SOURCE_PREFIXES = (
    ".github/",
    "backend/",
    "config/",
    "deploy/",
    "frontend/",
    "quant_testing/",
    "scripts/",
    "tests/",
    "web/",
)
REQUIRED_TRACKED_PREFIXES = (
    ".github/",
    "backend/",
    "deploy/",
    "scripts/",
    "tests/",
    "web/",
)
ROOT_SOURCE_FILES = {
    ".dockerignore",
    ".env.example",
    "compose.yaml",
    "docker-compose.yml",
    "Dockerfile",
    "Makefile",
    "package-lock.json",
    "package.json",
    "pyproject.toml",
    "pytest.ini",
    "requirements.txt",
    "setup.cfg",
    "tox.ini",
}


class GateError(ValueError):
    """Raised when a receipt is malformed or its local artifacts do not match."""


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GateError(f"{label} must be a JSON object.")
    return value


def _require_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        missing = sorted(expected - set(value))
        unknown = sorted(set(value) - expected)
        details = []
        if missing:
            details.append(f"missing {', '.join(missing)}")
        if unknown:
            details.append(f"unknown {', '.join(unknown)}")
        raise GateError(f"{label} has {'; '.join(details)}.")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise GateError("Evidence contains a duplicate JSON key.")
        result[key] = value
    return result


def _load_manifest(path: Path) -> tuple[dict[str, Any], Path, str]:
    try:
        if path.is_symlink():
            raise GateError("Evidence manifest must not be a symbolic link.")
        resolved = path.resolve(strict=True)
        if not resolved.is_file() or resolved.stat().st_size > 2_000_000:
            raise GateError("Evidence manifest is missing, not a file, or too large.")
        raw = resolved.read_bytes()
    except GateError:
        raise
    except OSError as error:
        raise GateError("Evidence manifest cannot be read.") from error

    try:
        manifest = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GateError("Evidence manifest is not valid UTF-8 JSON.") from error
    return _require_object(manifest, "Evidence manifest"), resolved.parent, hashlib.sha256(raw).hexdigest()


def _validate_artifact_reference(value: Any, label: str) -> tuple[str, str]:
    artifact = _require_object(value, label)
    _require_keys(artifact, {"path", "sha256"}, label)
    path = artifact["path"]
    digest = artifact["sha256"]
    if not isinstance(path, str) or not path or "\\" in path:
        raise GateError(f"{label}.path must be a non-empty relative POSIX path.")
    relative = PurePosixPath(path)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise GateError(f"{label}.path must stay inside the evidence directory.")
    if not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest):
        raise GateError(f"{label}.sha256 must be a lowercase SHA-256 digest.")
    return path, digest


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_artifact(
    value: Any,
    evidence_root: Path,
    cache: dict[str, tuple[str, str]],
    label: str,
) -> tuple[str, str]:
    relative_path, expected_digest = _validate_artifact_reference(value, label)
    cached = cache.get(relative_path)
    if cached is not None:
        if cached[1] != expected_digest:
            raise GateError(f"{label} repeats an artifact path with a different digest.")
        return cached

    candidate = evidence_root.joinpath(*PurePosixPath(relative_path).parts)
    try:
        current = evidence_root
        for part in PurePosixPath(relative_path).parts:
            current = current / part
            if current.is_symlink():
                raise GateError(f"{label} must not use symbolic links.")
        resolved = candidate.resolve(strict=True)
        if evidence_root != resolved and evidence_root not in resolved.parents:
            raise GateError(f"{label} resolves outside the evidence directory.")
        if not resolved.is_file():
            raise GateError(f"{label} is not a regular file.")
        actual_digest = _hash_file(resolved)
    except GateError:
        raise
    except OSError as error:
        raise GateError(f"{label} artifact is missing or cannot be read.") from error

    if actual_digest != expected_digest:
        raise GateError(f"{label} artifact SHA-256 does not match.")
    result = (relative_path, actual_digest)
    cache[relative_path] = result
    return result


def _validate_checks(
    value: Any,
    source_commit: str,
    evidence_root: Path,
    artifact_cache: dict[str, tuple[str, str]],
) -> dict[str, dict[str, Any]]:
    checks = _require_object(value, "checks")
    if set(checks) != set(CHECK_IDS):
        missing = sorted(set(CHECK_IDS) - set(checks))
        unknown = sorted(set(checks) - set(CHECK_IDS))
        details = []
        if missing:
            details.append(f"missing {', '.join(missing)}")
        if unknown:
            details.append(f"unknown {', '.join(unknown)}")
        raise GateError(f"checks has {'; '.join(details)}.")

    validated: dict[str, dict[str, Any]] = {}
    for check_id in CHECK_IDS:
        check = _require_object(checks[check_id], f"checks.{check_id}")
        _require_keys(
            check,
            {"status", "exit_code", "source_commit", "artifacts"},
            f"checks.{check_id}",
        )
        status = check["status"]
        exit_code = check["exit_code"]
        check_source = check["source_commit"]
        artifacts = check["artifacts"]
        if not isinstance(status, str) or status not in {"PASS", "FAIL", "NOT_RUN"}:
            raise GateError(f"checks.{check_id}.status is not supported.")
        if check_source != source_commit:
            raise GateError(f"checks.{check_id}.source_commit does not match the manifest.")
        if not isinstance(artifacts, list):
            raise GateError(f"checks.{check_id}.artifacts must be a list.")

        verified_artifacts = [
            _verify_artifact(
                artifact,
                evidence_root,
                artifact_cache,
                f"checks.{check_id}.artifacts[{index}]",
            )
            for index, artifact in enumerate(artifacts)
        ]
        if status == "PASS":
            if type(exit_code) is not int or exit_code != 0 or not verified_artifacts:
                raise GateError(
                    f"checks.{check_id} PASS requires exit_code 0 and at least one verified artifact."
                )
        elif status == "FAIL":
            if type(exit_code) is not int or exit_code == 0 or not verified_artifacts:
                raise GateError(
                    f"checks.{check_id} FAIL requires a non-zero exit_code and verified failure evidence."
                )
        elif exit_code is not None or verified_artifacts:
            raise GateError(
                f"checks.{check_id} NOT_RUN requires a null exit_code and no artifacts."
            )
        validated[check_id] = {
            "status": status,
            "exit_code": exit_code,
            "source_commit": check_source,
            "artifacts": verified_artifacts,
        }
    return validated


def _parse_date(value: Any, label: str) -> date:
    if not isinstance(value, str):
        raise GateError(f"{label} must be an ISO date.")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise GateError(f"{label} must be an ISO date.") from error


def _validate_research(
    value: Any,
    profile: str,
    checks: dict[str, dict[str, Any]],
    evidence_root: Path,
    artifact_cache: dict[str, tuple[str, str]],
) -> dict[str, Any]:
    research = _require_object(value, "research")
    _require_keys(
        research,
        {"kind", "contains_synthetic", "dataset", "evaluation"},
        "research",
    )
    kind = research["kind"]
    contains_synthetic = research["contains_synthetic"]
    dataset = research["dataset"]
    evaluation = research["evaluation"]

    if profile == "demo":
        if not isinstance(kind, str):
            raise GateError("research.kind must be a supported string.")
        if kind not in {"none", "synthetic_fixture"}:
            raise GateError("A demo profile cannot claim qualified historical research.")
        if contains_synthetic is not (kind == "synthetic_fixture"):
            raise GateError("Demo research kind and contains_synthetic disagree.")
        if dataset is not None or evaluation is not None:
            raise GateError("A demo profile cannot attach a historical dataset or evaluation.")
        if any(checks[check_id]["status"] != "NOT_RUN" for check_id in SCIENCE_CHECKS):
            raise GateError("A demo profile must leave empirical qualification NOT_RUN.")
        return research

    if kind != "qualified_historical" or contains_synthetic is not False:
        raise GateError("Historical research requires qualified_historical data without synthetic rows.")

    dataset = _require_object(dataset, "research.dataset")
    _require_keys(
        dataset,
        {
            "id",
            "provider",
            "raw_artifact",
            "acquired_at",
            "permitted_uses",
            "price_basis",
            "corporate_actions",
            "calendar",
            "coverage_start",
            "coverage_end",
            "session_count",
        },
        "research.dataset",
    )
    for key in ("id", "provider"):
        if not isinstance(dataset[key], str) or not dataset[key].strip():
            raise GateError(f"research.dataset.{key} must be a non-empty string.")
    try:
        acquired_at = datetime.fromisoformat(dataset["acquired_at"].replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as error:
        raise GateError("research.dataset.acquired_at must be an ISO timestamp.") from error
    if acquired_at.tzinfo is None or acquired_at.utcoffset() != timedelta(0):
        raise GateError("research.dataset.acquired_at must include a UTC offset.")
    permitted_uses = dataset["permitted_uses"]
    if (
        not isinstance(permitted_uses, list)
        or not permitted_uses
        or any(not isinstance(use, str) or not use.strip() for use in permitted_uses)
        or "internal_research" not in permitted_uses
    ):
        raise GateError("Historical dataset rights must permit internal_research.")
    if dataset["price_basis"] != "unadjusted_close":
        raise GateError("Historical research requires unadjusted closing prices.")
    if dataset["corporate_actions"] != "complete_splits_and_dividends":
        raise GateError("Historical research requires complete split and dividend records.")
    if dataset["calendar"] != "XNYS":
        raise GateError("Historical research requires the qualified XNYS calendar.")
    coverage_start = _parse_date(dataset["coverage_start"], "research.dataset.coverage_start")
    coverage_end = _parse_date(dataset["coverage_end"], "research.dataset.coverage_end")
    if coverage_start >= coverage_end:
        raise GateError("Historical dataset coverage must have a positive date range.")
    session_count = dataset["session_count"]
    if type(session_count) is not int or not 120 <= session_count <= 1500:
        raise GateError("Historical dataset session_count must be between 120 and 1500.")

    raw_artifact = _validate_artifact_reference(dataset["raw_artifact"], "research.dataset.raw_artifact")
    if raw_artifact not in checks["dataset_provenance"]["artifacts"]:
        raise GateError("dataset_provenance must hash-check the raw dataset artifact.")

    evaluation = _require_object(evaluation, "research.evaluation")
    _require_keys(
        evaluation,
        {
            "dataset_id",
            "method",
            "preprocessing_fit_scope",
            "target_alignment",
            "horizons",
            "benchmarks",
            "synthetic_mixed",
            "availability_cutoff_minutes",
            "artifact",
        },
        "research.evaluation",
    )
    if evaluation["dataset_id"] != dataset["id"]:
        raise GateError("Research evaluation dataset_id does not match the dataset.")
    if evaluation["method"] != "chronological_walk_forward":
        raise GateError("Historical research requires chronological walk-forward evaluation.")
    if evaluation["preprocessing_fit_scope"] != "train_only":
        raise GateError("Research preprocessing must fit on training rows only.")
    if evaluation["target_alignment"] != "forward_h_session_close":
        raise GateError("Research targets must align to the forward session close.")
    horizons = evaluation["horizons"]
    if (
        not isinstance(horizons, list)
        or len(horizons) != 2
        or any(type(horizon) is not int for horizon in horizons)
        or horizons != [1, 5]
    ):
        raise GateError("Historical research must report both one- and five-session horizons.")
    required_benchmarks = {"naive_persistence", "last_close", "expanding_log_mean"}
    benchmarks = evaluation["benchmarks"]
    if (
        not isinstance(benchmarks, list)
        or any(not isinstance(benchmark, str) for benchmark in benchmarks)
        or not required_benchmarks.issubset(benchmarks)
    ):
        raise GateError("Historical evaluation must include all accepted simple baselines.")
    if evaluation["synthetic_mixed"] is not False:
        raise GateError("Historical evaluation must not mix synthetic observations.")
    if evaluation["availability_cutoff_minutes"] != 60:
        raise GateError("Historical input availability must meet the 60-minute cutoff.")
    evaluation_artifact = _validate_artifact_reference(
        evaluation["artifact"],
        "research.evaluation.artifact",
    )
    if evaluation_artifact not in checks["scientific_evaluation"]["artifacts"]:
        raise GateError("scientific_evaluation must hash-check its evaluation report.")
    return research


def _git_bytes(root: Path, *arguments: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=root,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise GateError("Git source state could not be inspected.") from error
    if result.returncode != 0:
        raise GateError("Git source state could not be inspected.")
    return result.stdout


def _git_paths(root: Path, *arguments: str) -> list[str]:
    output = _git_bytes(root, *arguments)
    try:
        return [item.decode("utf-8") for item in output.split(b"\0") if item]
    except UnicodeDecodeError as error:
        raise GateError("Git reported a source path that is not valid UTF-8.") from error


def _is_source_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if normalized == "backend/db.sqlite3" or normalized.startswith(".local/"):
        return False
    if normalized.lower().endswith((".db", ".sqlite", ".sqlite3", ".sqlite-shm", ".sqlite-wal")):
        return False
    return (
        normalized in ROOT_SOURCE_FILES
        or any(normalized.startswith(prefix) for prefix in SOURCE_PREFIXES)
        or normalized.startswith(".github/")
        or normalized.startswith("config/")
        or normalized.startswith(".")
        and normalized in {".gitignore", ".gitattributes", ".dockerignore"}
    )


def _source_binding(repo_root: Path, source_commit: str) -> dict[str, Any]:
    try:
        root = repo_root.resolve(strict=True)
        toplevel = Path(
            _git_bytes(root, "rev-parse", "--show-toplevel").decode("utf-8").strip()
        ).resolve(strict=True)
        if root != toplevel:
            return {
                "status": "FAIL",
                "head_commit": None,
                "reason": "Evidence was checked from a different repository root.",
            }
        commit = _git_bytes(root, "rev-parse", "--verify", f"{source_commit}^{{commit}}")
        if commit.decode("ascii").strip() != source_commit:
            return {
                "status": "FAIL",
                "head_commit": None,
                "reason": "The evidence source commit is not a full commit ID.",
            }
        head = _git_bytes(root, "rev-parse", "HEAD").decode("ascii").strip()
        tree_paths = _git_paths(root, "ls-tree", "-r", "--name-only", "-z", source_commit)
        missing_prefixes = [
            prefix
            for prefix in REQUIRED_TRACKED_PREFIXES
            if not any(path.startswith(prefix) for path in tree_paths)
        ]
        if missing_prefixes:
            return {
                "status": "FAIL",
                "head_commit": head,
                "reason": "The evidence commit does not track all required source areas.",
            }
        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", source_commit, head],
            cwd=root,
            capture_output=True,
            check=False,
            timeout=30,
        )
        if ancestry.returncode != 0:
            return {
                "status": "FAIL",
                "head_commit": head,
                "reason": "The evidence source commit is not an ancestor of HEAD.",
            }

        changed_history = _git_paths(
            root,
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            source_commit,
            head,
        )
        changed_worktree = _git_paths(
            root,
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            "HEAD",
        )
        untracked = _git_paths(root, "ls-files", "--others", "--exclude-standard", "-z")
        if any(_is_source_path(path) for path in (*changed_history, *changed_worktree, *untracked)):
            return {
                "status": "FAIL",
                "head_commit": head,
                "reason": "Relevant source changed after the tested commit.",
            }
        return {
            "status": "PASS",
            "head_commit": head,
            "reason": "The tested commit is an ancestor and relevant source is unchanged.",
        }
    except (GateError, OSError, UnicodeDecodeError, subprocess.TimeoutExpired):
        return {
            "status": "FAIL",
            "head_commit": None,
            "reason": "Git source state could not be verified.",
        }


def _combine(checks: dict[str, dict[str, Any]], required: tuple[str, ...]) -> dict[str, Any]:
    failed = [check_id for check_id in required if checks[check_id]["status"] == "FAIL"]
    not_run = [check_id for check_id in required if checks[check_id]["status"] == "NOT_RUN"]
    if failed:
        status = "FAIL"
    elif not_run:
        status = "BLOCKED"
    else:
        status = "PASS"
    return {
        "status": status,
        "required_checks": list(required),
        "failed_checks": failed,
        "not_run_checks": not_run,
    }


def evaluate_manifest(
    profile: str,
    evidence_path: str | Path,
    *,
    repo_root: str | Path = ROOT,
) -> tuple[dict[str, Any], int]:
    if profile not in {"demo", "historical_research"}:
        raise GateError("Profile must be demo or historical_research.")
    manifest, evidence_root, evidence_digest = _load_manifest(Path(evidence_path))
    _require_keys(
        manifest,
        {"schema_version", "profile", "source_commit", "checks", "research"},
        "Evidence manifest",
    )
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != SCHEMA_VERSION:
        raise GateError("Evidence manifest schema_version is not supported.")
    if manifest["profile"] != profile:
        raise GateError("CLI profile does not match the evidence manifest.")
    source_commit = manifest["source_commit"]
    if not isinstance(source_commit, str) or not GIT_COMMIT_PATTERN.fullmatch(source_commit):
        raise GateError("source_commit must be a full lowercase Git commit ID.")

    artifact_cache: dict[str, tuple[str, str]] = {}
    checks = _validate_checks(manifest["checks"], source_commit, evidence_root, artifact_cache)
    research = _validate_research(
        manifest["research"],
        profile,
        checks,
        evidence_root,
        artifact_cache,
    )
    binding = _source_binding(Path(repo_root), source_commit)

    if binding["status"] == "FAIL":
        verdicts = {
            "local_engineering": {
                "status": "FAIL",
                "required_checks": list(ENGINEERING_CHECKS),
                "failed_checks": ["source_binding"],
                "not_run_checks": [],
            },
            "security_and_containers": {
                "status": "FAIL",
                "required_checks": list(SECURITY_CONTAINER_CHECKS),
                "failed_checks": ["source_binding"],
                "not_run_checks": [],
            },
            "hosted_ci": {
                "status": "FAIL",
                "required_checks": ["hosted_ci"],
                "failed_checks": ["source_binding"],
                "not_run_checks": [],
            },
            "demo_qualification": {
                "status": "FAIL",
                "required_checks": list(DEMO_CHECKS),
                "failed_checks": ["source_binding"],
                "not_run_checks": [],
            },
            "scientific_qualification": {
                "status": "FAIL",
                "required_checks": list(SCIENCE_CHECKS),
                "failed_checks": ["source_binding"],
                "not_run_checks": [],
            },
            "actual_production_readiness": {
                "status": "FAIL",
                "required_checks": [*DEMO_CHECKS, *PRODUCTION_CHECKS],
                "failed_checks": ["source_binding"],
                "not_run_checks": [],
            },
        }
    else:
        local_engineering = _combine(checks, ENGINEERING_CHECKS)
        security_and_containers = _combine(checks, SECURITY_CONTAINER_CHECKS)
        hosted_ci = _combine(checks, ("hosted_ci",))
        demo_qualification = _combine(checks, DEMO_CHECKS)
        if profile == "demo":
            scientific_qualification = {
                "status": "NOT_QUALIFIED",
                "required_checks": list(SCIENCE_CHECKS),
                "failed_checks": [],
                "not_run_checks": list(SCIENCE_CHECKS),
            }
            production_checks = [*DEMO_CHECKS, *PRODUCTION_CHECKS]
        else:
            scientific_qualification = _combine(checks, SCIENCE_CHECKS)
            production_checks = [*DEMO_CHECKS, *SCIENCE_CHECKS, *PRODUCTION_CHECKS]
        actual_production_readiness = _combine(checks, tuple(production_checks))
        verdicts = {
            "local_engineering": local_engineering,
            "security_and_containers": security_and_containers,
            "hosted_ci": hosted_ci,
            "demo_qualification": demo_qualification,
            "scientific_qualification": scientific_qualification,
            "actual_production_readiness": actual_production_readiness,
        }

    if profile == "demo":
        requested_status = verdicts["demo_qualification"]["status"]
    else:
        requested_status = _combine(
            {
                "demo": {"status": verdicts["demo_qualification"]["status"]},
                "science": {"status": verdicts["scientific_qualification"]["status"]},
            },
            ("demo", "science"),
        )["status"]
    for verdict in verdicts.values():
        if verdict['status'] == 'PASS':
            verdict['status'] = 'REVIEW_REQUIRED'
    if requested_status == 'PASS':
        requested_status = 'REVIEW_REQUIRED'
    report = {
        "schema_version": SCHEMA_VERSION,
        "profile": profile,
        "source_commit": source_commit,
        "head_commit": binding["head_commit"],
        "evidence_manifest_sha256": evidence_digest,
        "source_binding": binding,
        "requested_profile_qualification": requested_status,
        "verdicts": verdicts,
        "scope": "Receipt consistency only. Artifact contents and producers are not authenticated; this tool cannot grant release, hosted CI, scientific, or production approval.",
    }
    return report, 1


def _write_new_report(path: Path, report: dict[str, Any]) -> None:
    output = path.absolute()
    if not output.parent.is_dir():
        raise GateError("Report output directory does not exist.")
    payload = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_BINARY", 0)
    try:
        descriptor = os.open(output, flags, 0o600)
    except FileExistsError as error:
        raise GateError("Report output already exists; choose a new path.") from error
    except OSError as error:
        raise GateError("Report output cannot be created.") from error
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def main(argv: list[str] | None = None, *, repo_root: str | Path = ROOT) -> int:
    parser = argparse.ArgumentParser(description="Validate Cadrisyn release evidence.")
    parser.add_argument("--profile", required=True, choices=("demo", "historical_research"))
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args(argv)

    try:
        report, exit_code = evaluate_manifest(
            arguments.profile,
            arguments.evidence,
            repo_root=repo_root,
        )
        _write_new_report(arguments.output, report)
    except GateError as error:
        print(f"release gate: {error}", file=sys.stderr)
        return 2

    print(f"profile qualification: {report['requested_profile_qualification']}")
    for name, verdict in report["verdicts"].items():
        print(f"{name}: {verdict['status']}")
    print("release gate report written")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
