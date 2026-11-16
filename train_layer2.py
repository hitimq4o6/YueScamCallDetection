"""Train the Layer-2 lexicon logistic model offline. Do not run this on the phone."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from layer1_score import load_all
from layer2_score import MODEL_PATH, feature_names, feature_vector, score_text

ROOT = Path(__file__).resolve().parent
TRAIN_PATH = ROOT / "kaggle_data" / "archive (1)" / "composite_train.csv"
TEST_PATH = ROOT / "kaggle_data" / "archive (1)" / "composite_test.csv"
EVAL_PATH = ROOT / "models" / "layer2_eval.json"


def load_rows(path: Path) -> tuple[list[str], list[int]]:
    texts: list[str] = []
    labels: list[int] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            label = (row.get("label") or "").strip()
            text = row.get("text") or ""
            if label not in {"0", "1"} or not text.strip():
                continue
            texts.append(text)
            labels.append(int(label))
    return texts, labels


def matrix(texts: list[str], concepts, digits, rules, names: list[str]) -> list[list[float]]:
    rows = []
    for text in texts:
        vector, _weights = feature_vector(text, concepts, digits, rules, names)
        rows.append(vector)
    return rows


def rates(labels: list[int], vectors: list[list[float]], names: list[str]) -> dict[str, float]:
    concept_index = [index for index, name in enumerate(names) if name not in {"n_concepts", "n_high", "whitelist", "number_bonus"}]
    hit = 0
    positive = 0
    positive_hit = 0
    for label, vector in zip(labels, vectors):
        fired = any(vector[index] > 0 for index in concept_index)
        hit += int(fired)
        if label == 1:
            positive += 1
            positive_hit += int(fired)
    return {
        "rows_with_concept": round(hit / len(labels), 4) if labels else 0.0,
        "scam_rows_with_concept": round(positive_hit / positive, 4) if positive else 0.0,
    }


def metrics_at(labels: list[int], probabilities, threshold: float) -> dict[str, float]:
    predicted = [1 if value >= threshold else 0 for value in probabilities]
    return {
        "threshold": round(threshold, 2),
        "accuracy": round(accuracy_score(labels, predicted), 4),
        "precision": round(precision_score(labels, predicted, zero_division=0), 4),
        "recall": round(recall_score(labels, predicted, zero_division=0), 4),
        "f1": round(f1_score(labels, predicted, zero_division=0), 4),
    }


def choose_threshold(labels: list[int], probabilities) -> float:
    best_threshold = 0.5
    best_f1 = -1.0
    steps = [index / 100 for index in range(30, 71)]
    for threshold in steps:
        score = metrics_at(labels, probabilities, threshold)["f1"]
        if score > best_f1:
            best_f1 = score
            best_threshold = threshold
    return best_threshold


def main() -> None:
    concepts, digits, rules = load_all()
    names = feature_names(concepts)
    train_text, train_y = load_rows(TRAIN_PATH)
    test_text, test_y = load_rows(TEST_PATH)
    fit_text, val_text, fit_y, val_y = train_test_split(
        train_text,
        train_y,
        test_size=0.2,
        random_state=7,
        stratify=train_y,
    )
    fit_x = matrix(fit_text, concepts, digits, rules, names)
    val_x = matrix(val_text, concepts, digits, rules, names)
    best_c = 1.0
    best_f1 = -1.0
    for penalty in (0.1, 1.0, 10.0):
        probe = LogisticRegression(C=penalty, class_weight="balanced", max_iter=500)
        probe.fit(fit_x, fit_y)
        val_proba = probe.predict_proba(val_x)[:, 1]
        score = metrics_at(val_y, val_proba, 0.5)["f1"]
        if score > best_f1:
            best_f1 = score
            best_c = penalty
    train_x = matrix(train_text, concepts, digits, rules, names)
    model = LogisticRegression(C=best_c, class_weight="balanced", max_iter=500)
    model.fit(train_x, train_y)
    val_proba = model.predict_proba(val_x)[:, 1]
    threshold = choose_threshold(val_y, val_proba)
    test_x = matrix(test_text, concepts, digits, rules, names)
    test_proba = model.predict_proba(test_x)[:, 1]
    majority = max(sum(test_y), len(test_y) - sum(test_y)) / len(test_y)
    payload = {
        "type": "logistic_regression",
        "features": names,
        "coef": [round(float(value), 6) for value in model.coef_[0]],
        "intercept": round(float(model.intercept_[0]), 6),
        "threshold": threshold,
        "trained_on": "kaggle_data/archive (1)/composite_train.csv",
        "evaluated_on": "kaggle_data/archive (1)/composite_test.csv",
        "note": "Advisory only. English composite labels. Not a legal finding. Not a Hong Kong handbook evaluation.",
    }
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    evaluation = {
        "C": best_c,
        "train_rows": len(train_y),
        "test_rows": len(test_y),
        "test_scam_rate": round(sum(test_y) / len(test_y), 4),
        "majority_accuracy": round(majority, 4),
        "test": metrics_at(test_y, test_proba, threshold),
        "coverage": rates(test_y, test_x, names),
        "language": "composite files are almost all English; not a Cantonese evaluation",
    }
    EVAL_PATH.write_text(json.dumps(evaluation, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(evaluation, ensure_ascii=False, indent=2))
    for text in (
        "請致電18222或999查詢",
        "我是公安，請把錢轉入安全帳戶並立即轉帳",
        "銀行",
    ):
        result = score_text(text, concepts, digits, rules, payload)
        print(result["risk"], result["score"], result["proba"], text)


if __name__ == "__main__":
    sys.exit(main())
