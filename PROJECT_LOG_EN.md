# PROJECT_LOG_EN

Last updated: 2026-11-16

This file is the English copy of `PROJECT_LOG.md`.
Update both files after a big task.
A big task is a week deliverable, a new layer, a new module, or a user milestone.
Skip tiny edits.
If it is not in this log, it is not done.
Do not call unchecked data verified.

## Now

- Layer-2 first version can run.
- It can check `cantonese_concept_hit_test.csv`.
- Layer-3 has one English training run and an ONNX file.
- That number is not a Hong Kong accuracy.
- Next is still licensed Cantonese audio.
- On 2026-11-16 the user placed the Cantonese recording archive in the project root.
- It is not unpacked into `data/layer3/bonafide/` yet.
- No voice was cloned.
- The phone only runs inference.
- Training stays offline.
- Layer-2 is not a Cantonese test.
- Layer-2 is not a handbook test.

## Done

- Three Layer-1 lists exist. On 2026-10-25 the user said they are good enough for now:
  - `data/layer1/official_whitelist.csv`
  - `data/layer1/scam_keywords_zh.csv` and `data/layer1/scam_keywords_en.csv`
  - `data/layer1/number_rules.csv`
- `data/layer1/seed_blacklist.csv` is empty on purpose.
- Do not use community blacklists.
- Do not scrape HKJunkCall.
- `data/layer1/sources.md` records sources and limits.
- `layer1_score.py` scores concept groups.
- One concept cannot be high risk.
- A whitelist number cuts the score.
- On 2026-10-25, 13 built-in tests passed.
- `api.py` has `GET /health` and `POST /score`.
- The API returns Layer-1 plus `layer2_score`, `layer2_risk`, and `layer2_proba`.
- Scores are warnings, not legal findings.
- `training.py` is only a Mel-CNN skeleton. It is not trained. It is not exported.
- Layer-2 (2026-10-25):
  - `train_layer2.py` trains offline.
  - Features are Layer-1 concept slots, not a large model.
  - `layer2_score.py` is a dot product. The phone does not need sklearn.
  - `models/layer2_linear.json` is about 910 bytes.
  - `models/layer2_eval.json` holds the English test numbers.
  - One concept cannot reach high risk.
  - Whitelist numbers still cut the score.
  - The shown score passes these gates.
  - `proba` is the raw model probability.
  - On 2026-11-03, `python layer2_score.py cantonese_concept_hit_test.csv` can run a concept-hit check.
  - 29 rows. Concepts 17/29. Display 17/29. Both 12/29.
  - `URGENCY` is not in the lexicon.
  - This is not a Hong Kong accuracy number.
- Layer-3 (2026-11-03):
  - `training_layer3.py` uses the same 3-layer Mel-CNN as `training.py`.
  - Audio is 16 kHz, about 3 seconds, 64 Mel bins.
  - Empty folders stop the run. No accuracy is printed.
  - `export_onnx.py` reads `models/cnn_small.pt` and writes `models/cnn_small.onnx`.
  - Fixed input is `(1, 1, 64, 304)`.
  - On 2026-11-03 the trainer used `garystafford/deepfake-audio-detection`.
  - License is CC-BY-4.0. Language is English. Real clips are YouTube speech. Fake clips are TTS.
  - No new voice was generated or cloned.
  - Split keeps one YouTube video or one TTS job on one side only.
  - Val real sources are `yt_0008` and `yt_0012`.
  - Train: bonafide 672, spoof 706. Val: bonafide 261, spoof 227.
  - 15 epochs on MPS. lr 0.001. batch 16.
  - Best val is epoch 6: val_acc 0.9590, val_f1_spoof 0.9576.
  - Epoch 15 fell to val_acc 0.6619. The saved checkpoint is the best epoch, not the last epoch.
  - `models/cnn_small.pt` exists. `models/cnn_small.onnx` is 0.342 MB.
  - The ONNX dummy gap was 0.000002. That gap is not accuracy.
  - This is not Cantonese. This is not a Hong Kong scam-call accuracy. TFLite INT8 is not done.
- Layer-3 pilot prep (2026-11-16):
  - `scripts/prepare_layer3_pilot.py` downloads only after `MDC_API_KEY` is set.
  - It converts clips to 16 kHz mono WAV.
  - If IndexTTS-2 is missing, it prints the install commands and stops.
  - It does not use YouTube. It does not use a third-party mirror.
  - `data/layer3/sources.md` records the catalog id and the empty download.
  - `data/layer3/spoof_prompts.csv` has 30 short pilot lines. They are not handbook-checked.
  - Both manifests have headers only. Clip count is 0.
  - Catalog page: Common Voice Scripted Speech 27.0 Cantonese. Id `cmu5x3i5w00d6o107yvwox9lg`. Locale `yue`. Catalog license CC0-1.0. Full archive is about 6.4 GB.
  - On 2026-11-16 the user said `1789494296567-cv-corpus-27.0-2026-09-11-yue.tar.gz` is the recording set for that page.
  - A second copy is in Downloads. Both are 6433594094 bytes. That matches the catalog size. SHA256 was not recomputed. Do not call the checksum checked.
  - The archive holds `common_voice_yue_*.mp3` plus `validated.tsv`. The inner README says CC-0 and says do not identify speakers.
  - These are read-speech clips, not scam calls.

## Layer-2 numbers (do not change these)

- Train file: `kaggle_data/archive (1)/composite_train.csv`, 36751 rows. C=1.0.
- Test file: `composite_test.csv`, 9188 rows. Almost all English.
- Threshold is 0.35.
- The threshold was picked on a train split, not on the test set.
- Test scam rate is 0.5652.
- Always guessing scam gets accuracy 0.5652.
- Test accuracy 0.7719. Precision 0.9485. Recall 0.6307. F1 0.7576.
- Only 0.3513 of test rows hit a concept.
- Only 0.5704 of scam rows hit a concept.
- If a row hits no concept, this model cannot see it.
- Check: `請致電18222或999查詢` is low (proba 0.287).
- Check: `我是公安，請把錢轉入安全帳戶並立即轉帳` is high (proba 0.982).
- Check: `銀行` shows low, but raw proba is 0.914. The one-concept gate holds it down.

## Provisional decisions

- On 2026-10-25 the user said the three lists are good enough.
- Weeks 1–4 can move on. Layer-2 was started.
- This is not ADCC, Police, or OFCA verification.
- The report must say handbook phrases and some hotlines are not checked against primary sources.
- These numbers were not confirmed on the ADCC pages checked: 34236611, 81056060, +852-1868.
- 18222, `#ADCC18222`, and 999 are marked checked in `sources.md`.
- Layer-2 was trained on English composite text.
- Cantonese, Mandarin, and English share concept slots.
- Do not call the numbers above a Hong Kong accuracy until there are Cantonese labels.
- On 2026-11-16: real Cantonese audio comes only from MDC Common Voice yue.
- The Hugging Face Common Voice 17.0 page was empty. Do not use an old mirror. A person may have withdrawn consent.
- Do not generate spoof audio before those CC0 clips exist.
- A reference clip must stay inside `data/layer3/bonafide/`.
- IndexTTS-2 may not speak Cantonese well. Listen first. Do not call that a Cantonese accuracy.
- Do not mix the English `train/` and `val/` folders into this pilot.
- On 2026-11-16 the local folder was linked to the private repo `hitimq4o6/YueScamCallDetection`.
- These stay off git: the Cantonese tar.gz, `kaggle_data/`, `data/hf/`, `.venv/`, and the local symlinks in `data/layer3/train/` and `val/`.

## Not done

- Retrain or retest Layer-2 with labeled Cantonese or Mandarin scam and non-scam text.
- Weeks 7–9: unpack a small pilot from the local Cantonese tar.gz into `data/layer3/bonafide/`. Make spoof clips on the RTX 4080 Super if the Mac cannot run IndexTTS-2. The current number is English YouTube versus TTS only. TFLite INT8 is not done.
- Weeks 10–12: Android UI for older users, spoken alert, optional family notice.
- Weeks 13–14: evaluation, APA 7 report, and demo. Do not invent accuracy numbers.
- Check keywords against the ADCC handbook.
- Confirm the unchecked hotlines.

## Limits (keep these)

- Input is text. There is no separate caller-ID field.
- A scammer can mention 18222 and lower the score.
- A score is a warning, not a legal finding.
- The lexicon misses many lines. About four in ten English scam rows have no concept hit. That caps recall.
- The BANK weight is high. The single word `銀行` can have a high raw probability. A rule gate keeps the shown risk low.
- Layer-3 has no licensed Cantonese scam audio.
- Do not clone a real person's voice.
- Do not write an accuracy number before a real training run.
