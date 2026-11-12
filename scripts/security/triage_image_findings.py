"""Deduplicate hash-bound scanner evidence without granting scan exemptions."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


def _load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def analyze(directory, images, assessments, repository_root=None):
    evidence_root = (repository_root or Path(__file__).resolve().parents[2]).resolve()
    summary = _load(directory / "summary.json")
    cohort = images["images"]
    if not cohort or len(cohort) != len(summary["images"]):
        raise ValueError("Image manifest and scan cohort differ.")
    findings = []
    groups = defaultdict(list)
    identities = []
    for index, (image, scan) in enumerate(zip(cohort, summary["images"]), 1):
        if image["image_id"] != scan["image_id"] or not scan["scan_completed"]:
            raise ValueError("The scan does not bind to the requested completed image cohort.")
        artifacts = {}
        for artifact in scan["artifacts"]:
            name = artifact["path"]
            if Path(name).name != name or "\\" in name:
                raise ValueError("Scanner artifact paths must be local filenames.")
            if _digest(directory / name) != artifact["sha256"]:
                raise ValueError("Scanner artifact checksum mismatch: " + name)
            artifacts[name] = artifact["sha256"]
        filename = f"{index}-vulnerabilities.json"
        if filename not in artifacts:
            raise ValueError("The raw finding report is not hash-bound.")
        report = _load(directory / filename)
        target = report["source"]["target"]
        digests = {value.rsplit("@", 1)[-1] for value in target.get("repoDigests", [])}
        if image["image_id"] not in digests | {target.get("imageID")}:
            raise ValueError("Raw scanner image identity does not match the image manifest.")
        counts = dict(Counter(match["vulnerability"]["severity"] for match in report["matches"]))
        if counts != scan["severity_counts"]:
            raise ValueError("Raw findings disagree with the recorded severity counts.")
        identities.append({"service": image["service"], "image_id": image["image_id"],
                           "scanner_config_id": target.get("imageID"), "raw_artifacts": artifacts,
                           "scan_result": scan["result"], "ignored_matches": len(report.get("ignoredMatches") or [])})
        for ordinal, match in enumerate(report["matches"]):
            package, advisory = match["artifact"], match["vulnerability"]
            upstream = sorted({item["name"] for item in package.get("upstreams", [])})
            family = "+".join(upstream) if upstream else package["name"]
            key = family + "|" + advisory["id"]
            row = {"raw_id": image["service"] + ":" + str(ordinal), "service": image["service"],
                   "image_id": image["image_id"], "group": key, "source_dependency": family,
                   "package": package["name"], "version": package["version"], "package_type": package["type"],
                   "package_id": package.get("id"), "purl": package.get("purl"),
                   "inventory_paths": sorted({location["path"] for location in package.get("locations", [])}),
                   "advisory": advisory["id"], "namespace": advisory["namespace"], "severity": advisory["severity"],
                   "match_types": sorted({detail["type"] for detail in match["matchDetails"]}),
                   "scanner_fix": advisory.get("fix", {}), "source_url": advisory.get("dataSource"),
                   "raw_reference": filename + "#/matches/" + str(ordinal)}
            findings.append(row)
            groups[key].append(row)
    unknown = set(assessments) - set(groups)
    if unknown:
        raise ValueError("Assessments reference absent source/advisory groups: " + ", ".join(sorted(unknown)))
    reviewed = []
    for key, rows in sorted(groups.items()):
        assessment = assessments.get(key)
        if key in assessments and (not isinstance(assessment, dict) or
                                   any(not assessment.get(field) for field in ("disposition", "exposure", "rationale", "evidence"))):
            raise ValueError("Assessment lacks its decision, exposure, rationale or evidence: " + key)
        if assessment:
            if not isinstance(assessment["evidence"], list):
                raise ValueError("Assessment evidence must be a list of references: " + key)
            for reference in assessment["evidence"]:
                if not isinstance(reference, str):
                    raise ValueError("Assessment evidence must contain string references: " + key)
                if reference.startswith(("https://", "http://")):
                    continue
                path = (evidence_root / reference).resolve()
                if not path.is_relative_to(evidence_root) or not path.is_file():
                    raise ValueError("Missing or outside-root assessment evidence: " + reference)
        reviewed.append({"group": key, "source_dependency": rows[0]["source_dependency"],
                         "advisory": rows[0]["advisory"], "raw_ids": [row["raw_id"] for row in rows],
                         "raw_count": len(rows), "services": sorted({row["service"] for row in rows}),
                         "packages": sorted({row["package"] for row in rows}),
                         "versions": sorted({row["version"] for row in rows}), "assessment": assessment})
    missing = sorted(set(groups) - set(assessments))
    advisory_groups = defaultdict(list)
    for row in findings:
        advisory_groups[row["advisory"]].append(row)
    advisories = [{"advisory": key, "raw_count": len(rows),
                   "source_groups": sorted({row["group"] for row in rows}),
                   "services": sorted({row["service"] for row in rows}),
                   "severity_labels": sorted({row["severity"] for row in rows})}
                  for key, rows in sorted(advisory_groups.items())]
    result = {"counts": {"raw_matches": len(findings), "advisory_ids": len({row["advisory"] for row in findings}),
                         "source_dependencies": len({row["source_dependency"] for row in findings}),
                         "source_advisory_pairs": len(groups),
                         "image_source_advisory_pairs": len({(row["service"], row["group"]) for row in findings})},
              "classification": "INCOMPLETE" if missing else "COMPLETE", "unreviewed": missing,
              "classification_changes_policy": False,
              "local_evidence_references_validated": True,
              "release_decision": "NO_GO" if any(row["result"] != "PASS" for row in summary["images"]) else "NOT_ASSESSED",
              "disposition_group_counts": dict(Counter(row["assessment"]["disposition"] for row in reviewed if row["assessment"])),
              "disposition_raw_counts": dict(Counter(row["assessment"]["disposition"] for row in reviewed for _ in row["raw_ids"] if row["assessment"])),
              "images": identities, "advisories": advisories, "groups": reviewed, "findings": findings,
              "scope": "Primary advisory IDs are exact, not fuzzy aliases. Source groups retain every image, package, version and raw match. Assessments never waive the original policy."}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan-directory", type=Path, required=True)
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--assessments", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    arguments = parser.parse_args()
    result = analyze(arguments.scan_directory, _load(arguments.images), _load(arguments.assessments), arguments.repository_root)
    arguments.output.mkdir(parents=True, exist_ok=False)
    for name, value in [("findings", result.pop("findings")), ("groups", result.pop("groups")),
                        ("advisories", result.pop("advisories")), ("summary", result)]:
        (arguments.output / (name + ".json")).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result["counts"]))
    return 2 if result["unreviewed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
