import hashlib
import json
import math
from datetime import date, timedelta
from typing import Any

from .calendar import get_xnys_calendar, next_session, session_close_utc
from .dataset import canonical_json
from .errors import DatasetError
from .features import split_neutral_prices
from .types import Dataset

_MODEL_IDS = ("last_close", "historical_log_mean")
_PARTITIONS = ("validation", "test")
_PROTOCOL_ID = "expanding-60-20-20-v1"


def evaluate(dataset: Dataset, *, horizon: int) -> dict[str, Any]:
    if not isinstance(dataset, Dataset):
        raise DatasetError("dataset must be a parsed Dataset.")
    if type(horizon) is not int or horizon not in {1, 5}:
        raise DatasetError("horizon must be the integer 1 or 5.")

    payload = dataset.payload
    observations = payload["observations"]
    prices = split_neutral_prices(observations)
    count = len(observations)
    train_boundary = int(count * 0.6)
    validation_boundary = int(count * 0.8)
    first_target = horizon + 1
    if first_target >= train_boundary:
        raise DatasetError("Dataset is too short for the fixed training partition.")

    calendar = _calendar_for(payload, horizon)
    prefix_hashes = _input_prefix_hashes(payload)
    log_mean_by_origin = _expanding_log_means(prices)
    records = []
    for target_index in range(first_target, count):
        if target_index < train_boundary:
            continue
        partition = "validation" if target_index < validation_boundary else "test"
        origin_index = target_index - horizon
        origin_value = prices[origin_index]
        actual = prices[target_index]
        historical_prediction = _scaled_exponential(
            origin_value,
            log_mean_by_origin[origin_index],
            horizon,
        )
        origin_session = observations[origin_index]["session"]
        cutoff = session_close_utc(calendar, origin_session) + timedelta(minutes=60)
        records.append(
            {
                "partition": partition,
                "origin": origin_session,
                "target": observations[target_index]["session"],
                "information_cutoff": cutoff.isoformat(),
                "origin_value": origin_value,
                "actual": actual,
                "input_sha256": prefix_hashes[origin_index],
                "predictions": {
                    "last_close": origin_value,
                    "historical_log_mean": historical_prediction,
                },
            }
        )

    if not records:
        raise DatasetError("The dataset has no validation or test targets for this horizon.")

    model_rows = []
    model_inputs = {
        model_id: {partition: [] for partition in _PARTITIONS}
        for model_id in _MODEL_IDS
    }
    for model_id in _MODEL_IDS:
        for record in records:
            predicted = record["predictions"][model_id]
            predicted_return = _finite_return(predicted, record["origin_value"])
            actual_return = _finite_return(record["actual"], record["origin_value"])
            model_inputs[model_id][record["partition"]].append(
                (predicted, record["actual"], predicted_return, actual_return)
            )
            model_rows.append(
                {
                    "model_id": model_id,
                    "partition": record["partition"],
                    "origin": record["origin"],
                    "target": record["target"],
                    "information_cutoff": record["information_cutoff"],
                    "origin_value": record["origin_value"],
                    "predicted": predicted,
                    "actual": record["actual"],
                    "input_sha256": record["input_sha256"],
                }
            )

    baseline_mae = {
        partition: _mean_absolute_error(model_inputs["last_close"][partition])
        for partition in _PARTITIONS
    }
    evaluation = []
    for model_id in _MODEL_IDS:
        for partition in _PARTITIONS:
            values = model_inputs[model_id][partition]
            if not values:
                raise DatasetError(f"The {partition} partition has no scoreable targets.")
            mae = _mean_absolute_error(values)
            evaluation.append(
                {
                    "model_id": model_id,
                    "partition": partition,
                    "n": len(values),
                    "mae": mae,
                    "rmse": _root_mean_square_error(values),
                    "return_mae": _mean_return_error(values),
                    "return_rmse": _root_mean_square_return_error(values),
                    "directional_accuracy": _directional_accuracy(values),
                    "direction_confusion": _direction_confusion(values),
                    "mae_difference_vs_last_close": mae - baseline_mae[partition],
                }
            )

    last_session = observations[-1]["session"]
    future_sessions = []
    previous_session = last_session
    for _ in range(horizon):
        previous_session = next_session(calendar, previous_session)
        future_sessions.append(previous_session)
    forecast_origin = prices[-1]
    forecast_log_mean = log_mean_by_origin[-1]
    forecast_points = {}
    for model_id in _MODEL_IDS:
        points = [{"time": last_session, "value": forecast_origin}]
        for step, session in enumerate(future_sessions, start=1):
            if model_id == "last_close":
                value = forecast_origin
            else:
                value = _scaled_exponential(forecast_origin, forecast_log_mean, step)
            points.append({"time": session, "value": value})
        forecast_points[model_id] = points

    protocol = {
        "id": _PROTOCOL_ID,
        "train_start": observations[first_target]["session"],
        "train_end": observations[train_boundary - 1]["session"],
        "validation_start": observations[train_boundary]["session"],
        "validation_end": observations[validation_boundary - 1]["session"],
        "test_start": observations[validation_boundary]["session"],
        "test_end": observations[-1]["session"],
        "training_policy": (
            "No tuned hyperparameters; historical log mean estimates expanding split-neutral one-session "
            "log returns through each origin and projects a geometric drift reference path."
        ),
        "configuration_trials": 1,
        "directional_policy": (
            "Classify the origin-to-target simple price return by sign; exact zero is neutral."
        ),
        "issue_lag_minutes": 60,
    }
    protocol["protocol_sha256"] = hashlib.sha256(
        canonical_json(protocol).encode("utf-8")
    ).hexdigest()

    forecast_cutoff = session_close_utc(calendar, last_session) + timedelta(minutes=60)
    limitations = [
        "Dividends are excluded; values are split-neutral close prices in initial-share units.",
        "This fixed descriptive protocol does not establish empirical performance.",
        (
            "No statistical significance, prediction intervals, tuning, or model promotion "
            "is performed."
        ),
    ]
    if dataset.data_kind == "synthetic_fixture":
        limitations.insert(
            0,
            "Synthetic fixture data only; results are pipeline checks, not market evidence.",
        )
    else:
        limitations.insert(
            0,
            (
                "Historical results are descriptive only; source truth, action completeness, "
                "and licensing are supplied by the operator and not independently verified."
            ),
        )

    result = {
        "schema_version": 1,
        "engine_version": "baseline-v1",
        "dataset_version": dataset.version,
        "data_kind": dataset.data_kind,
        "empirical_performance_established": False,
        "evidence_kind": (
            "synthetic_pipeline_check"
            if dataset.data_kind == "synthetic_fixture"
            else "historical_walk_forward"
        ),
        "target": {
            "name": "split_neutral_close",
            "horizon_sessions": horizon,
            "units": "USD per initial share; dividends excluded",
            "return_convention": "simple price return",
        },
        "protocol": protocol,
        "models": [
            {"id": "last_close", "label": "Last close", "version": "1"},
            {
                "id": "historical_log_mean",
                "label": "Historical log mean",
                "version": "1",
            },
        ],
        "evaluation": evaluation,
        "evaluation_rows": model_rows,
        "forecast": {
            "origin": last_session,
            "information_cutoff": forecast_cutoff.isoformat(),
            "history": [
                {"time": observation["session"], "value": price}
                for observation, price in zip(observations[-80:], prices[-80:])
            ],
            "models": [
                {"model_id": model_id, "points": forecast_points[model_id]}
                for model_id in _MODEL_IDS
            ],
        },
        "limitations": limitations,
    }
    _validate_json_result(result)
    return result


def _calendar_for(payload: dict, horizon: int):
    first = date.fromisoformat(payload["observations"][0]["session"])
    last = date.fromisoformat(payload["observations"][-1]["session"])
    return get_xnys_calendar(first, last, forecast_sessions=horizon)


def _expanding_log_means(prices: list[float]) -> list[float]:
    means = [0.0]
    running_sum = 0.0
    compensation = 0.0
    try:
        for count in range(1, len(prices)):
            log_return = math.log(prices[count]) - math.log(prices[count - 1])
            adjusted = log_return - compensation
            updated = running_sum + adjusted
            compensation = (updated - running_sum) - adjusted
            running_sum = updated
            mean = running_sum / count
            if not math.isfinite(mean):
                raise DatasetError("Historical log-return calculation is not finite.")
            means.append(mean)
    except (OverflowError, ValueError) as exc:
        raise DatasetError("Historical log-return calculation overflowed.") from exc
    return means


def _scaled_exponential(origin_value: float, mean_log_return: float, horizon: int) -> float:
    try:
        growth = math.exp(mean_log_return * horizon)
        prediction = origin_value * growth
    except OverflowError as exc:
        raise DatasetError("Forecast calculation overflowed.") from exc
    if not math.isfinite(growth) or growth <= 0 or not math.isfinite(prediction) or prediction <= 0:
        raise DatasetError("Forecast calculation is outside the finite positive range.")
    return prediction


def _input_prefix_hashes(payload: dict) -> list[str]:
    metadata = {key: value for key, value in payload.items() if key != "observations"}
    state = hashlib.sha256(
        b"cadrisyn-research-input-prefix-v1\0"
        + canonical_json(metadata).encode("utf-8")
    ).digest()
    hashes = []
    for observation in payload["observations"]:
        row = canonical_json(observation).encode("utf-8")
        state = hashlib.sha256(state + len(row).to_bytes(8, "big") + row).digest()
        hashes.append(state.hex())
    return hashes


def _finite_return(value: float, origin: float) -> float:
    result = value / origin - 1.0
    if not math.isfinite(result):
        raise DatasetError("Price return calculation overflowed.")
    return result


def _mean_absolute_error(values: list[tuple[float, float, float, float]]) -> float:
    errors = [abs(predicted - actual) for predicted, actual, _, _ in values]
    return _scaled_mean(errors)


def _root_mean_square_error(values: list[tuple[float, float, float, float]]) -> float:
    errors = [abs(predicted - actual) for predicted, actual, _, _ in values]
    return _scaled_rms(errors)


def _mean_return_error(values: list[tuple[float, float, float, float]]) -> float:
    errors = [
        abs(predicted_return - actual_return)
        for _, _, predicted_return, actual_return in values
    ]
    return _scaled_mean(errors)


def _root_mean_square_return_error(values: list[tuple[float, float, float, float]]) -> float:
    errors = [
        abs(predicted_return - actual_return)
        for _, _, predicted_return, actual_return in values
    ]
    return _scaled_rms(errors)


def _scaled_mean(errors: list[float]) -> float:
    scale = max(errors)
    if scale == 0:
        return 0.0
    try:
        result = scale * (math.fsum(error / scale for error in errors) / len(errors))
    except (OverflowError, ZeroDivisionError) as exc:
        raise DatasetError("Metric calculation overflowed.") from exc
    if not math.isfinite(result):
        raise DatasetError("Metric calculation overflowed.")
    return result


def _scaled_rms(errors: list[float]) -> float:
    scale = max(errors)
    if scale == 0:
        return 0.0
    try:
        result = scale * math.sqrt(
            math.fsum((error / scale) ** 2 for error in errors) / len(errors)
        )
    except (OverflowError, ZeroDivisionError) as exc:
        raise DatasetError("Metric calculation overflowed.") from exc
    if not math.isfinite(result):
        raise DatasetError("Metric calculation overflowed.")
    return result


def _direction(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _directional_accuracy(values: list[tuple[float, float, float, float]]) -> float:
    correct = sum(
        _direction(predicted_return) == _direction(actual_return)
        for _, _, predicted_return, actual_return in values
    )
    return correct / len(values)


def _direction_confusion(values: list[tuple[float, float, float, float]]) -> list[list[int]]:
    positions = {-1: 0, 0: 1, 1: 2}
    matrix = [[0, 0, 0] for _ in range(3)]
    for _, _, predicted_return, actual_return in values:
        row = positions[_direction(predicted_return)]
        column = positions[_direction(actual_return)]
        matrix[row][column] += 1
    return matrix


def _validate_json_result(result: dict[str, Any]) -> None:
    try:
        json.dumps(result, allow_nan=False, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError, OverflowError) as exc:
        raise DatasetError("Evaluation result contains non-finite or non-JSON values.") from exc
