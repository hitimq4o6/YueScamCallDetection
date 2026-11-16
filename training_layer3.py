"""Offline Layer-3 trainer. Same small Mel-CNN as training.py. Advisory only, not a legal finding."""

from __future__ import annotations

import argparse
import random
from pathlib import Path

import torch
import torch.nn as nn
import torchaudio
from torch.utils.data import DataLoader, Dataset

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "layer3"
SAVE_PATH = ROOT / "models" / "cnn_small.pt"
SAMPLE_RATE = 16000
DURATION_SEC = 3.0
N_MELS = 64
N_FFT = 1024
HOP_LENGTH = 160
BATCH_SIZE = 16
EPOCHS = 15
LR = 1e-3
SEED = 42
AUDIO_EXTS = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}
LABELS = {"bonafide": 0, "spoof": 1}
CLASS_DIRS = ("bonafide", "spoof")


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def pick_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    mps = getattr(torch.backends, "mps", None)
    if mps is not None and mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def load_waveform(path: Path) -> tuple[torch.Tensor, int]:
    try:
        return torchaudio.load(path)
    except Exception:
        return load_waveform_av(path)


def load_waveform_av(path: Path) -> tuple[torch.Tensor, int]:
    import av

    chunks = []
    sample_rate = SAMPLE_RATE
    with av.open(str(path)) as container:
        stream = container.streams.audio[0]
        sample_rate = int(stream.sample_rate or stream.rate or SAMPLE_RATE)
        for frame in container.decode(stream):
            array = frame.to_ndarray()
            channels = int(frame.layout.nb_channels)
            tensor = torch.from_numpy(array)
            if channels > 1 and tensor.shape[0] == 1:
                tensor = tensor.reshape(-1, channels).transpose(0, 1)
            elif tensor.ndim == 1:
                tensor = tensor.unsqueeze(0)
            tensor = tensor.float()
            if array.dtype.kind in "iu":
                if array.dtype.itemsize == 2:
                    tensor = tensor / 32768.0
                elif array.dtype.itemsize == 4:
                    tensor = tensor / 2147483648.0
                else:
                    tensor = tensor / max(abs(float(array.max())), abs(float(array.min())), 1.0)
            chunks.append(tensor.contiguous())
    if not chunks:
        raise RuntimeError(f"no audio in {path}")
    return torch.cat(chunks, dim=1), sample_rate


def list_audio(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(path for path in folder.rglob("*") if path.suffix.lower() in AUDIO_EXTS)


def mel_transform() -> torchaudio.transforms.MelSpectrogram:
    return torchaudio.transforms.MelSpectrogram(
        sample_rate=SAMPLE_RATE,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        n_mels=N_MELS,
    )


def aligned_num_samples() -> int:
    raw = mel_transform()(torch.zeros(int(SAMPLE_RATE * DURATION_SEC)))
    frames = int(raw.shape[-1])
    aligned = ((frames + 15) // 16) * 16
    return (aligned - 1) * HOP_LENGTH


NUM_SAMPLES = aligned_num_samples()


def mel_time_frames() -> int:
    spec = mel_transform()(torch.zeros(NUM_SAMPLES))
    return int(spec.shape[-1])


def input_shape() -> tuple[int, int, int, int]:
    return (1, 1, N_MELS, mel_time_frames())


class AudioFolderDataset(Dataset):
    def __init__(self, items: list[tuple[Path, int]]) -> None:
        self.items = items
        self.num_samples = NUM_SAMPLES
        self.mel = mel_transform()
        self.db = torchaudio.transforms.AmplitudeToDB()

    def __len__(self) -> int:
        return len(self.items)

    def _load(self, path: Path) -> torch.Tensor:
        wav, sr = load_waveform(path)
        if wav.size(0) > 1:
            wav = wav.mean(dim=0, keepdim=True)
        if sr != SAMPLE_RATE:
            wav = torchaudio.functional.resample(wav, sr, SAMPLE_RATE)
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


def collect_split(split: str) -> list[tuple[Path, int]]:
    items: list[tuple[Path, int]] = []
    for name in CLASS_DIRS:
        folder = DATA_DIR / split / name
        items.extend((path, LABELS[name]) for path in list_audio(folder))
    return items


def count_split(split: str) -> dict[str, int]:
    return {name: len(list_audio(DATA_DIR / split / name)) for name in CLASS_DIRS}


def missing_data_message() -> str | None:
    lines = []
    blocked = False
    for split in ("train", "val"):
        counts = count_split(split)
        for name in CLASS_DIRS:
            count = counts[name]
            folder = DATA_DIR / split / name
            if count == 0:
                blocked = True
            state = "missing" if not folder.is_dir() else f"{count} files"
            lines.append(f"  {folder.relative_to(ROOT)}: {state}")
    if not blocked:
        return None
    detail = "\n".join(lines)
    return (
        "Layer-3 training did not start. No accuracy is reported.\n"
        "Put licensed public audio in these folders. Accepted: .wav .mp3 .flac .m4a .ogg\n"
        f"{detail}\n"
        "Need at least one bonafide file and one spoof file in both train and val.\n"
        "Do not generate or clone a real person's voice. Do not scrape HKJunkCall."
    )


def binary_f1(y_true: list[int], y_pred: list[int], positive: int = 1) -> float:
    tp = sum(1 for truth, pred in zip(y_true, y_pred) if truth == positive and pred == positive)
    fp = sum(1 for truth, pred in zip(y_true, y_pred) if truth != positive and pred == positive)
    fn = sum(1 for truth, pred in zip(y_true, y_pred) if truth == positive and pred != positive)
    if tp == 0:
        return 0.0
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    return 2 * precision * recall / (precision + recall)


@torch.no_grad()
def evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> tuple[float, float]:
    model.eval()
    correct = 0
    total = 0
    y_true: list[int] = []
    y_pred: list[int] = []
    for spec, label in loader:
        spec = spec.to(device)
        label = label.to(device)
        pred = model(spec).argmax(dim=1)
        correct += (pred == label).sum().item()
        total += label.size(0)
        y_true.extend(label.cpu().tolist())
        y_pred.extend(pred.cpu().tolist())
    accuracy = correct / total
    return accuracy, binary_f1(y_true, y_pred)


def save_checkpoint(model: nn.Module, path: Path, val_acc: float, val_f1: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model": model.state_dict(),
            "sample_rate": SAMPLE_RATE,
            "duration_sec": DURATION_SEC,
            "n_mels": N_MELS,
            "n_fft": N_FFT,
            "hop_length": HOP_LENGTH,
            "num_samples": NUM_SAMPLES,
            "n_frames": mel_time_frames(),
            "input_shape": list(input_shape()),
            "labels": LABELS,
            "val_acc": val_acc,
            "val_f1_spoof": val_f1,
            "note": "Advisory only. Not a legal finding. Not a Hong Kong accuracy figure unless the val set is that data.",
        },
        path,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the small Layer-3 Mel-CNN offline.")
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--lr", type=float, default=LR)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR, help="folder holding train/ and val/")
    parser.add_argument("--save", type=Path, default=SAVE_PATH, help="checkpoint path to write")
    return parser.parse_args()


def main() -> None:
    global DATA_DIR, SAVE_PATH
    args = parse_args()
    DATA_DIR = args.data_dir.resolve()
    SAVE_PATH = args.save.resolve()
    if args.epochs < 1 or args.batch_size < 1 or args.lr <= 0:
        raise SystemExit("epochs and batch-size must be >= 1, and lr must be > 0")
    blocked = missing_data_message()
    if blocked:
        raise SystemExit(blocked)

    set_seed(SEED)
    device = pick_device()
    train_items = collect_split("train")
    val_items = collect_split("val")
    print(f"device: {device}")
    print(
        "train "
        + " ".join(f"{name}={count_split('train')[name]}" for name in CLASS_DIRS)
        + "  val "
        + " ".join(f"{name}={count_split('val')[name]}" for name in CLASS_DIRS)
    )
    print(f"input_shape={input_shape()}  epochs={args.epochs}  batch_size={args.batch_size}  lr={args.lr}")

    train_loader = DataLoader(
        AudioFolderDataset(train_items),
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,
    )
    val_loader = DataLoader(
        AudioFolderDataset(val_items),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
    )
    model = SmallCNN().to(device)
    params = sum(param.numel() for param in model.parameters())
    print(f"parameters={params}")
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    best_acc = -1.0
    best_f1 = 0.0

    for epoch in range(1, args.epochs + 1):
        model.train()
        running = 0.0
        seen = 0
        for spec, label in train_loader:
            spec = spec.to(device)
            label = label.to(device)
            optimizer.zero_grad()
            loss = criterion(model(spec), label)
            loss.backward()
            optimizer.step()
            running += loss.item() * label.size(0)
            seen += label.size(0)
        val_acc, val_f1 = evaluate(model, val_loader, device)
        train_loss = running / seen
        print(f"epoch {epoch:02d}  loss={train_loss:.4f}  val_acc={val_acc:.4f}  val_f1_spoof={val_f1:.4f}")
        if val_acc >= best_acc:
            best_acc = val_acc
            best_f1 = val_f1
            save_checkpoint(model, SAVE_PATH, val_acc, val_f1)

    print(f"best val_acc={best_acc:.4f}  best val_f1_spoof={best_f1:.4f}")
    print(f"saved: {SAVE_PATH}")
    print("This score is advisory only. It is not a legal finding.")


if __name__ == "__main__":
    main()
