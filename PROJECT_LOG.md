# PROJECT_LOG

Last updated: 2026-11-16

給人和 agent 共用。英文簡版在 `PROJECT_LOG_EN.md`。做完一個大項目必須同時更新這兩份 log，再結束該項工作。大項目指：週次產出、新 layer、新模組，或用戶確認的里程碑。小改動不用記。

狀態以本檔為準。未寫進來的，視為未完成。不要把暫定資料寫成已核實。

## 現況

- 進行中：用戶已於 2026-11-16 15:35 把 Common Voice 粵語錄音包放到專案根目錄。尚未解壓成 `data/layer3/bonafide/`。IndexTTS-2 仍未裝，沒有生成或克隆聲線。英文訓練結果仍不是香港準確率。
- 電話只做推論。模型只在離線訓練。
- Layer-2 不是粵語評估，也不是《全城防伏手冊》評估。

## 已做

- Layer-1 三份規則表已存在，用戶於 2026-10-25 暫定確認可用：
  - `data/layer1/official_whitelist.csv`
  - `data/layer1/scam_keywords_zh.csv`、`data/layer1/scam_keywords_en.csv`
  - `data/layer1/number_rules.csv`
- `data/layer1/seed_blacklist.csv` 故意留空。不用社區黑名單，不爬 HKJunkCall。
- `data/layer1/sources.md` 記錄來源同限制。
- `layer1_score.py`：概念組合計分、單概念不高分、白名單壓分、號碼加分。2026-10-25 內建 13 項測試全部通過。
- `api.py`：FastAPI stub，`GET /health`、`POST /score`。回傳 Layer-1，以及 Layer-2 的 `layer2_score`、`layer2_risk`、`layer2_proba`。只是建議分數，不是法律判定。
- `training.py`：Mel-CNN 訓練骨架，尚未訓練、尚未匯出。
- Layer-2（2026-10-25）：
  - `train_layer2.py`：離線訓練。特徵是 Layer-1 概念槽，不是大模型。
  - `layer2_score.py`：手機側只做點積，不需要 sklearn。
  - `models/layer2_linear.json`：邏輯回歸權重，約 910 B。
  - `models/layer2_eval.json`：英文測試集數字。
  - 單概念不可到「高」。白名單仍壓分。顯示分數經過這些閘門；`proba` 才是模型原始機率。
  - 2026-11-03：`python layer2_score.py cantonese_concept_hit_test.csv` 可跑概念命中檢查。29 行：概念 17/29，顯示 17/29，兩者都中 12/29。`URGENCY` 不在詞表。這不是香港準確率。
- Layer-3（2026-11-03）：
  - `training_layer3.py`：沿用 `training.py` 的 3 層 Mel-CNN。16 kHz、約 3 秒、64 Mel。空資料夾會停止，不印準確率。
  - `export_onnx.py`：讀 `models/cnn_small.pt`，寫 `models/cnn_small.onnx`，再做一次 dummy 檢查。
  - `requirements_layer3.txt`、`README_layer3.md`。
  - 固定輸入 `(1, 1, 64, 304)`。窗口補到 48480 samples，只為讓原有 pool 可匯出。
  - 2026-11-03 試用 `garystafford/deepfake-audio-detection`（CC-BY-4.0，英文 YouTube 真人聲對 TTS）。沒有新生成或克隆聲線。
  - 按來源切開，避免同一條 YouTube 或同一個 TTS 工作同時出現在訓練和驗證。驗證真人來源：`yt_0008`、`yt_0012`。
  - 訓練：bonafide 672、spoof 706。驗證：bonafide 261、spoof 227。15 epochs，MPS，lr 0.001，batch 16。
  - 最佳驗證在第 6 個 epoch：val_acc 0.9590，val_f1_spoof 0.9576。第 15 個 epoch 跌到 val_acc 0.6619，checkpoint 保留最佳，不是最後一輪。
  - 已存 `models/cnn_small.pt`。已匯出 `models/cnn_small.onnx`，0.342 MB，dummy 最大差 0.000002。這不是準確率。
  - 這不是粵語，也不是香港騙案電話準確率。TFLite INT8 未做。
- Layer-3 試點準備（2026-11-16）：
  - `scripts/prepare_layer3_pilot.py`：有金鑰先下載 MDC 樣本，轉 16 kHz mono WAV；IndexTTS-2 未就緒就印指令並停止。不用 YouTube，不用第三方鏡像。
  - `data/layer3/sources.md`：記錄目錄編號、CC0 目錄頁、以及當日沒有下載、沒有生成。
  - `data/layer3/spoof_prompts.csv`：30 句試點短句。未對《全城防伏手冊》核對。
  - 兩份 manifest 只有表頭，0 條音檔。
  - 目錄頁查到：Common Voice Scripted Speech 27.0 Cantonese，id `cmu5x3i5w00d6o107yvwox9lg`，locale `yue`，目錄寫 CC0-1.0，完整包 6433594094 bytes。
  - 2026-11-16：用戶確認 `1789494296567-cv-corpus-27.0-2026-09-11-yue.tar.gz` 就是上述頁面的錄音包。專案根目錄同 Downloads 各有一份，大小同目錄 `sizeBytes` 一致。包內是 `cv-corpus-27.0-2026-09-11/yue/clips/common_voice_yue_*.mp3`。內附 README 寫 CC-0，並寫明不得辨認講者身份。SHA256 未在本機重算，不要寫成 checksum 已核對。這不是騙案電話。

## Layer-2 實測（不要改成別的數字）

- 訓練：`kaggle_data/archive (1)/composite_train.csv`，36751 行。C=1.0。
- 測試：`composite_test.csv`，9188 行。幾乎全是英文。門檻 0.35，在訓練集的驗證切分上選，不是在測試集上調。
- 測試集詐騙比例 0.5652。全猜詐騙的 accuracy 是 0.5652。
- 測試集：accuracy 0.7719，precision 0.9485，recall 0.6307，f1 0.7576。
- 測試集只有 0.3513 的句子打中概念；詐騙句只有 0.5704 打中。打不中的，這個模型看不到。
- 抽查：`請致電18222或999查詢` 為低（proba 0.287）。`我是公安，請把錢轉入安全帳戶並立即轉帳` 為高（proba 0.982）。`銀行` 顯示為低，但原始 proba 0.914，靠單概念閘門壓住。

## 暫定決定

- 2026-10-25：用戶暫定三份 list 正確，第 1–4 週可先過，先做 Layer-2。
- 這不是 ADCC／警方／OFCA 核實完成。報告仍須寫明手冊語句同部分熱線尚未對一手來源核實。
- 未在已查 ADCC 頁面確認機構名稱的號碼：34236611、81056060、+852-1868。18222、`#ADCC18222`、999 已在 `sources.md` 標為已核對。
- Layer-2 先用英文 composite 訓練，讓粵／普／英共用概念槽。沒有粵語標註之前，不把上述數字寫成香港準確率。
- 2026-11-16：粵語真人聲只從 MDC 的 Common Voice yue 下載。Hugging Face 上的 Common Voice 17.0 當日是空的，不用舊鏡像，以免納入已撤回同意的聲線。
- 生成 spoof 前必須先有上述 CC0 參考音。參考音不得來自 `data/layer3/bonafide/` 以外。IndexTTS-2 粵語未必穩，聽過之前不要當粵語準確率。
- 英文 `train/`、`val/` 不要同呢個試點混在一起訓練。
- 2026-11-16：本機接到私人倉庫 `hitimq4o6/YueScamCallDetection`。不入庫：粵語 tar.gz、`kaggle_data/`、`data/hf/`、`.venv/`、`data/layer3/train/` 同 `val/` 的本機符號連結。

## 未做

- 用有標籤的粵語／普通話詐騙與非詐騙文本重訓或另測 Layer-2。
- 第 7–9 週：從已放好的粵語錄音包抽出試點 WAV 到 `data/layer3/bonafide/`。再在 4080 Super 裝 IndexTTS-2 生成 spoof。現有數字只屬英文 YouTube 對 TTS。TFLite INT8 仍未做。
- 第 10–12 週：Android 長者介面、語音警告、可選家人通知。
- 第 13–14 週：評估、報告（APA 7）、demo。不捏造準確率。
- 用《全城防伏手冊》核對關鍵詞，並核實未確認熱線。

## 限制（沿用，不要在 log 裡抹掉）

- 輸入是文字，沒有獨立來電號碼欄。
- 詐騙者在文字裡提到 18222 可以壓低分數。
- 分數只是警告，不是法律判定。
- Layer-2 詞表覆蓋不足。英文測試集約四成詐騙句沒有概念命中，召回受此限制。
- `BANK` 權重高。單字「銀行」原始機率可以很高，目前只靠規則閘門維持「低」。
- Layer-3 沒有授權的粵語騙案音頻。不要生成或克隆他人聲線。沒有訓練結果之前，不要寫準確率。
