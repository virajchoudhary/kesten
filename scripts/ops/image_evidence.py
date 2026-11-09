"""Inventory and scan local immutable images without suppressing advisory findings."""

import argparse
import hashlib
import json
import os
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def command(arguments, environment=None):
    return subprocess.run(list(map(str, arguments)), cwd=ROOT, env=environment, capture_output=True, text=True, check=False)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(images, output, syft, grype, database):
    output.mkdir(parents=True, exist_ok=False)
    environment = os.environ.copy()
    environment.update(GRYPE_DB_CACHE_DIR=str(database.resolve()), GRYPE_DB_AUTO_UPDATE='false', GRYPE_CHECK_FOR_APP_UPDATE='false')
    status = command([grype, 'db', 'status', '-o', 'json'], environment)
    (output / 'advisory-database.json').write_text(status.stdout, encoding='utf-8')
    if status.returncode:
        raise RuntimeError('A valid pre-initialized advisory database is required; no image was marked passing.')
    versions = {name: command([executable, 'version', '-o', 'json']).stdout for name, executable in [('syft', syft), ('grype', grype)]}
    source = command(['git', 'rev-parse', 'HEAD']).stdout.strip()
    rows = []
    for index, image in enumerate(images):
        inspected = command(['docker', 'image', 'inspect', image])
        inspected.check_returncode()
        metadata = json.loads(inspected.stdout)[0]
        image_id = metadata['Id']
        prefix = str(index + 1)
        sbom = output / (prefix + '-sbom.spdx.json')
        inventory = command([syft, 'docker:' + image_id, '-o', 'spdx-json=' + str(sbom)])
        (output / (prefix + '-sbom.log')).write_text(inventory.stderr, encoding='utf-8')
        findings = output / (prefix + '-vulnerabilities.json')
        scan = command([grype, 'docker:' + image_id, '--fail-on', 'medium', '--output', 'json', '--file', findings], environment)
        (output / (prefix + '-scan.log')).write_text(scan.stderr, encoding='utf-8')
        counts = {}
        ignored_count = 0
        ignore_rule_count = 0
        valid_report = False
        if findings.is_file():
            try:
                report = json.loads(findings.read_text(encoding='utf-8'))
                counts = dict(Counter(match['vulnerability']['severity'] for match in report['matches']))
                ignored = report.get('ignoredMatches') or []
                valid_report = isinstance(report['matches'], list) and isinstance(ignored, list)
                ignored_count = len(ignored)
                ignore_rule_count = len(report.get('descriptor', {}).get('configuration', {}).get('ignore') or [])
            except (ValueError, KeyError, TypeError):
                pass
        rows.append({
            'reference': image, 'image_id': image_id, 'repository_digests': metadata.get('RepoDigests', []),
            'revision_label': (metadata.get('Config', {}).get('Labels') or {}).get('org.opencontainers.image.revision'),
            'sbom_exit_code': inventory.returncode, 'scan_exit_code': scan.returncode,
            'scan_completed': valid_report and scan.returncode in {0, 2},
            'severity_counts': counts,
            'ignored_match_count': ignored_count, 'configured_ignore_rule_count': ignore_rule_count,
            'artifacts': [{'path': path.name, 'sha256': digest(path)} for path in [sbom, findings] if path.is_file()],
            'result': 'PASS' if inventory.returncode == 0 and sbom.is_file() and valid_report and scan.returncode == 0 and ignored_count == 0 else 'FAIL',
        })
    result = {
        'created_at': datetime.now(UTC).isoformat(), 'collector_checkout_commit': source,
        'working_tree_dirty': bool(command(['git', 'status', '--porcelain']).stdout),
        'source_binding': 'UNVERIFIED',
        'tool_versions': versions, 'advisory_database_sha256': digest(output / 'advisory-database.json'),
        'threshold': 'medium', 'suppressions': [
            {'image_id': row['image_id'], 'ignored_matches': row['ignored_match_count']}
            for row in rows if row['ignored_match_count']
        ], 'images': rows,
        'scope': 'Local inventory and advisory receipts; not signed provenance, hosted CI, or production approval.',
        'scan_policy': 'PASS' if all(row['result'] == 'PASS' for row in rows) else 'FAIL',
        'result': 'REVIEW_REQUIRED' if all(row['result'] == 'PASS' for row in rows) else 'FAIL',
    }
    (output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ['result', 'collector_checkout_commit', 'source_binding', 'images']}, indent=2))
    return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--syft', required=True)
    parser.add_argument('--grype', required=True)
    parser.add_argument('--db-cache', type=Path, required=True)
    args = parser.parse_args()
    return collect(args.image, args.output, args.syft, args.grype, args.db_cache)


if __name__ == '__main__':
    raise SystemExit(main())
