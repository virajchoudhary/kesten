"""Validate the discovery package without running or modifying the application."""

import hashlib
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = Path(__file__).resolve().parent


def main():
    failures = []
    links_checked = 0
    references_checked = 0
    markdown_files = list(PACKAGE.glob("*.md"))
    for path in markdown_files:
        content = path.read_text(encoding="utf-8-sig")
        if content.count("```") % 2:
            failures.append(f"Unbalanced code fence in {path.name}")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
            if re.match(r"https?://", target) or target.startswith("#"):
                continue
            target = target.split("#")[0]
            links_checked += 1
            if not (path.parent / target).exists():
                failures.append(f"Missing link in {path.name}: {target}")
        for relative, first, last in re.findall(r"((?:backend|frontend|agents|decision|quant_reporter|quant_testing|scripts|tests)/[A-Za-z0-9_./-]+\.py):(\d+)(?:-(\d+))?", content):
            source = ROOT / relative
            references_checked += 1
            if not source.is_file():
                failures.append(f"Missing source in {path.name}: {relative}")
                continue
            line_count = len(source.read_text(encoding="utf-8-sig").splitlines())
            if not 1 <= int(first) <= int(last or first) <= line_count:
                failures.append(f"Invalid source range in {path.name}: {relative}:{first}-{last}")

    json_files = list(PACKAGE.glob("*.json"))
    for path in json_files:
        json.loads(path.read_text(encoding="utf-8-sig"))

    baseline = json.loads((PACKAGE / "baseline.json").read_text(encoding="utf-8-sig"))
    database_hash = hashlib.sha256((ROOT / "backend/db.sqlite3").read_bytes()).hexdigest().upper()
    database_preserved = database_hash == baseline["database_sha256"]
    if not database_preserved:
        failures.append("Database bytes differ from the captured baseline")

    changed = subprocess.check_output(["git", "diff", "--name-only", "HEAD"], cwd=ROOT, text=True).splitlines()
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines()
    unexpected = [p for p in changed if p != "backend/db.sqlite3" and not p.startswith("docs/rebrand/")]
    unexpected += [p for p in untracked if not p.startswith("docs/rebrand/")]
    if unexpected or staged:
        failures.append(f"Unexpected scope changes or staged files: {unexpected + staged}")

    coverage = {
        "1 repository discovery": ["01-repository-audit.md", "audit-probe-results.json"],
        "2 five screened brands": ["02-brand-research.md", "public-name-checks.json", "domain-checks-followup.json", "search-engine-checks.json", "connected-github-check.json"],
        "3 three brand concepts": ["03-brand-concepts.md"],
        "4 design system": ["04-design-system.md"],
        "5 site and user behavior": ["05-product-specification.md"],
        "6 target architecture": ["06-architecture.md", "11-sources-and-verification.md"],
        "7 security data operations quant gates": ["07-security-data-operations.md", "08-quantitative-verification.md"],
        "8 phased migration": ["09-migration-roadmap.md"],
        "9 reviewable Markdown and approval stop": ["README.md", "10-approval-gate.md", "review-notes.md"],
    }
    for files in coverage.values():
        for name in files:
            if not (PACKAGE / name).is_file():
                failures.append(f"Missing coverage artifact: {name}")

    report = {
        "result": "PASS" if not failures else "FAIL",
        "scope": "Package integrity and working-tree preservation only, not application correctness or production acceptance.",
        "relative_links_checked": links_checked,
        "source_references_checked_for_file_and_line_bounds": references_checked,
        "markdown_files": len(markdown_files),
        "json_files_read": len(json_files),
        "database_sha256": database_hash,
        "database_preserved": database_preserved,
        "tracked_changes": changed,
        "all_new_files_under_docs_rebrand": not any(not p.startswith("docs/rebrand/") for p in untracked),
        "requirements_coverage_map": coverage,
        "limitations": ["Links to the web are cited research sources, not fetched again by this check.", "Source line bounds do not prove semantic accuracy; parent source inspection and independent review supply that evidence.", "Existing syntax and quantitative defects remain recorded in the audit receipt.", "Django suite, browser flows, exact dependency resolution, deployment and scientific validation remain unverified."],
        "failures": failures,
    }
    print(json.dumps(report, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
