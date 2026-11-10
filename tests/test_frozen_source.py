import hashlib
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from scripts.ops import freeze_source


WORKSPACE = Path(__file__).resolve().parents[1]


class FrozenSourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix=".test-frozen-source-", dir=WORKSPACE)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self._git("init", "--quiet")
        self._git("config", "user.name", "Frozen Source Test")
        self._git("config", "user.email", "frozen-source@example.invalid")
        self._git("config", "commit.gpgsign", "false")
        self._git("config", "core.hooksPath", str(self.root / "disabled-hooks"))

    def _git(self, *arguments, input_bytes=None):
        return subprocess.run(
            ["git", *arguments],
            cwd=self.root,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        ).stdout

    def _commit(self, files):
        for name, contents in files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
        self._git("add", "-A")
        self._git("commit", "--quiet", "-m", "fixture")
        return self._git("rev-parse", "HEAD").decode("ascii").strip()

    def test_commit_export_avoids_checkout_crlf_and_matches_git_blobs(self):
        source = b"alpha = 1\nbeta = 2\n"
        binary = b"\x00\xff\x10\r\n\x80"
        revision = self._commit({"src/analysis.py": source, "assets/model.bin": binary})
        self._git("config", "core.autocrlf", "true")
        (self.root / "src/analysis.py").unlink()
        self._git("checkout-index", "--force", "--all")

        checked_out = (self.root / "src/analysis.py").read_bytes()
        self.assertIn(b"\r\n", checked_out)
        self.assertNotEqual(checked_out, source)
        legacy_zip = self.root / "legacy-working-tree.zip"
        with zipfile.ZipFile(legacy_zip, "w") as archive:
            archive.write(self.root / "src/analysis.py", "src/analysis.py")
        with zipfile.ZipFile(legacy_zip) as archive:
            self.assertIn(b"\r\n", archive.read("src/analysis.py"))

        destination = self.root / ".local" / "canonical"
        with patch.object(freeze_source, "ROOT", self.root):
            receipt = freeze_source.freeze_source(revision, destination)

        self.assertEqual((destination / "tree/src/analysis.py").read_bytes(), source)
        self.assertEqual((destination / "tree/assets/model.bin").read_bytes(), binary)
        for relative_path, expected in [
            ("src/analysis.py", source),
            ("assets/model.bin", binary),
        ]:
            blob = self._git("cat-file", "blob", f"{revision}:{relative_path}")
            self.assertEqual((destination / "tree" / relative_path).read_bytes(), blob)
            record = next(row for row in receipt["files"] if row["path"] == relative_path)
            self.assertEqual(record["sha256"], hashlib.sha256(expected).hexdigest())
        self.assertEqual(receipt["commit"], revision)
        self.assertEqual(
            receipt["archive_sha256"],
            hashlib.sha256((destination / "source.zip").read_bytes()).hexdigest(),
        )
        receipt_text = (destination / "receipt.json").read_text()
        self.assertEqual(json.loads(receipt_text)["commit"], revision)
        self.assertNotIn(source.decode("ascii"), receipt_text)
        self._git("config", "core.autocrlf", "false")
        with patch.object(freeze_source, "ROOT", self.root):
            second_receipt = freeze_source.freeze_source(revision, self.root / ".local" / "second")
        self.assertEqual(
            (destination / "source.zip").read_bytes(),
            (self.root / ".local" / "second" / "source.zip").read_bytes(),
        )
        self.assertEqual(receipt["archive_sha256"], second_receipt["archive_sha256"])

    def test_dirty_and_untracked_files_are_excluded(self):
        original = b"committed = True\n"
        revision = self._commit({"src/module.py": original})
        (self.root / "src/module.py").write_bytes(b"working edit = True\n")
        (self.root / "untracked-private.txt").write_text("not part of the commit")

        destination = self.root / ".local" / "frozen"
        with patch.object(freeze_source, "ROOT", self.root):
            receipt = freeze_source.freeze_source(revision, destination)

        self.assertEqual((destination / "tree/src/module.py").read_bytes(), original)
        self.assertFalse((destination / "tree/untracked-private.txt").exists())
        self.assertEqual([row["path"] for row in receipt["files"]], ["src/module.py"])

    def test_source_reports_are_allowed_and_external_eol_settings_are_ignored(self):
        files = {
            "src/secrets.py": b"def redact(value): return '[redacted]'\n",
            "docs/known-credential-scan.json": b'{"findings": []}\n',
        }
        revision = self._commit(files)
        attributes = self.root / "local-attributes"
        attributes.write_text("*.py eol=crlf\n")
        self._git("config", "core.attributesFile", str(attributes))
        self._git("config", "core.eol", "crlf")
        with patch.object(freeze_source, "ROOT", self.root):
            receipt = freeze_source.freeze_source(revision, self.root / ".local" / "canonical")
        self.assertEqual({row["path"] for row in receipt["files"]}, set(files))
        for name, content in files.items():
            self.assertEqual((self.root / ".local/canonical/tree" / name).read_bytes(), content)

    def test_uncommitted_export_substitution_cannot_forge_blob_identity(self):
        revision = self._commit({"metadata.txt": b"commit=$Format:%H$\n"})
        (self.root / ".git/info/attributes").write_text("metadata.txt export-subst\n")
        destination = self.root / ".local" / "rejected"
        with patch.object(freeze_source, "ROOT", self.root):
            with self.assertRaisesRegex(ValueError, "differs from its committed Git blob"):
                freeze_source.freeze_source(revision, destination)
        self.assertFalse(destination.exists())

    def test_invalid_revisions_and_unsafe_destinations_do_not_create_output(self):
        revision = self._commit({"src/module.py": b"pass\n"})
        local = self.root / ".local"
        destination = local / "frozen"
        with patch.object(freeze_source, "ROOT", self.root):
            for invalid in ("HEAD", "f" * 40):
                with self.subTest(revision=invalid), self.assertRaises(ValueError):
                    freeze_source.freeze_source(invalid, destination)
                self.assertFalse(local.exists())
            with self.assertRaises(ValueError):
                freeze_source.freeze_source(revision, local)
            outside = self.root / "outside"
            with self.assertRaises(ValueError):
                freeze_source.freeze_source(revision, outside)
            self.assertFalse(outside.exists())
            destination.mkdir(parents=True)
            sentinel = destination / "preserve.txt"
            sentinel.write_text("existing user data")
            with self.assertRaises(FileExistsError):
                freeze_source.freeze_source(revision, destination)
            self.assertEqual(sentinel.read_text(), "existing user data")

    def test_committed_symlinks_are_rejected(self):
        self._commit({"src/module.py": b"pass\n"})
        target_blob = self._git("hash-object", "-w", "--stdin", input_bytes=b"target").decode("ascii").strip()
        self._git("update-index", "--add", "--cacheinfo", f"120000,{target_blob},links/current")
        self._git("commit", "--quiet", "-m", "add tracked symlink")
        linked_revision = self._git("rev-parse", "HEAD").decode("ascii").strip()
        with patch.object(freeze_source, "ROOT", self.root):
            with self.assertRaisesRegex(ValueError, "symlink"):
                freeze_source.freeze_source(linked_revision, self.root / ".local" / "linked")
        self.assertFalse((self.root / ".local").exists())

    def test_runtime_environment_files_are_rejected(self):
        environment_revision = self._commit({".env": b"API_TOKEN=fixture-only\n"})
        with patch.object(freeze_source, "ROOT", self.root):
            with self.assertRaisesRegex(ValueError, "environment"):
                freeze_source.freeze_source(environment_revision, self.root / ".local" / "environment")
        self.assertFalse((self.root / ".local").exists())

    def test_malicious_tree_path_is_rejected_before_output(self):
        blob_id = self._git("hash-object", "-w", "--stdin", input_bytes=b"outside").decode("ascii").strip()
        tree_bytes = b"100644 ../escape.txt\0" + bytes.fromhex(blob_id)
        tree_id = self._git(
            "hash-object", "--literally", "-t", "tree", "-w", "--stdin", input_bytes=tree_bytes
        ).decode("ascii").strip()
        revision = self._git("commit-tree", tree_id, "-m", "unsafe tree").decode("ascii").strip()

        with patch.object(freeze_source, "ROOT", self.root):
            with self.assertRaisesRegex(ValueError, "unsafe archive path"):
                freeze_source.freeze_source(revision, self.root / ".local" / "unsafe")
        self.assertFalse((self.root / ".local").exists())
        self.assertFalse((self.root.parent / "escape.txt").exists())


if __name__ == "__main__":
    unittest.main()
