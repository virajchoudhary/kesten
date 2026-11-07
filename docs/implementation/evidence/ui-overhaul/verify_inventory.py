import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
manifest = json.loads((root / "inventory.json").read_text(encoding="utf-8"))
failures = []
for entry in manifest["files"]:
    path = root / entry["path"]
    if not path.is_file():
        failures.append(entry["path"])
        continue
    raw = path.read_bytes()
    if entry["normalize_lf"]:
        raw = raw.replace(b"\r\n", b"\n")
    if len(raw) != entry["bytes"] or hashlib.sha256(raw).hexdigest() != entry["sha256"]:
        failures.append(entry["path"])
print(json.dumps({"checked": len(manifest["files"]), "failures": failures}))
raise SystemExit(bool(failures))
