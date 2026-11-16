"""Generate IndexTTS-2 spoof clips on the Windows training machine.

Reference audio must already be the Common Voice yue WAV files in refs/.
This does not download voices and does not call anyone.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
import wave
from pathlib import Path

ROOT = Path(r"C:\Users\user\Desktop\fyp\index-tts")
CKPT = ROOT / "checkpoints_2"
REFS = Path(r"C:\layer3\refs")
PROMPTS = Path(r"C:\layer3\spoof_prompts.csv")
OUT = Path(r"C:\layer3\spoof")
MANIFEST = Path(r"C:\layer3\spoof_manifest.csv")
COMMIT = "d9e41aac89fd00b3d71497fddb287b7f24613712"
PARAMS = "use_fp16=False;use_cuda_kernel=False;use_deepspeed=False;use_qwen_emo=False;emo=none"


def duration_sec(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        rate = handle.getframerate()
        if rate <= 0:
            return 0.0
        return handle.getnframes() / float(rate)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    from indextts.infer_v2 import IndexTTS2

    refs = sorted(REFS.glob("cv_yue_*.wav"))
    if not refs:
        raise SystemExit(f"no reference wav files in {REFS}")
    with PROMPTS.open(newline="", encoding="utf-8") as handle:
        prompts = list(csv.DictReader(handle))
    prompts = prompts[: args.limit]
    OUT.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    tts = IndexTTS2(
        cfg_path=str(CKPT / "config.yaml"),
        model_dir=str(CKPT),
        use_fp16=False,
        use_cuda_kernel=False,
        use_deepspeed=False,
        use_qwen_emo=False,
    )
    rows = []
    for index, prompt in enumerate(prompts):
        ref = refs[index % len(refs)].resolve()
        if REFS.resolve() not in ref.parents:
            raise SystemExit(f"refused reference outside {REFS}: {ref}")
        dest = OUT / f"indextts2_{index:03d}.wav"
        text = prompt["text"]
        clip_started = time.perf_counter()
        tts.infer(spk_audio_prompt=str(ref), text=text, output_path=str(dest), verbose=False)
        seconds = duration_sec(dest)
        rows.append(
            {
                "file": dest.name,
                "generator": f"IndexTTS-2 commit {COMMIT}",
                "reference_file": ref.name,
                "license_of_reference": "CC0-1.0",
                "text": text,
                "duration_sec": f"{seconds:.3f}",
                "parameters": PARAMS,
                "note": "pilot spoof for offline detection only; not for phone calls; Cantonese quality not verified",
            }
        )
        print(f"spoof {index + 1}/{len(prompts)} {seconds:.2f}s {time.perf_counter() - clip_started:.1f}s", flush=True)
    fields = [
        "file",
        "generator",
        "reference_file",
        "license_of_reference",
        "text",
        "duration_sec",
        "parameters",
        "note",
    ]
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"done {len(rows)} clips in {time.perf_counter() - started:.1f}s", flush=True)


if __name__ == "__main__":
    main()
