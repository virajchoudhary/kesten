"""Run bounded offline discovery probes without importing the application."""

import ast
import importlib.metadata
import importlib.util
import json
import math
from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd
import torch


ROOT = Path(__file__).resolve().parents[2]


def load_file(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def contrast(foreground, background):
    def luminance(color):
        channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        channels = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
        return sum(v * weight for v, weight in zip(channels, (0.2126, 0.7152, 0.0722)))

    values = sorted((luminance(foreground), luminance(background)))
    return (values[1] + 0.05) / (values[0] + 0.05)


def run():
    files = []
    for folder in ("backend", "frontend", "agents", "decision", "quant_reporter", "quant_testing", "tests", "scratch"):
        files.extend(p for p in (ROOT / folder).rglob("*.py") if not {"venv", "__pycache__", ".cache"}.intersection(p.parts) and not p.name.startswith("._"))
    parse_errors = []
    for path in files:
        try:
            ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        except SyntaxError as error:
            parse_errors.append({"path": path.relative_to(ROOT).as_posix(), "line": error.lineno, "error": error.msg})

    bs = load_file("rebrand_bsm_probe", "backend/api/black_scholes.py")
    args = (100, 105, 0.75, 0.04, 0.24, 0.01)
    call = bs.bs_call_price(*args)
    put = bs.bs_put_price(*args)
    parity_error = abs(call - put - (args[0] * math.exp(-args[5] * args[2]) - args[1] * math.exp(-args[3] * args[2])))
    iv = bs.implied_volatility(call, *args[:4], q=args[5])
    epsilon = 0.001
    delta_fd = (bs.bs_call_price(args[0] + epsilon, *args[1:]) - bs.bs_call_price(args[0] - epsilon, *args[1:])) / (2 * epsilon)
    delta = bs.greeks(*args)["call"]["delta"]
    assert parity_error < 1e-10
    assert abs(iv - args[4]) < 1e-7
    assert abs(delta - delta_fd) < 2e-6

    metrics = load_file("rebrand_metrics_probe", "quant_reporter/metrics.py")
    dip = pd.DataFrame({"asset": [100.0, 90.0, 100.0], "benchmark": [100.0, 101.0, 103.0]}, index=pd.date_range("2025-01-01", periods=3))
    dip_metrics, _ = metrics.calculate_metrics(dip, "asset", "benchmark")
    observed_drawdown = float(dip_metrics["Max Drawdown"].rstrip("%"))
    assert abs(observed_drawdown) < 1e-10
    dates = pd.bdate_range("2025-01-01", periods=63)
    growth = pd.DataFrame({"asset": np.linspace(100, 110, len(dates)), "benchmark": np.linspace(100, 105, len(dates))}, index=dates)
    growth_metrics, _ = metrics.calculate_metrics(growth, "asset", "benchmark")
    observed_cagr = float(growth_metrics["CAGR (Asset)"].rstrip("%"))
    assert abs(observed_cagr - 10) < 1e-8

    source = ROOT / "backend/api/ai_services.py"
    tree = ast.parse(source.read_text(encoding="utf-8-sig"))
    loss_node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_directional_penalty_loss")
    namespace = {"torch": torch}
    exec(compile(ast.Module(body=[loss_node], type_ignores=[]), str(source), "exec"), namespace)
    pred = torch.tensor([0.1], requires_grad=True)
    target = torch.tensor([-0.2])
    mse = torch.mean((pred - target) ** 2)
    mse_gradient = float(torch.autograd.grad(mse, pred)[0])
    loss = namespace["_directional_penalty_loss"](pred, target)
    penalty_gradient = float(torch.autograd.grad(loss, pred)[0])
    assert abs(mse_gradient - penalty_gradient) < 1e-8
    assert float(loss.detach() - mse.detach()) > 0

    design = (ROOT / "docs/rebrand/04-design-system.md").read_text(encoding="utf-8")
    tokens = {name: (light, dark) for name, light, dark in re.findall(r"\| `([^`]+)` \| `(#[0-9A-Fa-f]{6})` \| `(#[0-9A-Fa-f]{6})`", design)}
    themes = {}
    names = {"text": "text", "secondary": "text-secondary", "accent": "accent", "positive": "positive", "negative": "negative", "warning": "warning", "control": "border-control", "observed": "observed-series", "forecast": "forecast-series", "on_action": "on-action", "action_fill": "action-fill"}
    for column, theme in enumerate(("light", "dark")):
        themes[theme] = {name: tokens[token][column] for name, token in names.items()}
        themes[theme]["backgrounds"] = [tokens[name][column] for name in ("canvas", "surface", "surface-raised")]
    contrast_rows = []
    for theme, palette in themes.items():
        for token in ("text", "secondary", "accent", "positive", "negative", "warning", "control", "observed", "forecast"):
            minimum = min(contrast(palette[token], background) for background in palette["backgrounds"])
            threshold = 3 if token in ("control", "observed", "forecast") else 4.5
            assert minimum >= threshold, (theme, token, minimum)
            contrast_rows.append({"theme": theme, "token": token, "minimum_ratio": round(minimum, 3), "threshold": threshold})
        action_ratio = contrast(palette["on_action"], palette["action_fill"])
        assert action_ratio >= 4.5
        contrast_rows.append({"theme": theme, "token": "on-action against action-fill", "minimum_ratio": round(action_ratio, 3), "threshold": 4.5})

    return {
        "scope": "Offline source parse, three BSM properties, current defect reproductions, and proposed token contrast. This is not the Django suite or model validation.",
        "python": sys.version,
        "packages": {name: importlib.metadata.version(name) for name in ("numpy", "pandas", "scipy", "torch")},
        "python_files_attempted": len(files),
        "python_files_parsed": len(files) - len(parse_errors),
        "syntax_errors": parse_errors,
        "bsm": {"parity_absolute_error": parity_error, "iv_recovered": iv, "analytic_delta": delta, "finite_difference_delta": delta_fd, "result": "PASS for these fixtures only"},
        "defect_reproductions": {
            "initial_capital_drawdown": {"reported_pct": observed_drawdown, "expected_pct": -10, "result": "DEFECT REPRODUCED"},
            "short_period_cagr": {"calendar_days": (dates[-1] - dates[0]).days, "reported_pct": observed_cagr, "annualized_formula_pct": ((1.1 ** (365.25 / (dates[-1] - dates[0]).days)) - 1) * 100, "result": "CAGR LABEL/CONVENTION DEFECT REPRODUCED"},
            "directional_loss": {"mse_gradient": mse_gradient, "penalized_gradient": penalty_gradient, "result": "ZERO DIRECTIONAL GRADIENT CONTRIBUTION REPRODUCED"},
        },
        "token_contrast": contrast_rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, allow_nan=False))
