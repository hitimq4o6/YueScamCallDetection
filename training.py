"""
最簡語音真假分類訓練腳本（ Mel-spectrogram + 細 CNN ）

資料夾結構：
  data/
    real/   *.wav *.mp3 *.flac *.m4a
    fake/   *.wav *.mp3 *.flac *.m4a

用法：
  pip install torch torchaudio scikit-learn
  python training.py
"""

from __future__ import annotations

import random
from pathlib import Path

import torch
import torch.nn as nn
import torchaudio
from sklearn.metrics import classification_report
from torch.utils.data import DataLoader, Dataset, random_split

# ---------- 設定 ----------
DATA_DIR = Path("data")
SAVE_PATH = Path("models/cnn_small.pt")
SAMPLE_RATE = 16000
DURATION_SEC = 3.0
N_MELS = 64
BATCH_SIZE = 16
EPOCHS = 15
LR = 1e-3
VAL_RATIO = 0.2
SEED = 42
AUDIO_EXTS = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def list_audio(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return [p for p in folder.rglob("*") if p.suffix.lower() in AUDIO_EXTS]


class AudioFolderDataset(Dataset):
    def __init__(self, items: list[tuple[Path, int]], sample_rate: int, duration: float, n_mels: int):
        self.items = items
        self.sample_rate = sample_rate
        self.num_samples = int(sample_rate * duration)
        self.mel = torchaudio.transforms.MelSpectrogram(
            sample_rate=sample_rate,
            n_fft=1024,
            hop_length=160,
            n_mels=n_mels,
        )
        self.db = torchaudio.transforms.AmplitudeToDB()

    def __len__(self) -> int:
        return len(self.items)

    def _load(self, path: Path) -> torch.Tensor:
        wav, sr = torchaudio.load(path)
        if wav.size(0) > 1:
            wav = wav.mean(dim=0, keepdim=True)
        if sr != self.sample_rate:
            wav = torchaudio.functional.resample(wav, sr, self.sample_rate)
        wav = wav.squeeze(0)
        if wav.numel() < self.num_samples:
            wav = torch.nn.functional.pad(wav, (0, self.num_samples - wav.numel()))
        else:
            wav = wav[: self.num_samples]
        return wav

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        path, label = self.items[idx]
        wav = self._load(path)
        spec = self.db(self.mel(wav))
        spec = (spec - spec.mean()) / (spec.std() + 1e-5)
        return spec.unsqueeze(0), label


class SmallCNN(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4)),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(0.3),
            nn.Linear(64 * 4 * 4, 64),
            nn.ReLU(),
            nn.Linear(64, 2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(x))


@torch.no_grad()
def evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> tuple[float, list[int], list[int]]:
    model.eval()
    correct = 0
    total = 0
    y_true: list[int] = []
    y_pred: list[int] = []
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        pred = model(x).argmax(dim=1)
        correct += (pred == y).sum().item()
        total += y.size(0)
        y_true.extend(y.cpu().tolist())
        y_pred.extend(pred.cpu().tolist())
    return correct / max(total, 1), y_true, y_pred


def main() -> None:
    set_seed(SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device: {device}")

    real_files = list_audio(DATA_DIR / "real")
    fake_files = list_audio(DATA_DIR / "fake")
    items = [(p, 0) for p in real_files] + [(p, 1) for p in fake_files]
    if len(real_files) == 0 or len(fake_files) == 0:
        raise SystemExit(
            f"找不到音檔。請放入 {DATA_DIR}/real 同 {DATA_DIR}/fake\n"
            f"而家 real={len(real_files)} fake={len(fake_files)}"
        )

    random.shuffle(items)
    print(f"real={len(real_files)}  fake={len(fake_files)}  total={len(items)}")

    dataset = AudioFolderDataset(items, SAMPLE_RATE, DURATION_SEC, N_MELS)
    val_size = max(1, int(len(dataset) * VAL_RATIO))
    train_size = len(dataset) - val_size
    train_set, val_set = random_split(dataset, [train_size, val_size], generator=torch.Generator().manual_seed(SEED))

    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_set, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    model = SmallCNN().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    best_acc = 0.0
    SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, EPOCHS + 1):
        model.train()
        running = 0.0
        n = 0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            loss = criterion(model(x), y)
            loss.backward()
            optimizer.step()
            running += loss.item() * y.size(0)
            n += y.size(0)

        val_acc, y_true, y_pred = evaluate(model, val_loader, device)
        train_loss = running / max(n, 1)
        print(f"epoch {epoch:02d}  loss={train_loss:.4f}  val_acc={val_acc:.4f}")

        if val_acc >= best_acc:
            best_acc = val_acc
            torch.save(
                {
                    "model": model.state_dict(),
                    "sample_rate": SAMPLE_RATE,
                    "duration_sec": DURATION_SEC,
                    "n_mels": N_MELS,
                    "labels": {"real": 0, "fake": 1},
                },
                SAVE_PATH,
            )

    print(f"best val acc={best_acc:.4f}")
    print(f"saved: {SAVE_PATH.resolve()}")
    print(classification_report(y_true, y_pred, target_names=["real", "fake"]))


if __name__ == "__main__":
    main()
