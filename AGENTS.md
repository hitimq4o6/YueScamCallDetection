# AGENTS.md — Elderly-Friendly Suspicious Call Detection App (Hong Kong)

## Project Summary

Build a lightweight, elderly-friendly Android application that detects suspicious incoming calls and SMS for Hong Kong seniors. The system combines three scoring layers and immediately alerts the user (voice + text) and optionally notifies emergency contacts.

**Core constraint**: Models are trained offline (RTX 4080 Super / MacBook Air M4). Only the already-trained, quantized model runs on the phone for inference. Never train on-device.

## Objectives

- Collect and organise public rule data (ADCC handbook, official hotlines, keywords).
- Implement a three-layer scoring pipeline:
  1. Rule-based detection (CSV knowledge base)
  2. Lightweight NLP (concept / keyword / sentiment cues on transcripts or SMS)
  3. Small deepfake-voice classifier (Mel-CNN, quantized for mobile)
- Deliver an elderly-friendly Android app (large text, voice alerts, family notification).
- Evaluate on public datasets + synthetic Hong Kong-style test items (no impersonation of real private individuals).

## Technical Architecture

| Layer | Component | Runtime | Notes |
|-------|-----------|---------|-------|
| 1. Rules | CSV whitelist + keyword scorer | Phone (local) | Official hotlines, ADCC phrases, number patterns. No training needed. |
| 2. NLP | Concept / lexicon scoring | Phone or server | Multilingual concept slots (粵 / 普 / 英). Prefer classical ML or tiny linear model. |
| 3. Voice | Small Mel-CNN | Phone (inference only) | Train on 4080 Super → export ONNX / TFLite INT8 (~5–10 MB target). |
| App | React Native / Expo | Android | Large UI, spoken alerts. First demo may call FastAPI. |
| Backend | FastAPI + FFmpeg | Development server | Optional fallback during early integration. |

**Hardware split**
- MacBook Air M4: data cleaning, rule testing, small dry-runs
- RTX 4080 Super: main CNN training + export
- Old Android phone: inference + UX testing only

## Data & Knowledge Sources

### Primary (Layer 1)
- ADCC *全城防伏手冊* (2026, 2nd ed.) — official scam types and phrases
- Official hotlines / SMS IDs: 18222, #ADCC18222, 999, 34236611, 81056060, +852-1868
- OFCA guidance on fraudulent calls

### Reference corpora (for concept alignment & related work only)
- Kaggle: Tee Connie Scam/Non-Scam Call Conversation Dataset
- Kaggle: Composite Scam Transcript Dataset / Call Transcripts Scam Determinations
- TeleAntiFraud-28K / Chinese Scam Call Dataset
- Mendeley ScamGen (Chinese telephone scams)
- GitHub: Telecom_Fraud_Texts
- Hugging Face: chinese-american-elder-fraud-qa
- English phrase lists: KindWatch, SavingAdvice, FTC, AARP (for conceptual mapping only)

**Important**: Do not bulk-scrape HKJunkCall. Single-number manual lookup or formal data-sharing key only. Community reports are weak evidence.

## Multilingual Concept Mapping (Layer 1 + 2)

Do not match English strings only. Map surface forms (Cantonese / Mandarin / English) into shared concept slots.

Example concepts:
- `BANK` ← 銀行, bank, HSBC, 戶口, 理財
- `AUTHORITY` ← 公安, 入境處, IRS, warrant, 拘捕令
- `MONEY_MOVE` ← 轉帳, 保證金, 安全帳戶, gift card
- `SECRECY` ← 唔好同人講, don’t tell Mom, 保密
- `REMOTE` ← 遠端, TeamViewer, 驗證碼, 密碼

**Scoring rule**: Single ordinary word (e.g. 銀行) = low score only. Require combination of high-weight concepts before high alert. Official whitelist numbers heavily reduce score.

Suggested CSV format:
```csv
surface,lang,concept,weight
銀行,zh-HK,BANK,40
bank,en,BANK,40
保證金,zh-HK,MONEY_MOVE,90
warrant,en,AUTHORITY,85
```

## Hard Constraints (must follow)

- Train offline only. Phone runs inference of a quantized model.
- Keep models small enough for old Android phones (target ONNX/TFLite INT8, ~5–10 MB for voice head).
- Do not train large transformers from scratch.
- Do not generate or clone real people’s voices to create scam samples.
- Do not bulk-enumerate or scrape HKJunkCall (e.g. looping `?ft=2000–9999`).
- Do not treat community reports as official blacklist.
- Scores are advisory warnings only — not legal determinations.
- When regenerating the Project Plan document: **omit the “Scope — out” section**. Integrate any necessary limitations into objectives, method, or ethics sections instead.

## Expected Deliverables

- Project report (with APA 7 references)
- Source code (training, Layer-1 scorer, API, app)
- Android demo app (elderly-friendly UI)
- Live or recorded demo
- Model artefact (.pt / .onnx / TFLite)

## Project Schedule (indicative, mid-Sep 2026 start)

| Weeks | Focus | Output |
|-------|-------|--------|
| 1–2 | Layer-1 data collection | ADCC handbook CSVs, whitelist |
| 3–4 | Layer-1 scorer + FastAPI stub | `layer1_score.py` |
| 5–6 | Layer-2 text model | Lexicon + simple classifier |
| 7–9 | Layer-3 audio training (4080 Super) | Small CNN + ONNX export |
| 10–12 | Android UI + integration | Alerts, family notify, UX pass |
| 13–14 | Evaluation + report + demo | Accuracy note, source freeze |

## AI Usage Guidelines

- Use AI for literature structuring, boilerplate code, UI copy, and report drafting.
- Always verify official numbers, hotline IDs, and handbook phrases against primary ADCC / Police / OFCA sources.
- Do not invent accuracy numbers.
- Disclose AI tools used in the final report.
- Do not use AI to generate impersonated voices or bulk scrapers.

## Success Criteria

- Layer 1 correctly flags handbook official-impersonation phrases and official hotlines.
- Combined demo produces visible + spoken warning on a suspicious sample within a few seconds on modest Android hardware (server fallback acceptable for first demo).
- Report honestly states limitations: number rotation, caller-ID spoofing, scarce Cantonese spoof data, difference between junk marketing and criminal fraud.

## Key Files Already Started

- `PROJECT_LOG.md` — shared status log (Chinese); update after every major item
- `PROJECT_LOG_EN.md` — same status in simple English; update in the same turn
- `layer2_score.py` / `train_layer2.py` — lexicon logistic model; weights in `models/layer2_linear.json`
- `training.py` — lightweight Mel-CNN training skeleton (torchaudio, 16 kHz, 3-second windows)
- `data/layer1/` — starter CSVs (whitelist, keywords, number rules)
- Project plan draft (Word) — to be regenerated without “Scope — out” section

## Notes for the Agent

- Prefer official ADCC / OFCA sources over community databases for production rules.
- Keep the phone path extremely light. Prefer system ASR + local concept scoring before any neural model.
- When the user asks to regenerate the Project Plan, drop the entire “Scope — out” section.
- All references in academic writing must follow APA 7th edition.
- **Mandatory:** after every major item, update both `PROJECT_LOG.md` and `PROJECT_LOG_EN.md` in the same turn before finishing. A major item is a schedule-week deliverable, a new layer, a new module, or a user-confirmed milestone. Record what was done, what remains, and any provisional decision. Do not mark unverified sources as verified. Skip the log for tiny edits. Read both logs at the start of a project task so status matches the logs, not memory. Keep `PROJECT_LOG_EN.md` in simple English and short sentences.
