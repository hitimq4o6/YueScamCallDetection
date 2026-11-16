"""Lay out garystafford/deepfake-audio-detection for training_layer3.py.

Public CC-BY-4.0 set. English YouTube speech and TTS. Not Cantonese.
Not a Hong Kong evaluation. Does not generate or clone voices.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "layer3"
SOURCE_DIR = ROOT / "data" / "hf" / "garystafford-deepfake-audio-detection"
REPO_ID = "garystafford/deepfake-audio-detection"
SEED = 42
VAL_TARGET = 0.2


def source_id(name: str) -> str:
    return "_".join(name.split("_")[:2])


def grouped(folder: Path) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = {}
    for path in sorted(folder.glob("*.flac")):
        groups.setdefault(source_id(path.name), []).append(path)
    return groups


def hold_out(groups: dict[str, list[Path]], rng: random.Random) -> set[str]:
    names = list(groups)
    rng.shuffle(names)
    total = sum(len(paths) for paths in groups.values())
    target = max(1, int(total * VAL_TARGET))
    chosen: list[str] = []
    count = 0
    for name in names:
        if chosen and count >= target:
            break
        if len(chosen) == len(names) - 1:
            break
        chosen.append(name)
        count += len(groups[name])
    return set(chosen)


def link_split(groups: dict[str, list[Path]], held: set[str], class_name: str) -> dict[str, int]:
    counts = {"train": 0, "val": 0}
    for name, paths in groups.items():
        split = "val" if name in held else "train"
        dest_dir = DATA_DIR / split / class_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        for path in paths:
            dest = dest_dir / path.name
            if dest.is_symlink() or dest.exists():
                dest.unlink()
            dest.symlink_to(path.resolve())
            counts[split] += 1
    return counts


def main() -> None:
    snapshot_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        allow_patterns=["real/*.flac", "fake/*.flac"],
        local_dir=SOURCE_DIR,
    )
    rng = random.Random(SEED)
    real_groups = grouped(SOURCE_DIR / "real")
    fake_groups = grouped(SOURCE_DIR / "fake")
    if not real_groups or not fake_groups:
        raise SystemExit(f"missing flac files under {SOURCE_DIR}")
    real_held = hold_out(real_groups, rng)
    fake_held: set[str] = set()
    prefixes = sorted({name.split("_")[0] for name in fake_groups})
    for prefix in prefixes:
        subset = {name: paths for name, paths in fake_groups.items() if name.startswith(prefix + "_")}
        fake_held.update(hold_out(subset, rng))
    for class_name in ("bonafide", "spoof"):
        for split in ("train", "val"):
            folder = DATA_DIR / split / class_name
            folder.mkdir(parents=True, exist_ok=True)
            for path in folder.glob("*"):
                if path.is_symlink():
                    path.unlink()
    real_counts = link_split(real_groups, real_held, "bonafide")
    fake_counts = link_split(fake_groups, fake_held, "spoof")
    manifest = {
        "repo": REPO_ID,
        "url": "https://huggingface.co/datasets/garystafford/deepfake-audio-detection",
        "license": "CC-BY-4.0",
        "language": "en",
        "note": "English YouTube speech versus TTS. Not Cantonese. Not a Hong Kong accuracy set. No new voices were generated.",
        "split": "whole source id held out; clips from one YouTube video or one TTS job stay in one split",
        "seed": SEED,
        "real_val_sources": sorted(real_held),
        "fake_val_sources": sorted(fake_held),
        "counts": {
            "train_bonafide": real_counts["train"],
            "val_bonafide": real_counts["val"],
            "train_spoof": fake_counts["train"],
            "val_spoof": fake_counts["val"],
        },
    }
    (DATA_DIR / "split.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest["counts"], ensure_ascii=False))
    print("real val sources:", ", ".join(sorted(real_held)))
    print("fake val sources:", len(fake_held))


if __name__ == "__main__":
    main()
