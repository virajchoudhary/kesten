import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "production-qualification.yml"
EXPECTED_ACTION_PINS = {
    "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
    "actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1",
    "actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0",
    "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
}
QUALIFIED_IMAGES = (
    ("api", "API_IMAGE_ID", "api_image_id"),
    ("web", "WEB_IMAGE_ID", "web_image_id"),
    ("database", "DATABASE_IMAGE_ID", "database_image_id"),
    ("cache", "CACHE_IMAGE_ID", "cache_image_id"),
    ("gateway", "GATEWAY_IMAGE_ID", "gateway_image_id"),
)


def qualification_base_image(service):
    compose_path = ROOT / "deploy" / "compose.production-qualification.yaml"
    services = yaml.load(compose_path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)["services"]
    image = services[service]["image"]
    prefix = f"${{QUALIFICATION_{service.upper()}_IMAGE:-"
    if not image.startswith(prefix) or not image.endswith("}"):
        raise AssertionError(f"{service} must use its pinned qualification image fallback")
    return image[len(prefix):-1]


class ProductionWorkflowTests(unittest.TestCase):
    def test_production_overlay_preserves_the_existing_preview_ports(self):
        preview = yaml.load((ROOT / "deploy/compose.qualification.yaml").read_text(), Loader=yaml.BaseLoader)["services"]
        self.assertEqual(preview["database"]["ports"], ["127.0.0.1:15435:5432"])
        self.assertEqual(preview["cache"]["ports"], ["127.0.0.1:16385:6379"])
        self.assertEqual(preview["gateway"]["ports"], ["127.0.0.1:8085:8080"])
        production = yaml.load((ROOT / "deploy/compose.production-qualification.yaml").read_text(), Loader=yaml.BaseLoader)["services"]
        self.assertNotIn("ports", production["database"])
        self.assertNotIn("ports", production["cache"])

    @classmethod
    def setUpClass(cls):
        cls.workflow = yaml.load(WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        cls.job = cls.workflow["jobs"]["production-qualification"]
        cls.steps = {step.get("name"): step for step in cls.job["steps"]}

    def test_triggers_are_additive_and_permissions_are_read_only(self):
        self.assertEqual({"pull_request", "push", "workflow_dispatch"}, set(self.workflow["on"]))
        self.assertEqual({"contents": "read"}, self.workflow["permissions"])
        self.assertEqual({"production-qualification"}, set(self.workflow["jobs"]))
        for job in self.workflow["jobs"].values():
            self.assertNotIn("permissions", job)
        self.assertEqual("90", self.job["timeout-minutes"])

    def test_actions_are_official_pinned_commits_and_checkout_has_no_token_persistence(self):
        uses = {
            step["uses"]
            for job in self.workflow["jobs"].values()
            for step in job["steps"]
            if "uses" in step
        }
        self.assertEqual(EXPECTED_ACTION_PINS, uses)
        for action in uses:
            self.assertRegex(action, r"^(?:actions)/[a-z-]+@[0-9a-f]{40}$")

        checkout = self.steps["Check out source"]
        self.assertEqual("false", checkout["with"]["persist-credentials"])
        self.assertEqual("3.12", self.steps["Set up Python 3.12"]["with"]["python-version"])
        self.assertEqual(
            "22.23.4",
            self.steps["Set up Node.js 22.23.4"]["with"]["node-version"],
        )

    def test_production_rehearsal_builds_and_passes_all_five_immutable_images(self):
        build_step = self.steps["Build all production stack images from tested source"]
        build = build_step["run"]
        self.assertEqual(5, build.count("docker build "))
        self.assertEqual(2, build.count('--build-arg "CADRISYN_SOURCE_REVISION=${GITHUB_SHA}"'))
        self.assertIn("--file backend/Dockerfile", build)
        self.assertIn("--file web/Dockerfile", build)
        self.assertIn("--file deploy/Dockerfile.debian-security", build)
        self.assertEqual(2, build.count("--file deploy/Dockerfile.alpine-security"))
        for base_image in ("DATABASE_BASE_IMAGE", "CACHE_BASE_IMAGE", "GATEWAY_BASE_IMAGE"):
            with self.subTest(base_image=base_image):
                self.assertIn(f'"BASE_IMAGE=${{{base_image}}}"', build)
        self.assertEqual(qualification_base_image("database"), build_step["env"]["DATABASE_BASE_IMAGE"])
        self.assertEqual(qualification_base_image("cache"), build_step["env"]["CACHE_BASE_IMAGE"])
        self.assertEqual(qualification_base_image("gateway"), build_step["env"]["GATEWAY_BASE_IMAGE"])

        for image, qualify_name, output_name in QUALIFIED_IMAGES:
            with self.subTest(image=image):
                self.assertIn(
                    f'{image}_image_id="$(docker image inspect "${image}_ref" --format \'{{{{.Id}}}}\')"',
                    build,
                )
                self.assertIn(f"{image}_image_id=%s", build)
                self.assertEqual(
                    f"${{{{ steps.build.outputs.{output_name} }}}}",
                    self.steps["Qualify demo and historical research stacks"]["env"][qualify_name],
                )
        self.assertIn(">> \"$GITHUB_OUTPUT\"", build)

        qualify = self.steps["Qualify demo and historical research stacks"]
        command = qualify["run"]
        self.assertIn("scripts/ops/qualify_production.py", command)
        self.assertIn("--directory .local/ci-production", command)
        for argument, name in (
            ("--api-image", "API"),
            ("--web-image", "WEB"),
            ("--database-image", "DATABASE"),
            ("--cache-image", "CACHE"),
            ("--gateway-image", "GATEWAY"),
        ):
            with self.subTest(argument=argument):
                self.assertIn(f'{argument} "${name}_IMAGE_ID"', command)
        self.assertIn("--tls-port 8452", command)
        self.assertIn("--http-port 8092", command)

    def test_scanner_uses_only_the_five_ids_already_qualified_in_this_job(self):
        collect = self.steps["Collect SBOM and vulnerability reports for qualified images"]
        self.assertEqual(
            {
                f"QUALIFIED_{name}": f"${{{{ steps.build.outputs.{output} }}}}"
                for _, name, output in QUALIFIED_IMAGES
            },
            {
                name: value
                for name, value in collect["env"].items()
                if name.endswith("_IMAGE_ID")
            },
        )
        run = collect["run"]
        self.assertEqual(5, run.count("--image "))
        self.assertIn("scripts/ops/image_evidence.py", run)
        self.assertIn("--output .local/ci-security", run)
        self.assertIn("--syft .local/ci-tools/syft", run)
        self.assertIn("--grype .local/ci-tools/grype", run)
        self.assertIn("--db-cache .local/ci-grype", run)
        for variable in (
            "QUALIFIED_API_IMAGE_ID",
            "QUALIFIED_WEB_IMAGE_ID",
            "QUALIFIED_DATABASE_IMAGE_ID",
            "QUALIFIED_CACHE_IMAGE_ID",
            "QUALIFIED_GATEWAY_IMAGE_ID",
        ):
            self.assertIn(f'--image "${variable}"', run)
        self.assertIn("collector_status=$?", run)
        self.assertIn('"$collector_status" -ne 0 && "$collector_status" -ne 1', run)
        self.assertIn('exit "$collector_status"', run)
        collector = (ROOT / "scripts" / "ops" / "image_evidence.py").read_text(encoding="utf-8")
        self.assertIn("'--fail-on', 'medium'", collector)
        self.assertIn("scan.returncode == 0", collector)
        self.assertIn("'ignored_match_count'", collector)
        self.assertNotIn("--only-fixed", collector)
        self.assertNotIn("production-image-security", self.workflow["jobs"])
        self.assertEqual(5, sum(step.get("run", "").count("docker build ") for step in self.job["steps"]))

    def test_scanner_tools_are_downloaded_from_official_releases_and_checksum_verified(self):
        install = self.steps["Install checksum-verified Syft and Grype binaries"]
        self.assertEqual({"1.57.0", "0.121.2"}, {install["env"]["SYFT_VERSION"], install["env"]["GRYPE_VERSION"]})
        run = install["run"]
        self.assertIn(
            "https://github.com/anchore/${tool}/releases/download/v${version}/${archive}",
            run,
        )
        self.assertIn(
            "https://github.com/anchore/${tool}/releases/download/v${version}/${checksums}",
            run,
        )
        self.assertIn("_linux_amd64.tar.gz", run)
        self.assertIn("_checksums.txt", run)
        self.assertIn("sha256sum --check --strict", run)
        self.assertIn("tar --extract --gzip", run)
        self.assertIn('tools_dir="$GITHUB_WORKSPACE/.local/ci-tools"', run)
        self.assertNotIn("| bash", run)
        self.assertNotIn("| sh", run)

        database = self.steps["Update fresh Grype vulnerability database"]
        self.assertEqual(".local/ci-grype", database["env"]["GRYPE_DB_CACHE_DIR"])
        self.assertEqual("false", database["env"]["GRYPE_DB_AUTO_UPDATE"])
        self.assertEqual("false", database["env"]["GRYPE_CHECK_FOR_APP_UPDATE"])
        self.assertIn(".local/ci-tools/grype db update", database["run"])
        self.assertIn(".local/ci-tools/grype db status --output json", database["run"])

    def _run_image_evidence_verifier(self, *, summary_update=None, receipt_update=None):
        verifier = self.steps["Collect SBOM and vulnerability reports for qualified images"]["run"]
        source = verifier.split(".venv/bin/python - <<'PY'\n", 1)[1].split("\nPY", 1)[0]
        source_sha = "a" * 40
        qualified_ids = {
            name: "sha256:" + digit * 64
            for (name, _, _), digit in zip(QUALIFIED_IMAGES, "12345")
        }
        receipt = {"result": "PASS", "source_commit": source_sha, "images": dict(qualified_ids)}
        rows = [
            {
                "reference": image_id,
                "image_id": image_id,
                "result": "PASS",
                "scan_completed": True,
                "sbom_exit_code": 0,
                "scan_exit_code": 0,
                "ignored_match_count": 0,
            }
            for image_id in qualified_ids.values()
        ]
        summary = {
            "collector_checkout_commit": source_sha,
            "result": "REVIEW_REQUIRED",
            "scan_policy": "PASS",
            "threshold": "medium",
            "suppressions": [],
            "images": rows,
        }
        if summary_update:
            summary_update(summary)
        if receipt_update:
            receipt_update(receipt)
        original_receipt = json.loads(json.dumps(receipt))

        with tempfile.TemporaryDirectory(dir=ROOT, prefix=".tmp-production-scan-policy-") as temporary_directory:
            local = Path(temporary_directory) / ".local"
            qualification = local / "ci-production"
            security = local / "ci-security"
            qualification.mkdir(parents=True)
            security.mkdir(parents=True)
            receipt_path = qualification / "receipt.json"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            (security / "summary.json").write_text(json.dumps(summary), encoding="utf-8")

            environment = os.environ.copy()
            environment["QUALIFIED_SOURCE_SHA"] = source_sha
            for name, image_id in qualified_ids.items():
                environment[f"QUALIFIED_{name.upper()}_IMAGE_ID"] = image_id
            completed = subprocess.run(
                [sys.executable, "-c", source],
                cwd=temporary_directory,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )
            resulting_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        return completed, original_receipt, resulting_receipt

    def test_image_evidence_verifier_accepts_only_a_passing_medium_scan_policy(self):
        passed, original_receipt, resulting_receipt = self._run_image_evidence_verifier()
        self.assertEqual(0, passed.returncode, passed.stderr)
        self.assertEqual(
            "Verified image scan policy only; this does not grant deployment approval.",
            passed.stdout.strip(),
        )
        self.assertEqual(original_receipt, resulting_receipt)

        def failed_policy(summary):
            summary["scan_policy"] = "FAIL"
            summary["result"] = "FAIL"

        def wrong_scanned_id(summary):
            summary["images"][0]["image_id"] = "sha256:" + "f" * 64

        def wrong_reference(summary):
            summary["images"][0]["reference"] = "sha256:" + "f" * 64

        def failed_image_row(summary):
            summary["images"][2]["result"] = "FAIL"

        def wrong_receipt_id(receipt):
            receipt["images"]["gateway"] = "sha256:" + "f" * 64

        def suppressed_finding(summary):
            summary["suppressions"] = ["CVE-EXAMPLE"]

        def hidden_ignored_match(summary):
            summary["images"][0]["ignored_match_count"] = 1

        def weakened_threshold(summary):
            summary["threshold"] = "critical"

        cases = (
            ("scan failure", failed_policy, None),
            ("one failed image row", failed_image_row, None),
            ("scanned image ID mismatch", wrong_scanned_id, None),
            ("scanner reference mismatch", wrong_reference, None),
            ("qualification receipt ID mismatch", None, wrong_receipt_id),
            ("suppression present", suppressed_finding, None),
            ("ignored match omitted from aggregate", hidden_ignored_match, None),
            ("severity threshold changed", weakened_threshold, None),
        )
        for label, update_summary, update_receipt in cases:
            with self.subTest(label=label):
                rejected, _, _ = self._run_image_evidence_verifier(
                    summary_update=update_summary,
                    receipt_update=update_receipt,
                )
                self.assertNotEqual(0, rejected.returncode)
                self.assertIn("Image scan evidence rejected:", rejected.stderr)

    def test_browser_acceptance_uses_the_tls_rehearsal_and_two_synthetic_accounts(self):
        setup_node = self.steps["Set up Node.js 22.23.4"]
        self.assertEqual(
            "actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1",
            setup_node["uses"],
        )
        self.assertEqual("npm ci --no-audit --no-fund", self.steps["Install frontend dependencies"]["run"])
        self.assertEqual(
            "npx playwright install --with-deps chromium",
            self.steps["Install Chromium for production browser qualification"]["run"],
        )
        browser = self.steps["Run isolated production browser acceptance"]
        self.assertGreater(
            [step["name"] for step in self.job["steps"]].index(browser["name"]),
            [step["name"] for step in self.job["steps"]].index("Qualify demo and historical research stacks"),
        )
        self.assertEqual("web", browser["working-directory"])
        self.assertEqual(
            "npx playwright test --config playwright.qualification.config.ts",
            browser["run"],
        )
        self.assertEqual(
            {
                "PLAYWRIGHT_BASE_URL": "https://localhost:8452",
                "CADRISYN_REHEARSAL_CERT": "${{ github.workspace }}/.local/ci-production/gateway_cert",
                "CADRISYN_RELEASE_CREDENTIALS": "${{ github.workspace }}/.local/ci-production/credentials.json",
                "KERQUANT_BROWSER_OUTPUT": "${{ github.workspace }}/.local/ci-browser",
            },
            browser["env"],
        )

        config = (ROOT / "web" / "playwright.qualification.config.ts").read_text(encoding="utf-8")
        spec = (ROOT / "web" / "e2e-production" / "qualification.spec.ts").read_text(encoding="utf-8")
        self.assertIn('testDir: "./e2e-production"', config)
        self.assertIn("z.tuple([account, account])", spec)
        self.assertNotIn("page.route(", spec)
        self.assertIn('fetch("/api/v1/research/runs/")', spec)
        self.assertIn('expect(run.data_kind).toBe("synthetic_fixture")', spec)

    def test_qualification_context_records_tested_and_pull_request_revisions(self):
        qualify = self.steps["Qualify demo and historical research stacks"]
        self.assertEqual(
            "${{ steps.build.outputs.api_image_id }}",
            qualify["env"]["API_IMAGE_ID"],
        )
        self.assertEqual(
            "${{ steps.build.outputs.web_image_id }}",
            qualify["env"]["WEB_IMAGE_ID"],
        )

        metadata = self.steps["Attach sanitized workflow metadata to receipt"]
        env = metadata["env"]
        self.assertEqual("${{ github.event_name }}", env["QUALIFICATION_EVENT_NAME"])
        self.assertEqual("${{ github.sha }}", env["QUALIFICATION_TESTED_SHA"])
        self.assertEqual(
            "${{ github.event.pull_request.head.sha || '' }}",
            env["QUALIFICATION_PR_HEAD_SHA"],
        )
        self.assertEqual(
            "${{ github.event_name == 'pull_request' && github.sha || '' }}",
            env["QUALIFICATION_PR_MERGE_SHA"],
        )

        self.assertEqual("always()", metadata["if"])
        source = metadata["run"]
        for field in ("event_name", "tested_sha", "pr_head_sha", "pr_merge_sha"):
            with self.subTest(field=field):
                self.assertIn(f'"{field}"', source)
        self.assertIn("re.fullmatch", source)
        self.assertIn('receipt.get("source_commit") != tested_sha', source)

    def test_pull_request_metadata_is_sanitized_and_source_bound(self):
        run = self.steps["Attach sanitized workflow metadata to receipt"]["run"]
        source = run.split(".venv/bin/python - <<'PY'\n", 1)[1].split("\nPY", 1)[0]
        tested_sha = "a" * 40
        head_sha = "b" * 40

        with tempfile.TemporaryDirectory(dir=ROOT, prefix=".tmp-production-workflow-") as temporary_directory:
            receipt_directory = Path(temporary_directory) / ".local" / "ci-production"
            receipt_directory.mkdir(parents=True)
            receipt_path = receipt_directory / "receipt.json"
            receipt_path.write_text(json.dumps({"source_commit": tested_sha}), encoding="utf-8")
            environment = os.environ.copy()
            environment.update(
                {
                    "QUALIFICATION_EVENT_NAME": "pull_request",
                    "QUALIFICATION_TESTED_SHA": tested_sha,
                    "QUALIFICATION_PR_HEAD_SHA": head_sha,
                    "QUALIFICATION_PR_MERGE_SHA": tested_sha,
                }
            )
            subprocess.run(
                [sys.executable, "-c", source],
                cwd=temporary_directory,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )

            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(
                {
                    "event_name": "pull_request",
                    "tested_sha": tested_sha,
                    "pr_head_sha": head_sha,
                    "pr_merge_sha": tested_sha,
                },
                receipt["workflow_metadata"],
            )

    def test_only_sanitized_receipt_and_scanner_reports_are_uploaded(self):
        uploads = [
            step for step in self.job["steps"]
            if step.get("uses", "").startswith("actions/upload-artifact@")
        ]
        self.assertEqual(1, len(uploads))
        upload = uploads[0]
        self.assertEqual("always()", upload["if"])
        self.assertEqual(
            [
                ".local/ci-production/receipt.json",
                ".local/ci-security/summary.json",
                ".local/ci-security/*-sbom.spdx.json",
                ".local/ci-security/*-vulnerabilities.json",
            ],
            upload["with"]["path"].splitlines(),
        )
        self.assertEqual("ignore", upload["with"]["if-no-files-found"])
        self.assertEqual("7", upload["with"]["retention-days"])
        self.assertEqual("true", upload["with"]["include-hidden-files"])

    def test_workflow_has_no_repository_or_image_publish_commands_or_scan_waivers(self):
        source = WORKFLOW_PATH.read_text(encoding="utf-8").lower()
        for forbidden in (
            "docker push ",
            "git push ",
            "docker login ",
            "permissions: write",
            "production-image-security",
            "only-fixed",
            "continue-on-error",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

        for step in self.job["steps"]:
            if "uses" in step:
                self.assertRegex(step["uses"], re.compile(r"^[^@]+@[0-9a-f]{40}$"))


if __name__ == "__main__":
    unittest.main()
