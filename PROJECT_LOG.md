# PROJECT_LOG

Last updated: 2026-11-16

給人和 agent 共用。英文簡版在 `PROJECT_LOG_EN.md`。做完一個大項目必須同時更新這兩份 log，再結束該項工作。大項目指：週次產出、新 layer、新模組，或用戶確認的里程碑。小改動不用記。

狀態以本檔為準。未寫進來的，視為未完成。不要把暫定資料寫成已核實。

## 現況

- 進行中：2026-11-16 粵語 Layer-3 pilot 已訓練並匯出 ONNX。checkpoint `models/cnn_small_zh_split2.pt`，ONNX `models/cnn_small_zh.onnx`，val 25/27 正確。這不是香港準確率，樣本只有 60 條，spoof 只有 2 條 TTS 聲線。第 7–9 週交付已齊。TFLite INT8 同手機大小／延遲測試已移到第 10–12 週。
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
  - 同日 `scripts/prepare_layer3_bonafide.py` 抽出 30 條。條件：3–6 秒、`up_votes>=2`、`down_votes==0`、30 個不同 `client_id` 各 1 條。輸出 `data/layer3/bonafide/cv_yue_000.wav` 至 `cv_yue_029.wav`，16 kHz mono。實測時長全部在 3–6 秒。`split.json` 的 `yue_pilot` 是 train 24、val 6。沒有改英文 `train/`、`val/`。
  - 30 條 WAV 同 `spoof_prompts.csv` 已複製到 `user@192.168.50.86` 的 `C:\layer3\refs` 同 `C:\layer3`。Windows 列出 30 個 wav。
  - 同日 IndexTTS-2 已在 `C:\Users\user\Desktop\fyp\index-tts`，commit `d9e41aa`。輔助模型因 Windows 憑證錯誤，改由 Mac 下載再傳入 `checkpoints_2\hf_cache`。
  - 試聽 3 條已生成：`C:\layer3\spoof\indextts2_000.wav` 至 `002`，本機副本在 `data/layer3/spoof/`。時長 8.70、5.17、5.47 秒，22050 Hz。日誌顯示多個粵語字是 unknown token。這不是準確率。未跑齊 30 條。
  - 同日發現 IndexTTS-2 只會出普通話：BPE 詞表缺大量繁體字（係、哋、喺、咗、嚟、個、戶、處、職、員、銀 皆不在），`我係入境處職員` 有 4 個 unknown；官方亦不支援粵語。用戶要求真粵語發音，故改用 Qwen3-TTS 粵語模型。
  - 新方案：`jmtl/hk-cantonese-cc0-qwen3-tts` v0.0.5（Apache-2.0，LoRA over `Qwen/Qwen3-TTS-12Hz-1.7B-Base`，用 Common Voice yue 22.0 + zh-HK 27.0 的 CC0 資料訓練）。聲音是內建 `hk_voice_343`，生成時不讀參考音、不即時克隆。
  - 執行：Mac 用 `scripts/apply_adapter.py` 合併出 4.21 GB 模型，經 tar over SSH 送到 `C:\layer3\tts\hk-cantonese`。Windows 裝 `qwen-tts==0.1.1`（會把 transformers 升到 4.57.3）。
  - 3 條試聽已生成：`data/layer3/spoof/qwentts_000..002.wav`，24 kHz，9.20、8.72、10.88 秒。腳本 `scripts/windows_generate_yue_tts.py`。已刪除 3 條 IndexTTS-2 普通話檔。
  - 同日擴至 30 條。模型內建兩個 CC0 聲線 `hk_voice_343`、`hk_voice_777`，交替使用，非克隆。新增 `data/layer3/neutral_prompts.csv` 17 句日常非詐騙短句。最終 30 條：詐騙風格 15、日常 15；兩個聲線各 15。時長 4.24–12.48 秒，平均 8.55 秒，24 kHz。`spoof_manifest.csv` 加 `kind` 欄。
  - 用戶指出兩個內建聲線其實都是女聲，會有 bias。已查證模型卡：v0.0.5 是單一女士捐贈者聲線。用戶決定暫時不換 TTS，先用現有 30 條完成 Layer-3。
  - 發現並修正資料洩漏：原先 bonafide 16 kHz、spoof 24 kHz，模型可單靠頻譜邊界分辨。已把 30 條 spoof 重採樣到 16 kHz mono，兩邊一致。
  - `scripts/layout_layer3_zh.py` 建立 `data/layer3_zh/` 同 `data/layer3_zh_split2/`，唔改英文 `data/layer3/{train,val}`。
  - `training_layer3.py` 加 `--data-dir` 同 `--save`，可用其他資料夾同 checkpoint 名。
  - split2 拆分：train bonafide 18、spoof 15；val bonafide 12、spoof 15。8 epochs、batch 8、lr 0.0005、MPS。
  - 結果：train 18/18、15/15；val bonafide 12/12、spoof 13/15。寫入 `models/layer3_zh_eval.json`。
  - 中途一度誤判模型失效，原因是診斷腳本漏了 AmplitudeToDB 同標準化。用 `AudioFolderDataset` 重測後才正確。
  - 限制：spoof 只有 2 條 TTS 聲線、全部女聲；60 條樣本；驗證集只 27 條。唔可以寫成香港準確率。
  - 同日完成第 7–9 週 ONNX 交付：`export_onnx.py` 加 `--checkpoint`、`--out`。匯出 `models/cnn_small_zh.onnx`，0.342 MB，輸入 `(1,1,64,304)`、輸出 `(1,2)`，dummy max_abs_diff 0.000000。這不是準確率。
  - 第 7–9 週交付（Small CNN + ONNX export）已齊。
  - 由第 7–9 週移到第 10–12 週的項目：TFLite INT8 量化。原因：要先確認 Android 手機 runtime 同實際 CPU 表現，唔應該在第 7–9 週單獨做完。同期一併做手機推論大小同延遲測試。
  - 語音模型卡提醒：這是真人捐贈者的聲線，須標示為合成語音，不得冒充他人。仍未跑齊 30 條。

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
- 第 10–12 週：Android 長者介面、語音警告、可選家人通知。同期做原定第 7–9 週的 TFLite INT8 量化，以及手機推論大小同延遲測試，因為要先有 Android runtime 才量得準。
- 第 13–14 週：評估、報告（APA 7）、demo。不捏造準確率。
- 用《全城防伏手冊》核對關鍵詞，並核實未確認熱線。
- 換多聲線粵語 TTS，解決 spoof 只有 2 條女聲的 bias。

## 限制（沿用，不要在 log 裡抹掉）

- 輸入是文字，沒有獨立來電號碼欄。
- 詐騙者在文字裡提到 18222 可以壓低分數。
- 分數只是警告，不是法律判定。
- Layer-2 詞表覆蓋不足。英文測試集約四成詐騙句沒有概念命中，召回受此限制。
- `BANK` 權重高。單字「銀行」原始機率可以很高，目前只靠規則閘門維持「低」。
- Layer-3 沒有授權的粵語騙案音頻。不要生成或克隆他人聲線。沒有訓練結果之前，不要寫準確率。
