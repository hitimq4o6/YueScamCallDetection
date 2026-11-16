"""Lay out the Cantonese pilot for training_layer3.py.

Copies the 30 Common Voice yue WAV files into data/layer3_zh/train|val/bonafide.
Copies the 30 Qwen3-TTS Cantonese WAV files into the same tree's spoof folders.
The split follows split.json yue_pilot. The English data/layer3 tree is not touched.
"""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "layer3"
OUT = ROOT / "data" / "layer3_zh"
SPLIT = SRC / "split.json"
BONAFIDE_MANIFEST = SRC / "bonafide_manifest.csv"
SPOOF_MANIFEST = SRC / "spoof_manifest.csv"
VAL_RATIO = 0.2


def read_split() -> dict[str, str]:
    data = json.loads(SPLIT.read_text(encoding="utf-8"))
    files = data["yue_pilot"]["files"]
    return {Path(item["file"]).name: item["split"] for item in files}


def reset(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    split = read_split()
    bonafide = [Path(row["file"]).name for row in csv.DictReader(BONAFIDE_MANIFEST.open(encoding="utf-8"))]
    spoof = [row["file"] for row in csv.DictReader(SPOOF_MANIFEST.open(encoding="utf-8"))]
    for name in ("train", "val"):
        for cls in ("bonafide", "spoof"):
            reset(OUT / name / cls)
    counts = {"train": {"bonafide": 0, "spoof": 0}, "val": {"bonafide": 0, "spoof": 0}}
    for name in bonafide:
        target = split.get(name)
        if target is None:
            raise SystemExit(f"no split for bonafide {name}")
        shutil.copy2(SRC / "bonafide" / name, OUT / target / "bonafide" / name)
        counts[target]["bonafide"] += 1
    val_spoof = max(1, round(len(spoof) * VAL_RATIO))
    for index, name in enumerate(sorted(spoof)):
        target = "val" if index >= len(spoof) - val_spoof else "train"
        shutil.copy2(SRC / "spoof" / name, OUT / target / "spoof" / name)
        counts[target]["spoof"] += 1
    print("bonafide", counts["train"]["bonafide"], "train /", counts["val"]["bonafide"], "val")
    print("spoof", counts["train"]["spoof"], "train /", counts["val"]["spoof"], "val")
    print("tree:", OUT)


if __name__ == "__main__":
    main()
