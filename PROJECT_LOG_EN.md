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
- On 2026-11-16, 30 Cantonese read-speech clips were extracted to `data/layer3/bonafide/`.
- The same 30 files were copied to Windows `C:\layer3\refs`.
- IndexTTS-2 then made 3 listen-test spoof clips, but it only speaks Mandarin.
- The user asked for real Cantonese speech. The project switched to `jmtl/hk-cantonese-cc0-qwen3-tts` v0.0.5.
- All 30 Cantonese spoof clips are made. Two built-in voices were used, 15 clips each. 15 clips are scam-style and 15 are everyday lines.
- The Cantonese Layer-3 pilot is trained and exported to ONNX. Checkpoint `models/cnn_small_zh_split2.pt`. ONNX `models/cnn_small_zh.onnx`. Val is 25/27 correct.
- This is not a Hong Kong accuracy. There are only 60 clips and just 2 TTS voices.
- The weeks 7–9 deliverable is complete.
- Moved to weeks 10–12: TFLite INT8, plus phone model-size and latency checks.- The phone only runs inference.
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
  - On 2026-11-16 `scripts/prepare_layer3_bonafide.py` wrote 30 files: `cv_yue_000.wav` to `cv_yue_029.wav`.
  - Rules: 3–6 seconds, `up_votes>=2`, `down_votes==0`, one clip per `client_id`.
  - Format checked: 16 kHz mono. Measured duration stayed inside 3–6 seconds.
  - `split.json` key `yue_pilot` is train 24, val 6. The English `train/` and `val/` folders were not changed.
  - Windows `user@192.168.50.86` has the 30 wav files in `C:\layer3\refs` and `spoof_prompts.csv` in `C:\layer3`.
  - IndexTTS-2 is installed at `C:\Users\user\Desktop\fyp\index-tts`, commit `d9e41aa`.
  - Windows could not download Hugging Face helper models because of a certificate error. The Mac downloaded them and copied them to `checkpoints_2\hf_cache`.
  - Three listen clips exist: `indextts2_000.wav` to `indextts2_002.wav`. Durations are 8.70, 5.17, and 5.47 seconds. Sample rate is 22050 Hz.
  - The log says many Cantonese characters are unknown tokens. This is not an accuracy number. The other 27 clips were not generated.
  - Cause found: IndexTTS-2 uses a Mandarin tokenizer. Common Traditional characters like 係, 哋, 喺, 咗, 嚟, 個, 戶, 處, 職, 員, 銀 are missing from its BPE table. IndexTTS-2 has no Cantonese support.
  - Replacement model: `jmtl/hk-cantonese-cc0-qwen3-tts` v0.0.5. Apache-2.0. A LoRA on `Qwen/Qwen3-TTS-12Hz-1.7B-Base`, trained on CC0 Common Voice yue 22.0 and zh-HK 27.0.
  - The voice is baked in as `hk_voice_343`. It does not read a reference clip at run time.
  - The Mac merged the adapter into a 4.21 GB model and copied it to `C:\layer3\tts\hk-cantonese` with tar over SSH.
  - Windows has `qwen-tts==0.1.1`. It upgraded transformers to 4.57.3.
  - Three Cantonese clips exist: `data/layer3/spoof/qwentts_000.wav` to `002.wav`, 24 kHz, 9.20, 8.72, 10.88 seconds. Script is `scripts/windows_generate_yue_tts.py`.
  - The 3 Mandarin IndexTTS-2 clips were deleted.
  - Model card: this is one real CC0 contributor voice. Label output as synthetic. Do not impersonate anyone.
  - Expanded to 30 clips. The model has two built-in CC0 voices: `hk_voice_343` and `hk_voice_777`. They alternate. Nothing is cloned.
  - New file `data/layer3/neutral_prompts.csv` has 17 everyday, non-scam lines.
  - Final set: 15 scam-style and 15 neutral. 15 clips per voice.
  - Durations 4.24 to 12.48 seconds, mean 8.55. Sample rate 24 kHz.
  - `spoof_manifest.csv` now has a `kind` column.
  - The user said both built-in voices are female, so the spoof class is biased. The model card confirms v0.0.5 is one female donor.
  - The user chose to keep these clips for now and finish Layer-3.
  - Fixed a data leak: bonafide was 16 kHz and spoof was 24 kHz, so a model could split on bandwidth alone. All 30 spoof clips were resampled to 16 kHz mono.
  - `scripts/layout_layer3_zh.py` builds `data/layer3_zh/` and `data/layer3_zh_split2/`. The English `data/layer3/{train,val}` folders were not touched.
  - `training_layer3.py` now has `--data-dir` and `--save`.
  - split2: train bonafide 18, spoof 15; val bonafide 12, spoof 15. 8 epochs, batch 8, lr 0.0005, MPS.
  - Result: train 18/18 and 15/15; val bonafide 12/12 and spoof 13/15. Saved in `models/layer3_zh_eval.json`.
  - One check wrongly showed the model as broken. The cause was a probe script that skipped AmplitudeToDB and normalisation. Re-testing with `AudioFolderDataset` gave the correct result.
  - Limits: only 2 TTS voices and all female. Only 60 clips. Val is only 27 clips. Do not call it a Hong Kong accuracy.
  - Weeks 7–9 ONNX deliverable is done. `export_onnx.py` now takes `--checkpoint` and `--out`.
  - Exported `models/cnn_small_zh.onnx`, 0.342 MB. Input `(1,1,64,304)`, output `(1,2)`. Dummy max_abs_diff 0.000000. This is not an accuracy number.
  - Weeks 7–9 (Small CNN + ONNX export) are complete.
  - Moved from weeks 7–9 to weeks 10–12: TFLite INT8 quantisation.
  - Reason: the Android runtime and real phone CPU speed must be checked first. That step should not be done alone in weeks 7–9.
  - The weeks 10–12 work also covers model size and latency checks on the phone.

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
- Weeks 10–12: Android UI for older users, spoken alert, optional family notice. TFLite INT8 quantisation from weeks 7–9 is done here too, plus phone model-size and latency checks, because the Android runtime is needed to measure them.
- Weeks 13–14: evaluation, APA 7 report, and demo. Do not invent accuracy numbers.
- Check keywords against the ADCC handbook.
- Confirm the unchecked hotlines.
- Move to a multi-voice Cantonese TTS to fix the 2-female-voice spoof bias.

## Limits (keep these)

- Input is text. There is no separate caller-ID field.
- A scammer can mention 18222 and lower the score.
- A score is a warning, not a legal finding.
- The lexicon misses many lines. About four in ten English scam rows have no concept hit. That caps recall.
- The BANK weight is high. The single word `銀行` can have a high raw probability. A rule gate keeps the shown risk low.
- Layer-3 has no licensed Cantonese scam audio.
- Do not clone a real person's voice.
- Do not write an accuracy number before a real training run.
