# Layer-3 Data Preparation Prompt (for OpenCode / Agent)

You are helping with a Final Year Project (FYP) on an elderly scam-call detection app for Hong Kong.
The goal of this task is to prepare a small, clean, and well-documented dataset for later Layer-3 (Mel-CNN) experiments.

## Hard Constraints (must follow)

- Do **not** clone any real person's voice without explicit consent.
- Do **not** download or use YouTube / social-media audio.
- Do **not** scrape or republish third-party voices.
- All generated audio is **spoof only**. Real human speech comes only from open datasets.
- Keep a clear record of every source, license, and generation step.
- Scores and models later must remain advisory only.

## Target Combination

- **bonafide** (real human speech): Common Voice Cantonese (`yue`), license **CC0**.
- **spoof** (synthetic): IndexTTS2 (or IndexTTS-2), using short reference clips taken only from Common Voice yue.

## Tasks

### 1. Prepare bonafide data

- Download or prepare a small subset of Common Voice `yue` (CC0).
- Prefer validated clips.
- Convert to 16 kHz mono WAV if needed.
- Put files under:
  ```
  data/layer3/bonafide/
  ```
- Create a manifest: `data/layer3/bonafide_manifest.csv` with columns:
  `file, source, license, duration_sec, speaker_id (if available), note`

### 2. Prepare spoof data with IndexTTS2

- Use IndexTTS2 (official or documented local setup).
- Reference audio must come **only** from the Common Voice yue clips prepared above (or other CC0 Cantonese speech).
- Generate Cantonese sentences related to common scam-style phrases (official impersonation, bank, urgency, money transfer, secrecy).
- Keep generation short (about 3–6 seconds per clip is enough for later Mel-CNN experiments).
- Save outputs under:
  ```
  data/layer3/spoof/
  ```
- Create a manifest: `data/layer3/spoof_manifest.csv` with columns:
  `file, generator, reference_file, license_of_reference, text, duration_sec, parameters, note`

### 3. Record keeping (required)

Create / update a file:

```
data/layer3/sources.md
```

It must record:

- Date of preparation
- Common Voice version / download date / license (CC0)
- IndexTTS2 version / commit / how it was run
- Confirmation that no YouTube or unlicensed audio was used
- Confirmation that reference voices came only from open CC0 data
- Any known limitation (e.g. IndexTTS2 is stronger on Mandarin than Cantonese)

Also append a short entry to the project log (if `PROJECT_LOG` or similar exists) stating that Layer-3 pilot data was prepared with this combination.

### 4. Minimal folder layout expected

```
data/layer3/
  bonafide/           # Common Voice yue clips
  spoof/              # IndexTTS2 outputs
  bonafide_manifest.csv
  spoof_manifest.csv
  sources.md
```

### 5. Optional but useful

- A tiny script `scripts/prepare_layer3_pilot.py` that:
  - lists the bonafide files
  - calls IndexTTS2 (or documents the exact command if the model must be run manually)
  - writes the two manifests
  - prints a short summary

## Output style

- Prefer clear, reproducible steps.
- If IndexTTS2 cannot be installed automatically, write the exact commands and the expected input/output, then stop and tell the user what to run.
- Do not invent accuracy numbers.
- Do not claim this is a full Cantonese scam-call dataset; label it as a **pilot set**.

Start by checking what already exists under `data/` and then proceed with the smallest working pilot (e.g. 20–50 bonafide + 20–50 spoof clips).
