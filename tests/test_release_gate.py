import hashlib
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.ops import release_gate


WORKSPACE = Path(__file__).resolve().parents[1]


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self._create_repository()

    def _git(self, *arguments):
        return subprocess.run(
            ["git", *arguments],
            cwd=self.root,
            capture_output=True,
            check=True,
            timeout=10,
        ).stdout.decode("utf-8").strip()

    def _commit(self, message):
        self._git("add", "-A")
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Release Gate Test",
                "-c",
                "user.email=release-gate@example.invalid",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-m",
                message,
            ],
            cwd=self.root,
            capture_output=True,
            check=True,
            timeout=10,
        )

    def _create_repository(self):
        subprocess.run(
            ["git", "init", "--quiet"],
            cwd=self.root,
            capture_output=True,
            check=True,
            timeout=10,
        )
        source_files = {
            ".github/workflows/workspace.yml": "name: test\n",
            "backend/app.py": "VALUE = 1\n",
            "deploy/compose.yaml": "services: {}\n",
            "scripts/check.py": "pass\n",
            "tests/test_app.py": "pass\n",
            "web/app.tsx": "export {};\n",
            "docs/implementation/README.md": "# Evidence\n",
        }
        for name, contents in source_files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding="utf-8")
        self._commit("tested source")
        self.source_commit = self._git("rev-parse", "HEAD")

    def _create_demo_receipt(self):
        evidence_dir = self.root / "evidence"
        evidence_dir.mkdir()
        checks = {}
        for check_id in release_gate.CHECK_IDS:
            status = "PASS" if check_id in release_gate.DEMO_CHECKS else "NOT_RUN"
            artifacts = []
            exit_code = None
            if status == "PASS":
                path = evidence_dir / "checks" / f"{check_id}.txt"
                path.parent.mkdir(exist_ok=True)
                contents = f"synthetic receipt fixture for {check_id}\n".encode("utf-8")
                path.write_bytes(contents)
                artifacts.append(
                    {
                        "path": f"checks/{check_id}.txt",
                        "sha256": hashlib.sha256(contents).hexdigest(),
                    }
                )
                exit_code = 0
            checks[check_id] = {
                "status": status,
                "exit_code": exit_code,
                "source_commit": self.source_commit,
                "artifacts": artifacts,
            }
        manifest = {
            "schema_version": release_gate.SCHEMA_VERSION,
            "profile": "demo",
            "source_commit": self.source_commit,
            "checks": checks,
            "research": {
                "kind": "synthetic_fixture",
                "contains_synthetic": True,
                "dataset": None,
                "evaluation": None,
            },
        }
        manifest_path = evidence_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest_path, manifest

    def test_demo_profile_reports_synthetic_research_without_empirical_pass(self):
        manifest_path, _ = self._create_demo_receipt()

        report, exit_code = release_gate.evaluate_manifest(
            "demo",
            manifest_path,
            repo_root=self.root,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(report["verdicts"]["local_engineering"]["status"], "REVIEW_REQUIRED")
        self.assertEqual(report["verdicts"]["security_and_containers"]["status"], "REVIEW_REQUIRED")
        self.assertEqual(report["verdicts"]["hosted_ci"]["status"], "REVIEW_REQUIRED")
        self.assertEqual(report["verdicts"]["demo_qualification"]["status"], "REVIEW_REQUIRED")
        self.assertEqual(report["verdicts"]["scientific_qualification"]["status"], "NOT_QUALIFIED")
        self.assertEqual(
            report["verdicts"]["actual_production_readiness"]["status"],
            "BLOCKED",
        )

    def test_missing_mandatory_check_fails_closed(self):
        manifest_path, manifest = self._create_demo_receipt()
        del manifest["checks"]["accessibility"]
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        with self.assertRaisesRegex(release_gate.GateError, "missing accessibility"):
            release_gate.evaluate_manifest("demo", manifest_path, repo_root=self.root)

    def test_unknown_check_fails_closed(self):
        manifest_path, manifest = self._create_demo_receipt()
        manifest["checks"]["maybe_good_enough"] = manifest["checks"].pop("accessibility")
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        with self.assertRaisesRegex(release_gate.GateError, "unknown maybe_good_enough"):
            release_gate.evaluate_manifest("demo", manifest_path, repo_root=self.root)

    def test_pass_with_missing_artifact_or_nonzero_exit_is_rejected(self):
        manifest_path, manifest = self._create_demo_receipt()
        manifest["checks"]["image_scan"]["artifacts"] = []
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        with self.assertRaisesRegex(release_gate.GateError, "PASS requires exit_code 0"):
            release_gate.evaluate_manifest("demo", manifest_path, repo_root=self.root)

        manifest["checks"]["image_scan"]["artifacts"] = [
            {
                "path": "checks/image_scan.txt",
                "sha256": hashlib.sha256(
                    (manifest_path.parent / "checks" / "image_scan.txt").read_bytes()
                ).hexdigest(),
            }
        ]
        manifest["checks"]["image_scan"]["exit_code"] = 13
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(release_gate.GateError, "PASS requires exit_code 0"):
            release_gate.evaluate_manifest("demo", manifest_path, repo_root=self.root)

    def test_changed_artifact_bytes_reject_the_receipt(self):
        manifest_path, _ = self._create_demo_receipt()
        (manifest_path.parent / "checks" / "backend_tests.txt").write_text(
            "changed after receipt\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(release_gate.GateError, "SHA-256 does not match"):
            release_gate.evaluate_manifest("demo", manifest_path, repo_root=self.root)

    def test_security_failure_does_not_erase_independent_engineering_result(self):
        manifest_path, manifest = self._create_demo_receipt()
        manifest["checks"]["image_scan"]["status"] = "FAIL"
        manifest["checks"]["image_scan"]["exit_code"] = 1
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        report, exit_code = release_gate.evaluate_manifest(
            "demo",
            manifest_path,
            repo_root=self.root,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(report["verdicts"]["local_engineering"]["status"], "REVIEW_REQUIRED")
        self.assertEqual(report["verdicts"]["security_and_containers"]["status"], "FAIL")
        self.assertEqual(report["verdicts"]["demo_qualification"]["status"], "FAIL")

    def test_historical_profile_rejects_synthetic_fixture_evidence(self):
        manifest_path, manifest = self._create_demo_receipt()
        manifest["profile"] = "historical_research"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        with self.assertRaisesRegex(release_gate.GateError, "qualified_historical data"):
            release_gate.evaluate_manifest(
                "historical_research",
                manifest_path,
                repo_root=self.root,
            )

    def test_source_change_after_tested_commit_prevents_pass(self):
        manifest_path, _ = self._create_demo_receipt()
        source_path = self.root / "backend" / "app.py"
        source_path.write_text("VALUE = 2\n", encoding="utf-8")
        self._commit("change tested source")

        report, exit_code = release_gate.evaluate_manifest(
            "demo",
            manifest_path,
            repo_root=self.root,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(report["source_binding"]["status"], "FAIL")
        self.assertEqual(report["verdicts"]["demo_qualification"]["status"], "FAIL")
        self.assertNotIn(
            "PASS",
            [verdict["status"] for verdict in report["verdicts"].values()],
        )

    def test_docs_and_evidence_followup_commit_preserves_source_binding(self):
        manifest_path, _ = self._create_demo_receipt()
        docs_path = self.root / "docs" / "implementation" / "followup.md"
        docs_path.write_text("Receipt explanation.\n", encoding="utf-8")
        self._commit("document evidence")

        report, exit_code = release_gate.evaluate_manifest(
            "demo",
            manifest_path,
            repo_root=self.root,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(report["source_binding"]["status"], "PASS")

    def test_cli_writes_report_without_overwriting_and_returns_profile_status(self):
        manifest_path, _ = self._create_demo_receipt()
        output_path = self.root / "report.json"

        exit_code = release_gate.main(
            [
                "--profile",
                "demo",
                "--evidence",
                str(manifest_path),
                "--output",
                str(output_path),
            ],
            repo_root=self.root,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(
            json.loads(output_path.read_text(encoding="utf-8"))[
                "requested_profile_qualification"
            ],
            "REVIEW_REQUIRED",
        )
        with self.assertRaisesRegex(release_gate.GateError, "already exists"):
            release_gate._write_new_report(output_path, {})

    def test_workflow_yaml_parses_and_all_actions_use_full_commit_pins(self):
        workflow_paths = (
            WORKSPACE / ".github" / "workflows" / "workspace.yml",
            WORKSPACE / ".github" / "workflows" / "security.yml",
        )
        workflows = [yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader) for path in workflow_paths]
        for workflow in workflows:
            self.assertEqual(workflow["permissions"], {"contents": "read"})
            self.assertEqual(workflow["concurrency"]["cancel-in-progress"], "true")
            for node in self._walk(workflow):
                if isinstance(node, dict) and "uses" in node:
                    self.assertRegex(node["uses"], r"^[^@]+@[0-9a-f]{40}$")

        workspace_jobs = workflows[0]["jobs"]
        self.assertTrue(
            {
                "backend",
                "numerical",
                "frontend",
                "browser",
                "postgresql",
                "containers",
                "recovery",
            }.issubset(workspace_jobs)
        )
        self.assertEqual(workspace_jobs["browser"]["timeout-minutes"], "30")
        self.assertEqual(
            workflows[1]["jobs"]["app-image-scan"]["strategy"]["fail-fast"],
            "false",
        )

    def test_workflows_do_not_upload_browser_or_runtime_data(self):
        for name in ("workspace.yml", "security.yml"):
            workflow = yaml.load(
                (WORKSPACE / ".github" / "workflows" / name).read_text(encoding="utf-8"),
                Loader=yaml.BaseLoader,
            )
            for node in self._walk(workflow):
                if not isinstance(node, dict):
                    continue
                action = node.get("uses", "")
                if not action.startswith("actions/upload-artifact@"):
                    continue
                artifact_path = str(node.get("with", {}).get("path", "")).lower()
                for forbidden in (
                    ".local",
                    ".env",
                    ".sqlite",
                    "test-results",
                    "screenshots",
                    "playwright-report",
                    "trace.zip",
                    "token",
                    "dump",
                ):
                    self.assertNotIn(forbidden, artifact_path)
                retention = int(node.get("with", {}).get("retention-days", "0"))
                self.assertGreater(retention, 0)
                self.assertLessEqual(retention, 7)

    def _walk(self, value):
        if isinstance(value, dict):
            yield value
            for nested in value.values():
                yield from self._walk(nested)
        elif isinstance(value, list):
            for nested in value:
                yield from self._walk(nested)


if __name__ == "__main__":
    unittest.main()
