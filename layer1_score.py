"""Layer-1 text scorer. Advisory warning only, not a legal finding."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "layer1"

HIGH_CONCEPT_WEIGHT = 70
HIGH_SCORE = 80
MED_SCORE = 40
SINGLE_STRONG_SCORE = 50.0
SINGLE_WEAK_CAP = 35.0
WHITELIST_FACTOR = 0.15
WHITELIST_CAP = 25.0
NUMBER_BONUS_CAP = 20
SHORT_WHITELIST = {"999", "1868"}
CALL_HINT = re.compile(r"致電|打|撥|熱線|查詢|call|dial|hotline|緊急", re.IGNORECASE)
SENDER_HINT = re.compile(r"#?\s*ADCC\s*18222", re.IGNORECASE)


def load_concepts(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            surface = (row.get("surface") or "").strip()
            concept = (row.get("concept") or "").strip()
            if not surface or not concept:
                continue
            rows.append(
                {
                    "surface": surface,
                    "lang": (row.get("lang") or "").strip(),
                    "concept": concept,
                    "weight": int(row["weight"]),
                }
            )
    return rows


def load_whitelist(path: Path) -> tuple[set[str], list[str]]:
    digits: set[str] = set()
    senders: list[str] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            raw = (row.get("number") or "").strip()
            if not raw:
                continue
            if re.search(r"[A-Za-z]", raw):
                senders.append(re.sub(r"[^A-Za-z0-9]", "", raw).upper())
                continue
            only = re.sub(r"\D", "", raw)
            if only.startswith("852") and len(only) > 3:
                only = only[3:]
            if only:
                digits.add(only)
    return digits, senders


def load_number_rules(path: Path) -> list[dict]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    rules = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rule_id = (row.get("rule_id") or "").strip()
            if not rule_id:
                continue
            rules.append(
                {
                    "rule_id": rule_id,
                    "kind": (row.get("kind") or "").strip(),
                    "value": int(row["value"]),
                    "weight": int(row["weight"]),
                }
            )
    return rules


def _local_number(token: str) -> str:
    only = re.sub(r"\D", "", token)
    if only.startswith("852") and len(only) > 3:
        return only[3:]
    return only


def whitelist_hit(text: str, digits: set[str]) -> bool:
    if SENDER_HINT.search(text):
        return True
    for match in re.finditer(r"\+?\d[\d\s\-]*\d", text):
        token = match.group()
        only = re.sub(r"\D", "", token)
        local = _local_number(only)
        if local not in digits and only not in digits:
            continue
        if local in SHORT_WHITELIST or only in SHORT_WHITELIST:
            window = text[max(0, match.start() - 12) : match.end() + 6]
            if not token.strip().startswith("+") and not CALL_HINT.search(window):
                continue
        return True
    return False


def extract_numbers(text: str) -> list[str]:
    found = []
    for match in re.finditer(r"\+?\d[\d\s\-]{5,}\d", text):
        raw = match.group()
        only = re.sub(r"\D", "", raw)
        if len(only) < 7:
            continue
        found.append("+" + only if raw.strip().startswith("+") else only)
    return found


def number_bonus(text: str, rules: list[dict], whitelist_digits: set[str]) -> int:
    bonus = 0
    for token in extract_numbers(text):
        plus = token.startswith("+")
        only = token[1:] if plus else token
        local = _local_number(only)
        if only in whitelist_digits or local in whitelist_digits:
            continue
        for rule in rules:
            kind = rule["kind"]
            if kind == "leading_plus" and plus:
                bonus += rule["weight"]
            elif kind == "min_digits" and len(only) >= rule["value"]:
                bonus += rule["weight"]
            elif kind == "exact_digits" and len(only) == rule["value"]:
                bonus += rule["weight"]
    return min(bonus, NUMBER_BONUS_CAP)


def find_concepts(text: str, rows: list[dict]) -> list[dict]:
    occupied = [False] * len(text)
    hits = []
    ordered = sorted(rows, key=lambda row: len(row["surface"]), reverse=True)
    for row in ordered:
        surface = row["surface"]
        if surface.isascii():
            pattern = re.compile(
                rf"(?<![A-Za-z0-9]){re.escape(surface)}(?![A-Za-z0-9])",
                re.IGNORECASE,
            )
            for match in pattern.finditer(text):
                if any(occupied[match.start() : match.end()]):
                    continue
                for index in range(match.start(), match.end()):
                    occupied[index] = True
                hits.append(row)
                break
            continue
        start = 0
        while True:
            found = text.find(surface, start)
            if found < 0:
                break
            end = found + len(surface)
            if not any(occupied[found:end]):
                for index in range(found, end):
                    occupied[index] = True
                hits.append(row)
                break
            start = found + 1
    return hits


def concept_score(weights: dict[str, int]) -> float:
    if not weights:
        return 0.0
    if len(weights) == 1:
        only = next(iter(weights.values()))
        if only >= HIGH_CONCEPT_WEIGHT:
            return SINGLE_STRONG_SCORE
        return min(only * 0.5, SINGLE_WEAK_CAP)
    return float(sum(weights.values()))


def risk_label(score: float, concept_count: int, strongest: int) -> str:
    if score >= HIGH_SCORE and concept_count >= 2 and strongest >= HIGH_CONCEPT_WEIGHT:
        return "高"
    if score >= MED_SCORE:
        return "中"
    return "低"


def score_text(
    text: str,
    concepts: list[dict],
    whitelist_digits: set[str],
    rules: list[dict],
) -> dict:
    hits = find_concepts(text, concepts)
    weights: dict[str, int] = {}
    for hit in hits:
        concept = hit["concept"]
        weight = hit["weight"]
        if concept not in weights or weight > weights[concept]:
            weights[concept] = weight
    score = concept_score(weights) + number_bonus(text, rules, whitelist_digits)
    if whitelist_hit(text, whitelist_digits):
        score = min(score * WHITELIST_FACTOR, WHITELIST_CAP)
    strongest = max(weights.values()) if weights else 0
    ordered = sorted(weights, key=lambda concept: weights[concept], reverse=True)
    return {
        "score": round(score, 1),
        "risk": risk_label(score, len(weights), strongest),
        "concepts": ordered,
    }


def load_all() -> tuple[list[dict], set[str], list[dict]]:
    concepts: list[dict] = []
    for name in ("scam_keywords_zh.csv", "scam_keywords_en.csv"):
        path = DATA_DIR / name
        if path.exists():
            concepts.extend(load_concepts(path))
    digits, _senders = load_whitelist(DATA_DIR / "official_whitelist.csv")
    rules = load_number_rules(DATA_DIR / "number_rules.csv")
    return concepts, digits, rules


def main() -> None:
    concepts, digits, rules = load_all()
    cases = [
        ("請致電18222或999查詢", "低"),
        ("#ADCC18222 防騙提示", "低"),
        ("官方熱線 3423 6611", "低"),
        ("請打81056060", "低"),
        ("熱線 +852-1868", "低"),
        ("我是公安，請把錢轉入安全帳戶並立即轉帳", "高"),
        ("你好，我想問下銀行理財", "低"),
        ("我是公安，轉入安全帳戶，賠償999萬", "高"),
        ("請按1，你的電話2小時內停用", "高"),
        ("This is the police department. You are involved in money laundering. Transfer the payment now.", "高"),
        ("Your prescription is ready for pickup tomorrow.", "低"),
        ("I called the police department about a noise complaint.", "低"),
    ]
    failed = 0
    for text, expected in cases:
        result = score_text(text, concepts, digits, rules)
        concepts_text = ",".join(result["concepts"]) or "-"
        mark = "ok" if result["risk"] == expected else "FAIL"
        if result["risk"] != expected:
            failed += 1
        print(f"{mark}\t{result['risk']}\t{result['score']:.1f}\t{concepts_text}\t{text}")
    bank = score_text("銀行", concepts, digits, rules)
    if bank["risk"] != "低" or bank["score"] >= MED_SCORE:
        failed += 1
        print(f"FAIL\t{bank['risk']}\t{bank['score']:.1f}\t{','.join(bank['concepts'])}\t銀行")
    else:
        print(f"ok\t{bank['risk']}\t{bank['score']:.1f}\t{','.join(bank['concepts'])}\t銀行")
    if failed:
        raise SystemExit(f"{failed} case(s) failed")
    print("all cases passed")


if __name__ == "__main__":
    sys.exit(main())
