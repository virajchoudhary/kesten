from math import isfinite


_METHOD_IDS = {"last_close", "historical_log_mean"}
_ROW_KEY_FIELDS = ("partition", "model_id", "origin", "target", "input_sha256", "information_cutoff")


def compare_run_compatibility(left, right):
    left_result = left.result if type(left.result) is dict else {}
    right_result = right.result if type(right.result) is dict else {}
    reasons = []
    if (
        left_result.get("data_kind") != left.dataset.payload.get("data_kind")
        or right_result.get("data_kind") != right.dataset.payload.get("data_kind")
        or left_result.get("data_kind") != right_result.get("data_kind")
    ):
        reasons.append("data_kind_mismatch")
    if left_result.get("empirical_performance_established") is not False or right_result.get("empirical_performance_established") is not False:
        reasons.append("unqualified_performance_claim")

    if left.dataset_id != right.dataset_id:
        reasons.append("dataset_mismatch")
    if (
        left.dataset.version != right.dataset.version
        or left_result.get("dataset_version") != left.dataset.version
        or right_result.get("dataset_version") != right.dataset.version
    ):
        reasons.append("dataset_version_mismatch")

    left_target = left_result.get("target")
    right_target = right_result.get("target")
    if (
        type(left_target) is not dict
        or type(right_target) is not dict
        or left_target != right_target
        or left_target.get("horizon_sessions") != left.horizon_sessions
        or right_target.get("horizon_sessions") != right.horizon_sessions
    ):
        reasons.append("target_mismatch")

    left_protocol = left_result.get("protocol")
    right_protocol = right_result.get("protocol")
    if (
        type(left_protocol) is not dict
        or type(right_protocol) is not dict
        or left_protocol != right_protocol
    ):
        reasons.append("protocol_mismatch")

    if (
        not isinstance(left_result.get("engine_version"), str)
        or left_result.get("engine_version") != right_result.get("engine_version")
    ):
        reasons.append("engine_version_mismatch")

    if _method_versions(left_result) is None or _method_versions(left_result) != _method_versions(right_result):
        reasons.append("method_version_mismatch")

    if type(left.runtime) is not dict or type(right.runtime) is not dict or left.runtime != right.runtime:
        reasons.append("runtime_mismatch")

    left_rows = _index_rows(left_result)
    right_rows = _index_rows(right_result)
    if left_rows is None or right_rows is None or left_rows.keys() != right_rows.keys():
        reasons.append("row_alignment_mismatch")
    elif any(
        not _same_number(left_rows[key].get(field), right_rows[key].get(field))
        for key in left_rows
        for field in ("actual", "origin_value")
    ):
        reasons.append("row_values_mismatch")

    return {
        "left_id": str(left.id),
        "right_id": str(right.id),
        "compatible": not reasons,
        "reasons": reasons,
    }


def _method_versions(result):
    models = result.get("models")
    if type(models) is not list or len(models) != len(_METHOD_IDS):
        return None
    versions = {}
    for method in models:
        if type(method) is not dict:
            return None
        method_id = method.get("id")
        version = method.get("version")
        if method_id not in _METHOD_IDS or not isinstance(version, str) or method_id in versions:
            return None
        versions[method_id] = version
    if versions.keys() != _METHOD_IDS:
        return None
    return tuple(sorted(versions.items()))


def _index_rows(result):
    rows = result.get("evaluation_rows")
    if type(rows) is not list or not rows:
        return None
    indexed = {}
    for row in rows:
        if type(row) is not dict:
            return None
        if row.get("model_id") not in _METHOD_IDS or row.get("partition") not in {"validation", "test"}:
            return None
        key = tuple(row.get(field) for field in _ROW_KEY_FIELDS)
        if any(not isinstance(value, str) or not value for value in key) or key in indexed:
            return None
        indexed[key] = row
    return indexed


def _same_number(left, right):
    if type(left) not in (int, float) or type(right) not in (int, float):
        return False
    return isfinite(left) and isfinite(right) and left == right
