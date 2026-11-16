# Layer-3 pilot sources

Prepared 2026-11-16. This is a pilot set plan, not a full Cantonese scam-call dataset. No accuracy number belongs to this file. Scores later are warnings, not legal findings.

## Status on 2026-11-16

- The user placed the bonafide recording archive on disk at 15:35. It is not extracted into `data/layer3/bonafide/` yet.
- No spoof clip was generated. IndexTTS-2 is still not installed.
- `bonafide_manifest.csv` and `spoof_manifest.csv` still have headers only.
- `data/layer3/train/` and `data/layer3/val/` are the older English YouTube-versus-TTS set from 2026-11-03. Do not mix that set into this pilot. Do not call either set a Hong Kong accuracy.

## Why the clips are not here

Common Voice is no longer on Hugging Face. The `mozilla-foundation/common_voice_17_0` page was empty on 2026-11-16. Mozilla says community datasets, including Common Voice, are only on Mozilla Data Collective, so a person who withdraws consent can be removed. Third-party mirrors were not used. YouTube and social-media audio were not used.

The catalog entry checked without a download key:

- Name: Common Voice Scripted Speech 27.0 - Cantonese
- Locale: `yue`
- License: CC0-1.0
- Format: MP3
- Size: 6433594094 bytes (about 6.4 GB). This is the full archive, not the pilot.
- Dataset id: `cmu5x3i5w00d6o107yvwox9lg`
- Slug: `common-voice-scripted-speech-27-0-canton-14840b6e`
- Filename: `common-voice-scripted-speech-27-0-canton-14840b6e.tar.gz`
- Checksum: `ba060ea5326a43467741a826602518b833a0dea76068f9e40b9f0cc730364bfc`
- Listed createdAt: 2026-09-17T19:23:21.908Z
- Page: https://mozilladatacollective.com/datasets/cmu5x3i5w00d6o107yvwox9lg
- Organization: Mozilla Common Voice

## Local recording archive (user, 2026-11-16)

The user said this tar.gz is the recording set for https://mozilladatacollective.com/datasets/cmu5x3i5w00d6o107yvwox9lg

- Project copy: `1789494296567-cv-corpus-27.0-2026-09-11-yue.tar.gz` (program root)
- Download copy: `/Users/wongsiulun/Downloads/1789494296567-cv-corpus-27.0-2026-09-11-yue.tar.gz`
- Size of both: 6433594094 bytes. This matches the catalog `sizeBytes`. They are two copies, not one hard link.
- Catalog checksum was not recomputed on the local file in this note. Size match is not a checksum match.
- Archive listing starts with `cv-corpus-27.0-2026-09-11/yue/` and `clips/common_voice_yue_*.mp3`, plus `validated.tsv`. These are read-speech recordings, not scam calls.
- Inner README says: cv-corpus-27.0-2026-09-11, Cantonese `yue`, 279396 clips, 307.44 hours recorded, 210.78 hours validated, 1188 speakers, 28727 sentences.
- Inner README licence line: Creative Commons Zero (CC-0). It also says downloading means you agree not to determine the identity of speakers. Do not try to identify a speaker. A hashed `client_id` in a manifest is not an identity.
- Not a Hong Kong scam-call corpus. Not extracted into the pilot WAV folder yet.

## IndexTTS-2

Not installed on 2026-11-16. `uv` was not on this Mac. No checkpoint was downloaded. No voice was cloned.

Pinned upstream commit to use when the user installs it: `d9e41aac89fd00b3d71497fddb287b7f24613712` (GitHub `index-tts/index-tts` main, commit date 2026-09-29). That pin is a code revision, not proof that inference ran.

Model weights: `IndexTeam/IndexTTS-2` on Hugging Face, saved as `checkpoints_2`. License on the GitHub repo is the bilibili Model Use License. Read `LICENSE` and `DISCLAIMER` before sharing any generated file. This note does not claim the license allows republication.

Known limit: IndexTTS-2 is built mainly for Mandarin and English. Cantonese text may come out as Mandarin-like speech. Listen before any training run. Do not write a Cantonese accuracy from these clips until that check is done.

Reference audio, when generation runs, must come only from `data/layer3/bonafide/`. Those clips must be the CC0 Common Voice yue subset. Do not point the model at YouTube, social media, or a private person's recording.

Generated files are spoof labels for offline detector tests only. They are not for phone calls.

## What to run

1. Create an MDC account, open the Cantonese 27.0 page above, and accept that dataset's terms.
2. Create an API key and export it in the shell. Do not commit the key.

```bash
pip install datacollective
brew install ffmpeg
export MDC_API_KEY=your-key
python scripts/prepare_layer3_pilot.py --bonafide-only
```

Expected bonafide output: up to 30 files in `data/layer3/bonafide/`, 16 kHz mono WAV, plus one row each in `bonafide_manifest.csv`. The script uses the MDC sample first, not the 6.4 GB archive. If the sample has fewer than 20 clips, it stops and says so. `--full` downloads the 6.4 GB archive and is optional.

3. Install IndexTTS-2 on the RTX 4080 Super if this Mac cannot run it. This Mac is Apple Silicon, 24 GB, and has no CUDA. The official install path expects `uv` and is aimed at NVIDIA GPUs.

```bash
git clone https://github.com/index-tts/index-tts.git vendor/index-tts
cd vendor/index-tts
git checkout d9e41aac89fd00b3d71497fddb287b7f24613712
pip install -U uv
uv sync --extra webui
uv tool install "huggingface-hub"
hf download IndexTeam/IndexTTS-2 --local-dir=checkpoints_2
```

4. Generate spoof clips only after bonafide WAV files exist.

```bash
export INDEXTTS_DIR=/absolute/path/to/index-tts
python scripts/prepare_layer3_pilot.py --spoof-only
```

Expected spoof output: one WAV per row in `data/layer3/spoof_prompts.csv`, about 3–6 seconds if the model follows the short text, saved under `data/layer3/spoof/`, plus `spoof_manifest.csv`. Parameters written by the script: `use_fp16=False`, `use_cuda_kernel=False`, `use_deepspeed=False`, no emotion control. If import fails, the script prints this same install block and stops. It does not invent clips.

## Confirmations

- No YouTube or unlicensed audio was used.
- The only local speech archive noted here is the Common Voice yue tar.gz above. It was not unpacked into reference clips on this pass.
- No real person's voice was cloned.
