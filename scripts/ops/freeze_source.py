"""Freeze committed source bytes with a hash manifest, excluding working edits."""

import argparse
import hashlib
import json
import ntpath
import os
import re
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
_FULL_SHA = re.compile(r"[0-9a-f]{40}\Z")
_WINDOWS_NAMES = {"CON", "PRN", "AUX", "NUL"} | {
    f"{prefix}{number}" for prefix in ("COM", "LPT") for number in range(1, 10)
}


def _git(*arguments):
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result = subprocess.run(
        ["git", *arguments], cwd=ROOT, env=environment,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise ValueError("Git could not resolve or read the requested committed source.")
    return result.stdout


def _safe_parts(name):
    if not name or "\x00" in name or "\\" in name or name.startswith("/") or ntpath.splitdrive(name)[0]:
        raise ValueError("The committed source contains an unsafe archive path.")
    parts = name.rstrip("/").split("/")
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ValueError("The committed source contains an unsafe archive path.")
    for part in parts:
        if any(character in part for character in '<>:"|?*') or part.endswith((".", " ")):
            raise ValueError("The committed source contains a non-portable archive path.")
        if part.split(".", 1)[0].upper() in _WINDOWS_NAMES:
            raise ValueError("The committed source contains a non-portable archive path.")
    return tuple(PurePosixPath(*parts).parts)


def _contains_private_path(path):
    parts = [part.casefold() for part in PurePosixPath(path).parts]
    name = parts[-1]
    templates = (".example", ".sample", ".template")
    if any(part in {"secrets", "credentials"} for part in parts):
        return True
    if name == ".env" or name.endswith(".env") or name.startswith(".env."):
        if not name.endswith(templates):
            return True
    if name.endswith((".key", ".pem", ".p12", ".pfx", ".keystore")):
        return True
    if name in {"id_rsa", "id_ed25519", "id_ecdsa", "id_dsa", "credentials.json", "credentials.txt", "credentials.csv", ".netrc"}:
        return True
    return False


def _tree_entries(commit):
    entries = {}
    portable_prefixes = {}
    for row in _git("ls-tree", "-rz", "--full-tree", commit).split(b"\0"):
        if not row:
            continue
        metadata, raw_path = row.split(b"\t", 1)
        mode, kind, object_id = metadata.decode("ascii").split()
        path = raw_path.decode("utf-8")
        parts = _safe_parts(path)
        for length in range(1, len(parts) + 1):
            prefix = "/".join(parts[:length])
            folded = prefix.casefold()
            if portable_prefixes.setdefault(folded, prefix) != prefix:
                raise ValueError("The committed source contains a case-insensitive path collision.")
        if mode == "120000" or kind != "blob":
            raise ValueError("The committed source contains a symlink or submodule, which is unsupported.")
        if mode not in {"100644", "100755"}:
            raise ValueError("The committed source contains an unsupported file mode.")
        if _contains_private_path(path):
            raise ValueError("The committed source includes an environment or private-key file.")
        if path in entries:
            raise ValueError("The committed source contains a duplicate path.")
        entries[path] = {"mode": mode, "git_blob": object_id}
    return entries


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extract_archive(archive_path, tree_path, expected):
    seen = set()
    portable_names = set()
    files = []
    tree_path.mkdir()
    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            unix_mode = (info.external_attr >> 16) & 0xFFFF
            kind = stat.S_IFMT(unix_mode)
            if kind == stat.S_IFLNK:
                raise ValueError("The Git archive contains an unsupported symlink.")
            if kind not in {0, stat.S_IFREG, stat.S_IFDIR}:
                raise ValueError("The Git archive contains an unsupported file type.")
            parts = _safe_parts(info.filename)
            relative = "/".join(parts)
            if info.is_dir():
                if kind == stat.S_IFREG:
                    raise ValueError("The Git archive has inconsistent entry metadata.")
                continue
            if kind == stat.S_IFDIR or relative not in expected or relative in seen:
                raise ValueError("The Git archive does not match the committed source tree.")
            portable = relative.casefold()
            if portable in portable_names:
                raise ValueError("The Git archive contains colliding paths.")
            portable_names.add(portable)
            seen.add(relative)
            output = tree_path.joinpath(*parts)
            if not output.resolve().is_relative_to(tree_path.resolve()):
                raise ValueError("The Git archive contains a path outside the bundle.")
            output.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            git_digest = hashlib.sha1(b"blob " + str(info.file_size).encode("ascii") + b"\0")
            size = 0
            with archive.open(info) as source, output.open("xb") as target:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    target.write(chunk)
                    digest.update(chunk)
                    git_digest.update(chunk)
                    size += len(chunk)
            if git_digest.hexdigest() != expected[relative]["git_blob"]:
                raise ValueError("The archive content differs from its committed Git blob.")
            if os.name != "nt":
                output.chmod(0o755 if expected[relative]["mode"] == "100755" else 0o644)
            files.append({
                "path": relative,
                "git_blob": expected[relative]["git_blob"],
                "sha256": digest.hexdigest(),
                "size_bytes": size,
            })
    if seen != set(expected):
        raise ValueError("The Git archive omits files from the committed source tree.")
    return sorted(files, key=lambda item: item["path"])


def freeze_source(revision: str, directory: Path):
    from scripts.ops.prepare_local_tls import protect_directory

    if not isinstance(revision, str) or _FULL_SHA.fullmatch(revision) is None:
        raise ValueError("revision must be a full lowercase 40-character commit SHA.")
    commit = _git("rev-parse", "--verify", "--end-of-options", f"{revision}^{{commit}}").decode("ascii").strip()
    if commit != revision:
        raise ValueError("revision must identify the exact commit object.")
    expected = _tree_entries(commit)
    tree_id = _git("rev-parse", f"{commit}^{{tree}}").decode("ascii").strip()
    commit_epoch = int(_git("show", "-s", "--format=%ct", commit).decode("ascii").strip())

    root = ROOT.resolve()
    local = root / ".local"
    if local.is_symlink() or (local.exists() and not local.is_dir()):
        raise ValueError("The repository .local path must be a real directory.")
    requested_destination = Path(directory).expanduser()
    if not requested_destination.is_absolute():
        requested_destination = Path.cwd() / requested_destination
    destination = requested_destination.resolve()
    if destination == local or not destination.is_relative_to(local):
        raise ValueError("The bundle directory must be a new path strictly inside the repository .local directory.")
    if requested_destination.exists() or requested_destination.is_symlink() or destination.exists():
        raise FileExistsError("The bundle directory already exists; refusing to overwrite it.")

    local.mkdir(mode=0o700, parents=True, exist_ok=True)
    if local.is_symlink() or local.resolve() != local:
        raise ValueError("The repository .local path must be a real directory.")
    with tempfile.TemporaryDirectory(prefix="freeze-source-", dir=local) as temporary:
        staging = Path(temporary)
        protect_directory(staging)
        archive_path = staging / "source.zip"
        environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        with archive_path.open("xb") as archive_file:
            result = subprocess.run(
                ["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf", "-c", f"core.attributesFile={os.devnull}", "archive", "--format=zip", commit],
                cwd=root, env=environment, stdout=archive_file, stderr=subprocess.PIPE,
            )
        if result.returncode:
            raise ValueError("Git could not export the requested committed source.")
        files = _extract_archive(archive_path, staging / "tree", expected)
        receipt = {
            "commit": commit,
            "tree": tree_id,
            "commit_epoch": commit_epoch,
            "archive_sha256": _sha256(archive_path),
            "files": files,
        }
        (staging / "receipt.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.mkdir(mode=0o700, exist_ok=False)
        protect_directory(destination)
        for name in ("source.zip", "tree", "receipt.json"):
            os.replace(staging / name, destination / name)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True, help="full 40-character commit SHA")
    parser.add_argument("--directory", required=True, type=Path)
    arguments = parser.parse_args(argv)
    try:
        receipt = freeze_source(arguments.revision, arguments.directory)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"freeze_source: {error}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
