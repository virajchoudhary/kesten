"""Check preserved PyTorch mechanics offline, without training or market data."""

import json
import os
from pathlib import Path
import socket
import sys


def deny_network(*args, **kwargs):
    raise RuntimeError("Network access is disabled for the legacy tensor check.")


def main():
    os.environ.update({
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "GROQ_API_KEY": "",
        "POLYGON_API_KEY": "",
        "CADRISYN_LEGACY_SCHEDULER_ENABLED": "false",
    })
    socket.socket.connect = deny_network
    socket.create_connection = deny_network
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

    import torch
    from api.ai_services import LSTMModel, _directional_penalty_loss

    torch.set_num_threads(1)
    torch.manual_seed(17)
    model = LSTMModel(hidden_size=8, num_layers=1, dropout=0)
    model.eval()
    inputs = torch.linspace(-1, 1, 24).reshape(2, 12, 1)
    targets = torch.tensor([[0.25], [-0.25]])
    output = model(inputs)
    assert output.shape == (2, 1)
    assert torch.isfinite(output).all()
    assert torch.equal(output, model(inputs))
    loss = _directional_penalty_loss(output, targets)
    assert torch.isfinite(loss)
    loss.backward()
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())

    predictions = torch.tensor([[0.5], [-0.5]], requires_grad=True)
    opposed_targets = torch.tensor([[-0.25], [0.25]])
    mse = ((predictions - opposed_targets) ** 2).mean()
    combined = _directional_penalty_loss(predictions, opposed_targets)
    mse_gradient = torch.autograd.grad(mse, predictions, retain_graph=True)[0]
    combined_gradient = torch.autograd.grad(combined, predictions)[0]
    penalty_gradient_is_zero = torch.equal(mse_gradient, combined_gradient)

    print(json.dumps({
        "runtime_smoke": "PASS",
        "torch": torch.__version__,
        "device": "cpu",
        "input_kind": "synthetic_tensor_only",
        "checks": ["forward_shape", "finite_output", "deterministic_eval", "finite_backward_gradients"],
        "directional_penalty_adds_gradient": not penalty_gradient_is_zero,
        "optimizer_steps": 0,
        "model_artifacts_written": False,
        "empirical_evaluation": False,
        "model_promotion": "NOT_QUALIFIED",
    }, indent=2))


if __name__ == "__main__":
    main()
