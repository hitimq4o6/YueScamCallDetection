"""Prepare a small Layer-3 pilot. Does not train a model.

Bonafide audio comes only from Mozilla Data Collective Common Voice yue (CC0).
Spoof audio is IndexTTS-2, and the reference clip must be one of those files.
If the key or the TTS checkout is missing, this script prints the command and stops.
It does not download unofficial mirrors and it does not invent clips.

  export MDC_API_KEY=...
  python scripts/prepare_layer3_pilot.py --bonafide-only

  export INDEXTTS_DIR=/path/to/index-tts
  python scripts/prepare_layer3_pilot.py --spoof-only
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "layer3"
BONAFIDE_DIR = DATA / "bonafide"
SPOOF_DIR = DATA / "spoof"
CACHE = DATA / "_mdc_cache"
PROMPTS = DATA / "spoof_prompts.csv"
BONAFIDE_MANIFEST = DATA / "bonafide_manifest.csv"
SPOOF_MANIFEST = DATA / "spoof_manifest.csv"

DATASET_ID = "cmu5x3i5w00d6o107yvwox9lg"
DATASET_SLUG = "common-voice-scripted-speech-27-0-canton-14840b6e"
SOURCE = "Mozilla Data Collective Common Voice Scripted Speech 27.0 Cantonese"
LICENSE = "CC0-1.0"
INDEXTTS_COMMIT = "d9e41aac89fd00b3d71497fddb287b7f24613712"
AUDIO_SUFFIXES = {".mp3", ".wav", ".flac", ".ogg", ".m4a"}
MIN_SEC = 1.5
MAX_SEC = 8.0
TARGET = 30

INSTALL_BLOCK = f"""
IndexTTS-2 is not ready. Install it, then rerun. Prefer the RTX 4080 Super.
This Mac has no CUDA. Do not use a reference clip from outside {BONAFIDE_DIR}.

git clone https://github.com/index-tts/index-tts.git vendor/index-tts
cd vendor/index-tts
git checkout {INDEXTTS_COMMIT}
pip install -U uv
uv sync --extra webui
uv tool install "huggingface-hub"
hf download IndexTeam/IndexTTS-2 --local-dir=checkpoints_2

export INDEXTTS_DIR=/absolute/path/to/index-tts
python scripts/prepare_layer3_pilot.py --spoof-only
""".strip()


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def duration_sec(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        rate = handle.getframerate()
        if rate <= 0:
            return 0.0
        return handle.getnframes() / float(rate)


def convert_to_16k(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        subprocess.run(
            [ffmpeg, "-y", "-i", str(src), "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(dst)],
            check=True,
            capture_output=True,
        )
        return
    import torchaudio

    wav, sample_rate = torchaudio.load(str(src))
    if wav.shape[0] > 1:
        wav = wav.mean(dim=0, keepdim=True)
    if sample_rate != 16000:
        wav = torchaudio.functional.resample(wav, sample_rate, 16000)
    torchaudio.save(str(dst), wav, 16000)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def metadata_index(root: Path) -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for table in sorted(root.rglob("*.tsv")) + sorted(root.rglob("*.csv")):
        delimiter = "\t" if table.suffix == ".tsv" else ","
        try:
            with table.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle, delimiter=delimiter))
        except UnicodeDecodeError:
            continue
        if not rows:
            continue
        key = next((name for name in ("path", "clip", "file", "audio") if name in rows[0]), "")
        if not key:
            continue
        for row in rows:
            name = Path(row.get(key, "")).name
            if name:
                index[name] = row
    return index


def speaker_of(row: dict[str, str], fallback: str) -> str:
    for key in ("client_id", "speaker_id", "speaker"):
        value = (row.get(key) or "").strip()
        if value:
            return value[:16]
    return fallback


def pick_round_robin(items: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
    groups: dict[str, list[dict[str, str]]] = {}
    for item in items:
        groups.setdefault(item["speaker_id"], []).append(item)
    chosen: list[dict[str, str]] = []
    cursors = {name: 0 for name in groups}
    while len(chosen) < limit:
        moved = False
        for name in sorted(groups):
            cursor = cursors[name]
            if cursor >= len(groups[name]):
                continue
            chosen.append(groups[name][cursor])
            cursors[name] = cursor + 1
            moved = True
            if len(chosen) >= limit:
                break
        if not moved:
            break
    return chosen


def find_audio(root: Path) -> list[Path]:
    files = [
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in AUDIO_SUFFIXES and "youtube" not in path.as_posix().lower()
    ]
    return sorted(files)


def prepare_bonafide(limit: int, full: bool) -> int:
    if not os.environ.get("MDC_API_KEY"):
        print("MDC_API_KEY is not set. No Common Voice file was downloaded.")
        print("1. Open https://mozilladatacollective.com/datasets/" + DATASET_ID)
        print("2. Accept the dataset terms. License on the catalog page is CC0-1.0.")
        print("3. Create an API key. Do not commit it.")
        print("4. pip install datacollective && brew install ffmpeg")
        print("5. export MDC_API_KEY=your-key")
        print("6. python scripts/prepare_layer3_pilot.py --bonafide-only")
        print("The full archive is about 6.4 GB. The default command uses the sample only.")
        return 2
    try:
        from datacollective import download_dataset, download_sample
    except ImportError:
        print("pip install datacollective")
        return 2
    CACHE.mkdir(parents=True, exist_ok=True)
    try:
        if full:
            extracted = download_dataset(DATASET_ID, download_directory=str(CACHE), extract=True)
        else:
            extracted = download_sample(DATASET_ID, download_directory=str(CACHE), extract=True)
    except PermissionError:
        print("MDC refused the download. Accept the dataset terms, then retry.")
        print("https://mozilladatacollective.com/datasets/" + DATASET_ID)
        return 2
    root = Path(extracted)
    audio = find_audio(root)
    if not audio:
        print(f"No audio under {root}. Nothing was written to {BONAFIDE_DIR}.")
        return 1
    meta = metadata_index(root)
    candidates = []
    for path in audio:
        row = meta.get(path.name, {})
        candidates.append({"src": str(path), "speaker_id": speaker_of(row, "unknown")})
    picked = pick_round_robin(candidates, max(limit * 4, limit))
    rows = []
    for item in picked:
        if len(rows) >= limit:
            break
        src = Path(item["src"])
        dest = BONAFIDE_DIR / f"cv_yue_{len(rows):03d}.wav"
        try:
            convert_to_16k(src, dest)
            seconds = duration_sec(dest)
        except (subprocess.CalledProcessError, OSError, RuntimeError) as exc:
            dest.unlink(missing_ok=True)
            print(f"skip {src.name}: {exc}")
            continue
        if seconds < MIN_SEC or seconds > MAX_SEC:
            dest.unlink(missing_ok=True)
            continue
        rows.append(
            {
                "file": str(dest.relative_to(ROOT)),
                "source": SOURCE,
                "license": LICENSE,
                "duration_sec": f"{seconds:.3f}",
                "speaker_id": item["speaker_id"],
                "note": f"pilot; dataset {DATASET_SLUG}; converted to 16 kHz mono; not a scam-call recording",
            }
        )
    write_rows(
        BONAFIDE_MANIFEST,
        ["file", "source", "license", "duration_sec", "speaker_id", "note"],
        rows,
    )
    print(f"bonafide clips: {len(rows)}")
    print(f"manifest: {BONAFIDE_MANIFEST}")
    if len(rows) < 20 and not full:
        print("Fewer than 20 clips. The MDC sample is small. Optional full archive:")
        print("python scripts/prepare_layer3_pilot.py --bonafide-only --full")
        return 2
    return 0 if rows else 1


def indextts_dirs() -> tuple[Path, Path] | None:
    raw = os.environ.get("INDEXTTS_DIR", "")
    candidates = [Path(raw)] if raw else []
    candidates.extend([ROOT / "vendor" / "index-tts", ROOT.parent / "index-tts"])
    for repo in candidates:
        if not repo.is_dir():
            continue
        ckpt = Path(os.environ.get("INDEXTTS_CKPT", "")) if os.environ.get("INDEXTTS_CKPT") else repo / "checkpoints_2"
        if not (ckpt / "config.yaml").is_file():
            alt = repo / "checkpoints"
            if (alt / "config.yaml").is_file():
                ckpt = alt
        if (ckpt / "config.yaml").is_file():
            return repo, ckpt
    return None


def prepare_spoof() -> int:
    if not list(BONAFIDE_DIR.glob("*.wav")):
        print(f"No WAV files in {BONAFIDE_DIR}. Run --bonafide-only first.")
        return 2
    if not PROMPTS.is_file():
        print(f"Missing {PROMPTS}")
        return 1
    located = indextts_dirs()
    if located is None:
        print(INSTALL_BLOCK)
        return 3
    repo, ckpt = located
    sys.path.insert(0, str(repo))
    try:
        from indextts.infer_v2 import IndexTTS2
    except ImportError:
        print(INSTALL_BLOCK)
        return 3
    refs = sorted(BONAFIDE_DIR.glob("*.wav"))
    allowed = {path.resolve() for path in refs}
    prompts = read_csv(PROMPTS)
    tts = IndexTTS2(
        cfg_path=str(ckpt / "config.yaml"),
        model_dir=str(ckpt),
        use_fp16=False,
        use_cuda_kernel=False,
        use_deepspeed=False,
    )
    params = "use_fp16=False;use_cuda_kernel=False;use_deepspeed=False;emo=none"
    rows = []
    for index, prompt in enumerate(prompts):
        ref = refs[index % len(refs)].resolve()
        if ref not in allowed or not str(ref).startswith(str(BONAFIDE_DIR.resolve())):
            print(f"refused reference outside bonafide: {ref}")
            return 1
        dest = SPOOF_DIR / f"indextts2_{index:03d}.wav"
        text = prompt["text"]
        tts.infer(spk_audio_prompt=str(ref), text=text, output_path=str(dest), verbose=False)
        seconds = duration_sec(dest)
        rows.append(
            {
                "file": str(dest.relative_to(ROOT)),
                "generator": f"IndexTTS-2 commit {INDEXTTS_COMMIT}",
                "reference_file": str(ref.relative_to(ROOT)),
                "license_of_reference": LICENSE,
                "text": text,
                "duration_sec": f"{seconds:.3f}",
                "parameters": params,
                "note": "pilot spoof for offline detection only; not for phone calls; Cantonese quality not verified",
            }
        )
        print(f"spoof {index + 1}/{len(prompts)} {seconds:.2f}s")
    write_rows(
        SPOOF_MANIFEST,
        ["file", "generator", "reference_file", "license_of_reference", "text", "duration_sec", "parameters", "note"],
        rows,
    )
    print(f"spoof clips: {len(rows)}")
    print(f"manifest: {SPOOF_MANIFEST}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bonafide-only", action="store_true")
    parser.add_argument("--spoof-only", action="store_true")
    parser.add_argument("--full", action="store_true", help="download the 6.4 GB archive instead of the sample")
    parser.add_argument("--limit", type=int, default=TARGET)
    args = parser.parse_args()
    BONAFIDE_DIR.mkdir(parents=True, exist_ok=True)
    SPOOF_DIR.mkdir(parents=True, exist_ok=True)
    if args.bonafide_only and args.spoof_only:
        raise SystemExit("choose one of --bonafide-only or --spoof-only")
    if args.spoof_only:
        raise SystemExit(prepare_spoof())
    code = prepare_bonafide(args.limit, args.full)
    if code != 0 or args.bonafide_only:
        raise SystemExit(code)
    raise SystemExit(prepare_spoof())


if __name__ == "__main__":
    main()
