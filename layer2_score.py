"""Layer-2 lexicon linear scorer. Advisory warning only, not a legal finding."""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

from layer1_score import (
    HIGH_CONCEPT_WEIGHT,
    HIGH_SCORE,
    MED_SCORE,
    NUMBER_BONUS_CAP,
    SINGLE_STRONG_SCORE,
    SINGLE_WEAK_CAP,
    WHITELIST_CAP,
    WHITELIST_FACTOR,
    find_concepts,
    load_all,
    number_bonus,
    whitelist_hit,
)

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "models" / "layer2_linear.json"
HIT_TEST_PATH = ROOT / "cantonese_concept_hit_test.csv"
HIT_COLUMNS = ("id", "category", "sentence", "expected_concepts", "expected_display", "notes")
DISPLAYS = ("low", "low_medium", "medium", "medium_high", "high")
EXTRA = ("n_concepts", "n_high", "whitelist", "number_bonus")


def feature_names(concepts: list[dict]) -> list[str]:
    names = sorted({row["concept"] for row in concepts})
    return names + list(EXTRA)


def concept_weights(text: str, concepts: list[dict]) -> dict[str, int]:
    weights: dict[str, int] = {}
    for hit in find_concepts(text, concepts):
        concept = hit["concept"]
        weight = hit["weight"]
        if concept not in weights or weight > weights[concept]:
            weights[concept] = weight
    return weights


def feature_vector(
    text: str,
    concepts: list[dict],
    digits: set[str],
    rules: list[dict],
    names: list[str],
) -> tuple[list[float], dict[str, int]]:
    weights = concept_weights(text, concepts)
    high = sum(1 for weight in weights.values() if weight >= HIGH_CONCEPT_WEIGHT)
    values = {name: weights.get(name, 0) / 100 for name in names if name not in EXTRA}
    values["n_concepts"] = min(len(weights) / 4, 1.0)
    values["n_high"] = min(high / 3, 1.0)
    values["whitelist"] = 1.0 if whitelist_hit(text, digits) else 0.0
    bonus_cap = NUMBER_BONUS_CAP or 1
    values["number_bonus"] = number_bonus(text, rules, digits) / bonus_cap
    return [float(values.get(name, 0.0)) for name in names], weights


def load_model(path: Path = MODEL_PATH) -> dict:
    with path.open(encoding="utf-8") as handle:
        model = json.load(handle)
    if model.get("type") != "logistic_regression":
        raise ValueError("unsupported layer2 model")
    if len(model["features"]) != len(model["coef"]):
        raise ValueError("layer2 feature and coef length mismatch")
    return model


def sigmoid(value: float) -> float:
    if value >= 0:
        exp = math.exp(-value)
        return 1.0 / (1.0 + exp)
    exp = math.exp(value)
    return exp / (1.0 + exp)


def proba(vector: list[float], model: dict) -> float:
    total = float(model["intercept"])
    for weight, value in zip(model["coef"], vector):
        total += float(weight) * value
    return sigmoid(total)


def score_text(
    text: str,
    concepts: list[dict],
    digits: set[str],
    rules: list[dict],
    model: dict,
) -> dict:
    vector, weights = feature_vector(text, concepts, digits, rules, model["features"])
    raw = proba(vector, model)
    threshold = float(model["threshold"])
    strongest = max(weights.values()) if weights else 0
    count = len(weights)
    official = whitelist_hit(text, digits)
    score = raw * 100
    if official:
        score = min(score * WHITELIST_FACTOR, WHITELIST_CAP)
        risk = "低"
    elif count <= 1:
        if count == 1 and strongest >= HIGH_CONCEPT_WEIGHT and raw >= threshold:
            score = min(max(score, MED_SCORE), SINGLE_STRONG_SCORE)
            risk = "中"
        else:
            score = min(score * 0.5 if count == 1 else score, SINGLE_WEAK_CAP)
            risk = "低"
    elif raw >= threshold and strongest >= HIGH_CONCEPT_WEIGHT:
        score = min(max(score, HIGH_SCORE), 100.0)
        risk = "高"
    elif raw >= threshold * 0.75:
        score = min(max(score, MED_SCORE), HIGH_SCORE - 1)
        risk = "中"
    else:
        score = min(score, MED_SCORE - 1)
        risk = "低"
    ordered = sorted(weights, key=lambda concept: weights[concept], reverse=True)
    return {
        "score": round(score, 1),
        "risk": risk,
        "proba": round(raw, 4),
        "concepts": ordered,
        "whitelist": official,
        "display": display_band(risk, round(score, 1)),
    }


def display_band(risk: str, score: float) -> str:
    if risk == "高":
        return "high"
    if risk == "中":
        return "medium_high" if score >= 60 else "medium"
    if score >= SINGLE_WEAK_CAP:
        return "low_medium"
    return "low"


def parse_expected(raw: str) -> set[str]:
    return {part.strip() for part in (raw or "").split(";") if part.strip()}


def observed_concepts(result: dict) -> set[str]:
    found = set(result["concepts"])
    if result.get("whitelist"):
        found.add("WHITELIST")
    return found


def load_hit_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [name for name in HIT_COLUMNS if name not in (reader.fieldnames or [])]
        if missing:
            raise ValueError("missing columns: " + ", ".join(missing))
        rows = []
        for row in reader:
            if (row.get("sentence") or "").strip():
                rows.append(row)
        return rows


def resolve_test_path(raw: str) -> Path:
    path = Path(raw)
    if path.is_file():
        return path
    rooted = ROOT / raw
    if rooted.is_file():
        return rooted
    return path


def run_concept_hit_test(
    path: Path,
    concepts: list[dict],
    digits: set[str],
    rules: list[dict],
    model: dict,
) -> int:
    if not path.is_file():
        raise SystemExit(f"missing {path}")
    known = {row["concept"] for row in concepts}
    rows = load_hit_rows(path)
    concept_ok = 0
    display_ok = 0
    both_ok = 0
    unknown: set[str] = set()
    for row in rows:
        sentence = row["sentence"].strip()
        result = score_text(sentence, concepts, digits, rules, model)
        expected = parse_expected(row.get("expected_concepts") or "")
        expected_display = (row.get("expected_display") or "").strip()
        found = observed_concepts(result)
        band = result["display"]
        missing_names = sorted(expected - found)
        extra_names = sorted(found - expected)
        for name in missing_names:
            if name != "WHITELIST" and name not in known:
                unknown.add(name)
        concepts_pass = not missing_names and not extra_names
        display_pass = expected_display in DISPLAYS and band == expected_display
        concept_ok += int(concepts_pass)
        display_ok += int(display_pass)
        both_ok += int(concepts_pass and display_pass)
        detail = "-"
        if not concepts_pass or not display_pass:
            parts = []
            if missing_names:
                shown = [name + ("*" if name in unknown else "") for name in missing_names]
                parts.append("missing " + ",".join(shown))
            if extra_names:
                parts.append("extra " + ",".join(extra_names))
            if not display_pass:
                parts.append(f"display {band}!={expected_display or '-'}")
            detail = "; ".join(parts)
        got = ",".join(result["concepts"]) or "-"
        if result["whitelist"]:
            got = "WHITELIST" if not result["concepts"] else got + ",WHITELIST"
        mark = "ok" if concepts_pass and display_pass else "FAIL"
        row_id = (row.get("id") or "").strip() or "-"
        print(f"{mark}\t{row_id}\t{band}\t{got}\t{detail}\t{sentence}")
    total = len(rows)
    print(f"{total} rows: concepts {concept_ok}/{total}, display {display_ok}/{total}, both {both_ok}/{total}")
    if unknown:
        print("not in lexicon: " + ",".join(sorted(unknown)))
    print("concept-hit check only; not a Hong Kong accuracy figure")
    return 0 if both_ok == total and total else 1


def main() -> int:
    if not MODEL_PATH.exists():
        raise SystemExit(f"missing {MODEL_PATH}; run train_layer2.py")
    concepts, digits, rules = load_all()
    model = load_model()
    args = sys.argv[1:]
    if args and (args[0] in {"--test", "-t"} or args[0].endswith(".csv")):
        raw = str(HIT_TEST_PATH) if args[0] in {"--test", "-t"} else args[0]
        return run_concept_hit_test(resolve_test_path(raw), concepts, digits, rules, model)
    cases = [
        "請致電18222或999查詢",
        "公安 警察 錢",
        "我是公安，請把錢轉入安全帳戶並立即轉帳",
        "你好，我想問下銀行理財",
        "銀行",
        "This is the police department. You are involved in money laundering. Transfer the payment now.",
    ]
    for text in cases:
        result = score_text(text, concepts, digits, rules, model)
        concepts_text = ",".join(result["concepts"]) or "-"
        print(f"{result['risk']}\t{result['score']:.1f}\t{result['proba']:.3f}\t{concepts_text}\t{text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
