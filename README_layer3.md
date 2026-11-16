# Layer-3 small Mel-CNN

Offline training only. The phone runs inference of the exported model. A score is a warning, not a legal finding.

The network is the same 3-layer Mel-CNN as `training.py`. Audio is 16 kHz and about 3 seconds. Short clips are zero-padded. Long clips are cut. The window is padded to 304 Mel frames so the existing pool can export to ONNX. Input shape is `(1, 1, 64, 304)`.

## Data folders

```text
data/layer3/train/bonafide/
data/layer3/train/spoof/
data/layer3/val/bonafide/
data/layer3/val/spoof/
```

Accepted files: `.wav` `.mp3` `.flac` `.m4a` `.ogg`.

`bonafide` is label 0. `spoof` is label 1. Both classes are required in train and in val. If a folder is missing or empty, training stops and does not print an accuracy.

Use public, licensed audio only. Do not generate or clone a real person's voice. Do not scrape HKJunkCall. There is currently no licensed Cantonese scam-call audio in this project.

## Train

```bash
pip install -r requirements_layer3.txt
python training_layer3.py --epochs 15 --batch-size 16 --lr 0.001
```

The script picks CUDA, then MPS, then CPU. It saves the best validation checkpoint to `models/cnn_small.pt`. Printed loss, accuracy, and F1 come from that run only.

## Export

```bash
python export_onnx.py
```

This reads `models/cnn_small.pt` and writes `models/cnn_small.onnx`. It then runs one dummy ONNX Runtime check. That check is not an accuracy number. If the checkpoint is missing, nothing is exported.

TFLite INT8 is not produced by this step. The phone budget is about 5–10 MB. This CNN is smaller than that budget.
