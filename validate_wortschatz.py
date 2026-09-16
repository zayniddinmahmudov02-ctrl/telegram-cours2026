"""Standalone validator for Wortschatz.csv — run after any edit to the file.

Checks: duplicate words (case/whitespace/Unicode-NFC-insensitive), invalid
type/level, empty translation/example, required fields per type (Nomen:
article/plural, Verb: preteritum/partizip_ii, Adjektiv: positiv/komparativ/
superlativ), malformed rows (wrong column count), UTF-8 integrity, and
overall CSV structural validity.
"""
import csv
import sys
import unicodedata
from collections import Counter

CSV_PATH = "Wortschatz.csv"
VALID_LEVELS = {"A1", "A2", "B1", "B2", "C1", "C2"}
VALID_TYPES = {"Nomen", "Verb", "Adjektiv"}
VALID_ARTICLES = {"der", "die", "das"}
EXPECTED_COLUMNS = [
    "word", "type", "level", "translation", "article", "plural",
    "preteritum", "partizip_ii", "positiv", "komparativ", "superlativ", "example",
]


def normalize(word: str) -> str:
    """case-insensitive, whitespace-trimmed, Unicode-NFC-normalized key for dedup."""
    return unicodedata.normalize("NFC", word.strip().lower())


def validate(path: str = CSV_PATH, max_printed_errors: int = 200) -> bool:
    # ---- UTF-8 integrity check (strict decode of raw bytes) ----
    with open(path, "rb") as f:
        raw = f.read()
    try:
        text = raw.decode("utf-8", errors="strict")
        utf8_ok = True
    except UnicodeDecodeError as e:
        text = raw.decode("utf-8", errors="replace")
        utf8_ok = False
        utf8_error = str(e)

    # ---- malformed-row / column-count check via plain csv.reader ----
    lines = text.splitlines()
    raw_reader = csv.reader(lines)
    all_rows = list(raw_reader)
    header = all_rows[0] if all_rows else []
    col_mismatch = []
    for i, row in enumerate(all_rows[1:], start=2):
        if len(row) != len(EXPECTED_COLUMNS):
            col_mismatch.append((i, len(row)))

    if header != EXPECTED_COLUMNS:
        print(f"COLUMN MISMATCH: expected {EXPECTED_COLUMNS}, got {header}")
        return False

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    errors = []
    error_categories = Counter()

    if not utf8_ok:
        errors.append(f"UTF-8 DECODE ERROR: {utf8_error}")
        error_categories["utf8"] += 1

    for i, cnt in col_mismatch:
        errors.append(f"MALFORMED ROW at line {i}: expected {len(EXPECTED_COLUMNS)} columns, got {cnt}")
        error_categories["malformed_row"] += 1

    seen = {}
    seen_lemma_type = {}  # (normalized_word, type) -> row, catches same lemma re-entered under diff type accidentally twice
    for i, row in enumerate(rows, start=2):
        raw_word = row["word"]
        w = normalize(raw_word)
        if not w:
            errors.append(f"EMPTY word at row {i}")
            error_categories["empty_word"] += 1
            continue
        if w in seen:
            errors.append(f"DUPLICATE word '{raw_word}' at rows {seen[w]} and {i}")
            error_categories["duplicate"] += 1
        else:
            seen[w] = i

        if not row["translation"].strip():
            errors.append(f"EMPTY translation for '{raw_word}' (row {i})")
            error_categories["empty_translation"] += 1

        if not row["example"].strip():
            errors.append(f"EMPTY example for '{raw_word}' (row {i})")
            error_categories["empty_example"] += 1

        if row["level"] not in VALID_LEVELS:
            errors.append(f"INVALID level '{row['level']}' for '{raw_word}' (row {i})")
            error_categories["invalid_level"] += 1

        if row["type"] not in VALID_TYPES:
            errors.append(f"INVALID type '{row['type']}' for '{raw_word}' (row {i})")
            error_categories["invalid_type"] += 1

        if row["type"] == "Nomen":
            if not row["article"].strip():
                errors.append(f"Nomen '{raw_word}' missing article (row {i})")
                error_categories["nomen_missing_article"] += 1
            elif row["article"] not in VALID_ARTICLES:
                errors.append(f"Nomen '{raw_word}' invalid article '{row['article']}' (row {i})")
                error_categories["nomen_invalid_article"] += 1
            if not row["plural"].strip():
                errors.append(f"Nomen '{raw_word}' missing plural (row {i})")
                error_categories["nomen_missing_plural"] += 1

        if row["type"] == "Verb":
            if not row["preteritum"].strip():
                errors.append(f"Verb '{raw_word}' missing preteritum (row {i})")
                error_categories["verb_missing_preteritum"] += 1
            if not row["partizip_ii"].strip():
                errors.append(f"Verb '{raw_word}' missing partizip_ii (row {i})")
                error_categories["verb_missing_partizip_ii"] += 1
            else:
                pz = row["partizip_ii"].strip()
                if not (pz.startswith("hat ") or pz.startswith("ist ")):
                    errors.append(f"Verb '{raw_word}' partizip_ii not in 'hat/ist ...' format: '{pz}' (row {i})")
                    error_categories["verb_partizip_format"] += 1

        if row["type"] == "Adjektiv":
            missing = [c for c in ("positiv", "komparativ", "superlativ") if not row[c].strip()]
            if missing:
                errors.append(f"Adjektiv '{raw_word}' missing {missing} (row {i})")
                error_categories["adjektiv_missing_degree"] += 1
            elif not row["superlativ"].strip().startswith("am "):
                errors.append(f"Adjektiv '{raw_word}' superlativ doesn't start with 'am ': '{row['superlativ']}' (row {i})")
                error_categories["adjektiv_superlativ_format"] += 1

    level_counts = Counter(r["level"] for r in rows)
    type_counts = Counter(r["type"] for r in rows)

    print(f"CSV path: {path}")
    print(f"UTF-8 encoding: {'VALID' if utf8_ok else 'INVALID - ' + utf8_error}")
    print(f"CSV structure: {'VALID' if not col_mismatch else f'INVALID ({len(col_mismatch)} malformed rows)'}")
    print(f"Total rows: {len(rows)}")
    print(f"Unique words: {len(seen)}")
    print("Per level:", dict(sorted(level_counts.items())))
    print("Per type:", dict(type_counts))
    print(f"Duplicate count: {error_categories.get('duplicate', 0)}")
    print(f"Total validation errors: {len(errors)}")
    if error_categories:
        print("Errors by category:")
        for cat, cnt in sorted(error_categories.items(), key=lambda x: -x[1]):
            print(f"  - {cat}: {cnt}")
    if errors:
        print(f"\nFirst {min(max_printed_errors, len(errors))} errors:")
        for e in errors[:max_printed_errors]:
            print(" -", e)

    if errors:
        print("\nVALIDATION FAILED")
        return False

    print("\nVALIDATION PASSED")
    return True


if __name__ == "__main__":
    ok = validate(sys.argv[1] if len(sys.argv) > 1 else CSV_PATH)
    sys.exit(0 if ok else 1)
