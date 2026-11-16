"""Pick 30 Common Voice yue clips and write 16 kHz mono WAV files.

Reads the local MDC tar.gz. Does not download. Does not clone a voice.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import tarfile
import wave
from pathlib import Path

import av
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "layer3"
BONAFIDE_DIR = DATA / "bonafide"
EXTRACT_DIR = DATA / "_cv_extract"
MANIFEST = DATA / "bonafide_manifest.csv"
SPLIT_PATH = DATA / "split.json"
ARCHIVE = ROOT / "1789494296567-cv-corpus-27.0-2026-09-11-yue.tar.gz"
TAR_ROOT = "cv-corpus-27.0-2026-09-11/yue"
SOURCE = "Mozilla Data Collective Common Voice Scripted Speech 27.0 Cantonese"
LICENSE = "CC0-1.0"
DATASET_SLUG = "common-voice-scripted-speech-27-0-canton-14840b6e"
SEED = 42
LIMIT = 30
VAL_COUNT = 6
MIN_SEC = 3.0
MAX_SEC = 6.0


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def extract_tables(archive: Path, dest: Path) -> tuple[Path, Path]:
    dest.mkdir(parents=True, exist_ok=True)
    names = [f"{TAR_ROOT}/validated.tsv", f"{TAR_ROOT}/clip_durations.tsv"]
    with tarfile.open(archive, "r:gz") as tar:
        for name in names:
            member = tar.getmember(name)
            member.name = Path(name).name
            tar.extract(member, dest, filter="data")
    return dest / "validated.tsv", dest / "clip_durations.tsv"


def load_durations(path: Path) -> dict[str, float]:
    durations: dict[str, float] = {}
    for row in read_tsv(path):
        try:
            durations[row["clip"]] = int(row["duration[ms]"]) / 1000.0
        except (KeyError, ValueError):
            continue
    return durations


def eligible(rows: list[dict[str, str]], durations: dict[str, float]) -> list[dict[str, str]]:
    chosen = []
    for row in rows:
        name = row.get("path", "")
        seconds = durations.get(name)
        if seconds is None or seconds < MIN_SEC or seconds > MAX_SEC:
            continue
        try:
            up = int(row.get("up_votes") or 0)
            down = int(row.get("down_votes") or 0)
        except ValueError:
            continue
        if up < 2 or down != 0:
            continue
        row = dict(row)
        row["duration_sec"] = f"{seconds:.3f}"
        chosen.append(row)
    return chosen


def pick(rows: list[dict[str, str]], limit: int, seed: int) -> list[dict[str, str]]:
    groups: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        groups.setdefault(row["client_id"], []).append(row)
    rng = random.Random(seed)
    speakers = list(groups)
    rng.shuffle(speakers)
    picked = []
    for speaker in speakers:
        clips = groups[speaker]
        clips.sort(key=lambda item: abs(float(item["duration_sec"]) - 4.5))
        picked.append(clips[0])
        if len(picked) >= limit:
            break
    if len(picked) < limit:
        raise SystemExit(f"only {len(picked)} speakers in the 3-6 second window")
    return picked


def extract_clips(archive: Path, names: list[str], dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    wanted = {f"{TAR_ROOT}/clips/{name}": name for name in names}
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar:
            out_name = wanted.get(member.name)
            if not out_name:
                continue
            target = dest / out_name
            source = tar.extractfile(member)
            if source is None:
                raise SystemExit(f"missing audio stream for {member.name}")
            target.write_bytes(source.read())
            del wanted[member.name]
            if not wanted:
                break
    if wanted:
        missing = ", ".join(sorted(wanted.values())[:5])
        raise SystemExit(f"archive missing {len(wanted)} clips, including {missing}")


def to_wav(src: Path, dst: Path) -> float:
    container = av.open(str(src))
    stream = container.streams.audio[0]
    resampler = av.audio.resampler.AudioResampler(format="s16", layout="mono", rate=16000)
    chunks: list[np.ndarray] = []
    for frame in container.decode(stream):
        converted = resampler.resample(frame)
        if converted is None:
            continue
        if not isinstance(converted, list):
            converted = [converted]
        for item in converted:
            chunks.append(np.asarray(item.to_ndarray()))
    leftover = resampler.resample(None)
    if leftover is not None:
        if not isinstance(leftover, list):
            leftover = [leftover]
        for item in leftover:
            chunks.append(np.asarray(item.to_ndarray()))
    container.close()
    if not chunks:
        raise RuntimeError(f"no audio in {src}")
    audio = np.concatenate([chunk.reshape(-1) for chunk in chunks])
    dst.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(dst), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(audio.astype(np.int16).tobytes())
    return audio.size / 16000.0


def assign_split(rows: list[dict[str, str]], seed: int) -> None:
    rng = random.Random(seed)
    order = list(range(len(rows)))
    rng.shuffle(order)
    val_ids = {rows[index]["speaker_id"] for index in order[:VAL_COUNT]}
    for row in rows:
        row["split"] = "val" if row["speaker_id"] in val_ids else "train"


def write_manifest(rows: list[dict[str, str]]) -> None:
    fields = ["file", "source", "license", "duration_sec", "speaker_id", "note"]
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_split(rows: list[dict[str, str]]) -> None:
    existing = {}
    if SPLIT_PATH.is_file():
        existing = json.loads(SPLIT_PATH.read_text(encoding="utf-8"))
    existing["yue_pilot"] = {
        "source": SOURCE,
        "archive": ARCHIVE.name,
        "license": LICENSE,
        "dataset_slug": DATASET_SLUG,
        "page": "https://mozilladatacollective.com/datasets/cmu5x3i5w00d6o107yvwox9lg",
        "window_sec": [MIN_SEC, MAX_SEC],
        "seed": SEED,
        "rule": "one clip per client_id; 6 speakers held out for val",
        "note": "Read speech, not scam calls. Not mixed into the English train/val folders.",
        "counts": {
            "train": sum(1 for row in rows if row["split"] == "train"),
            "val": sum(1 for row in rows if row["split"] == "val"),
        },
        "val_speakers": sorted(row["speaker_id"] for row in rows if row["split"] == "val"),
        "files": [
            {"file": row["file"], "split": row["split"], "speaker_id": row["speaker_id"]}
            for row in rows
        ],
    }
    SPLIT_PATH.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=LIMIT)
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    args = parser.parse_args()
    if not args.archive.is_file():
        raise SystemExit(f"missing archive: {args.archive}")
    validated_path, duration_path = extract_tables(args.archive, EXTRACT_DIR)
    rows = pick(eligible(read_tsv(validated_path), load_durations(duration_path)), args.limit, SEED)
    clip_dir = EXTRACT_DIR / "clips"
    extract_clips(args.archive, [row["path"] for row in rows], clip_dir)
    BONAFIDE_DIR.mkdir(parents=True, exist_ok=True)
    for old in BONAFIDE_DIR.glob("cv_yue_*.wav"):
        old.unlink()
    written = []
    for index, row in enumerate(rows):
        src = clip_dir / row["path"]
        dest = BONAFIDE_DIR / f"cv_yue_{index:03d}.wav"
        seconds = to_wav(src, dest)
        if seconds < MIN_SEC or seconds > MAX_SEC:
            dest.unlink(missing_ok=True)
            raise SystemExit(f"{row['path']} measured {seconds:.3f}s, outside 3-6s")
        written.append(
            {
                "file": str(dest.relative_to(ROOT)),
                "source": SOURCE,
                "license": LICENSE,
                "duration_sec": f"{seconds:.3f}",
                "speaker_id": row["client_id"][:16],
                "split": "",
                "note": "pilot read speech; not a scam call; do not identify the speaker",
            }
        )
    assign_split(written, SEED)
    write_manifest(written)
    write_split(written)
    train = sum(1 for row in written if row["split"] == "train")
    val = sum(1 for row in written if row["split"] == "val")
    print(f"bonafide clips: {len(written)}")
    print(f"speakers: {len({row['speaker_id'] for row in written})}")
    print(f"split: train={train} val={val}")
    print(f"manifest: {MANIFEST}")


if __name__ == "__main__":
    main()
