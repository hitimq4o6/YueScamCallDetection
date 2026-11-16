"""Generate Cantonese spoof clips with the hk-cantonese Qwen3-TTS voice.

Two baked CC0 voices are used so the set is not one timbre.
No reference clip is read here and no contributor is cloned at runtime.
"""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

MODEL = Path(r"C:\layer3\tts\hk-cantonese")
PROMPTS = Path(r"C:\layer3\spoof_prompts.csv")
NEUTRAL = Path(r"C:\layer3\neutral_prompts.csv")
OUT = Path(r"C:\layer3\spoof")
MANIFEST = Path(r"C:\layer3\spoof_manifest.csv")
SPEAKERS = ["hk_voice_343", "hk_voice_777"]
GENERATOR = "jmtl/hk-cantonese-cc0-qwen3-tts v0.0.5 over Qwen/Qwen3-TTS-12Hz-1.7B-Base"
PARAMS = "language=chinese;speaker=alternating;dtype=bfloat16;sampling=default;chunk<=45"
LICENSE = "Apache-2.0; adapter trained on CC0-1.0 Common Voice yue"
NOTE = (
    "synthetic Hong Kong Cantonese; for offline detection tests only; "
    "not for phone calls; baked CC0 contributor voices; do not impersonate"
)
MAX_CHUNK = 45
FIELDS = [
    "file",
    "generator",
    "reference_file",
    "license_of_reference",
    "text",
    "duration_sec",
    "parameters",
    "note",
    "kind",
]


def split_chunks(text: str) -> list[str]:
    parts: list[str] = []
    buffer = ""
    for char in text:
        buffer += char
        if char in "，。、！？；：,.!?;:" or len(buffer) >= MAX_CHUNK:
            if buffer.strip():
                parts.append(buffer.strip())
            buffer = ""
    if buffer.strip():
        parts.append(buffer.strip())
    return parts


def read_prompts(path: Path, kind: str) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["kind"] = kind
    return rows


def build_plan(total: int) -> list[dict[str, str]]:
    scam = read_prompts(PROMPTS, "scam_style")
    neutral = read_prompts(NEUTRAL, "neutral")
    scam_take = total - min(len(neutral), total // 2)
    plan = scam[:scam_take] + neutral[: total - scam_take]
    if len(plan) < total:
        raise SystemExit(f"only {len(plan)} prompts for {total} clips")
    return plan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--total", type=int, default=30)
    parser.add_argument("--start", type=int, default=0)
    args = parser.parse_args()
    import numpy as np
    import soundfile as sf
    import torch
    from qwen_tts import Qwen3TTSModel

    plan = build_plan(args.total)
    model = Qwen3TTSModel.from_pretrained(
        str(MODEL),
        dtype=torch.bfloat16,
        device_map="cuda",
        attn_implementation="sdpa",
    )
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for index in range(args.start, len(plan)):
        prompt = plan[index]
        speaker = SPEAKERS[index % len(SPEAKERS)]
        dest = OUT / f"qwentts_{index:03d}.wav"
        if dest.exists():
            print(f"skip {dest.name}", flush=True)
            continue
        audio_parts = []
        rate = 24000
        started = time.perf_counter()
        for chunk in split_chunks(prompt["text"]):
            wavs, rate = model.generate_custom_voice(
                text=[chunk], speaker=[speaker], language=["chinese"]
            )
            audio_parts.append(np.asarray(wavs[0], dtype=np.float32).reshape(-1))
        audio = np.concatenate(audio_parts) if len(audio_parts) > 1 else audio_parts[0]
        sf.write(str(dest), audio, rate)
        seconds = len(audio) / float(rate)
        rows.append(
            {
                "file": dest.name,
                "generator": GENERATOR,
                "reference_file": "baked_voice:" + speaker,
                "license_of_reference": LICENSE,
                "text": prompt["text"],
                "duration_sec": f"{seconds:.3f}",
                "parameters": PARAMS,
                "note": NOTE,
                "kind": prompt["kind"],
            }
        )
        print(
            f"{index + 1}/{len(plan)} {dest.name} {speaker} {prompt['kind']} {seconds:.2f}s {time.perf_counter() - started:.1f}s",
            flush=True,
        )
    if args.start == 0:
        with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
    else:
        existing = []
        if MANIFEST.is_file():
            with MANIFEST.open(newline="", encoding="utf-8") as handle:
                existing = list(csv.DictReader(handle))
        with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(existing + rows)
    print(f"done {len(rows)} clips", flush=True)


if __name__ == "__main__":
    main()
