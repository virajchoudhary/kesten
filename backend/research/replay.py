import hashlib
import json

from django.utils import timezone

from .services import runtime_manifest


def result_hash(result):
    return hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def replay_run(run):
    from .quant import evaluate, parse_dataset

    dataset = parse_dataset(run.dataset.payload, now=timezone.now())
    current = runtime_manifest()
    replayed = evaluate(dataset, horizon=run.horizon_sessions)
    replayed_hash = result_hash(replayed)
    checks = {
        "dataset_matches": dataset.version == run.dataset.version,
        "engine_matches": current["engine_source_sha256"] == run.runtime["engine_source_sha256"],
        "dependency_lock_matches": current["dependency_lock_sha256"] == run.runtime["dependency_lock_sha256"],
        "runtime_versions_match": current["python"] == run.runtime["python"] and current["dependencies"] == run.runtime["dependencies"],
        "result_matches": replayed_hash == result_hash(run.result),
    }
    return {
        "run_id": str(run.id),
        "result": "PASS" if all(checks.values()) else "FAIL",
        **checks,
        "result_sha256": replayed_hash,
    }
