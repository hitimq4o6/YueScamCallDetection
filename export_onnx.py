"""Export the trained Layer-3 Mel-CNN to ONNX and run one dummy check. No accuracy is invented."""

from __future__ import annotations

from pathlib import Path

import torch

from training_layer3 import SAVE_PATH, SmallCNN, input_shape

ONNX_PATH = Path(__file__).resolve().parent / "models" / "cnn_small.onnx"


def load_model(path: Path) -> tuple[SmallCNN, tuple[int, int, int, int]]:
    try:
        checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        checkpoint = torch.load(path, map_location="cpu")
    model = SmallCNN()
    model.load_state_dict(checkpoint["model"])
    model.eval()
    shape = tuple(int(value) for value in checkpoint.get("input_shape", input_shape()))
    if len(shape) != 4 or shape[0] != 1 or shape[1] != 1:
        raise SystemExit(f"unsupported input_shape {shape}; expected (1, 1, n_mels, time)")
    return model, shape


def export_and_check(model: SmallCNN, shape: tuple[int, int, int, int], path: Path) -> None:
    try:
        import onnxruntime as ort
    except ImportError as exc:
        raise SystemExit("missing onnxruntime. Install with: pip install -r requirements_layer3.txt") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    dummy = torch.zeros(*shape)
    model.eval()
    with torch.no_grad():
        torch_out = model(dummy)
    torch.onnx.export(
        model,
        dummy,
        path,
        dynamo=False,
        input_names=["mel"],
        output_names=["logits"],
        opset_version=17,
    )
    session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    ort_out = session.run(None, {"mel": dummy.numpy()})[0]
    gap = float(torch.max(torch.abs(torch_out - torch.from_numpy(ort_out))).item())
    size_mb = path.stat().st_size / (1024 * 1024)
    print(f"exported: {path}")
    print(f"input_shape={shape}  output_shape={tuple(ort_out.shape)}  max_abs_diff={gap:.6f}  size_mb={size_mb:.3f}")
    print("Dummy check only. This is not an accuracy number and not a legal finding.")
    if gap > 1e-4:
        raise SystemExit("ONNX dummy output does not match PyTorch")


def main() -> None:
    if not SAVE_PATH.is_file():
        raise SystemExit(
            f"missing {SAVE_PATH}. Train first: python training_layer3.py\n"
            "No ONNX file was written. No accuracy is reported."
        )
    model, shape = load_model(SAVE_PATH)
    export_and_check(model, shape, ONNX_PATH)


if __name__ == "__main__":
    main()
