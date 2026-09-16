"""Standalone validator for Wortschatz.csv — run after any manual edit to the file.

Checks: no duplicate words, no empty translations, required fields present per
type (Nomen: article/plural, Verb: preteritum/partizip_ii, Adjektiv: positiv/
komparativ/superlativ), level in A1-C2, type in the allowed set, and CSV
structural integrity.
"""
import csv
import sys
from collections import Counter

CSV_PATH = "Wortschatz.csv"
VALID_LEVELS = {"A1", "A2", "B1", "B2", "C1", "C2"}
VALID_TYPES = {"Nomen", "Verb", "Adjektiv"}
EXPECTED_COLUMNS = [
    "word", "type", "level", "translation", "article", "plural",
    "preteritum", "partizip_ii", "positiv", "komparativ", "superlativ", "example",
]


def validate(path: str = CSV_PATH) -> bool:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != EXPECTED_COLUMNS:
            print(f"COLUMN MISMATCH: expected {EXPECTED_COLUMNS}, got {reader.fieldnames}")
            return False
        rows = list(reader)

    errors = []
    seen = {}

    for i, row in enumerate(rows, start=2):
        w = row["word"].strip().lower()
        if not w:
            errors.append(f"EMPTY word at row {i}")
            continue
        if w in seen:
            errors.append(f"DUPLICATE word '{row['word']}' at rows {seen[w]} and {i}")
        else:
            seen[w] = i

        if not row["translation"].strip():
            errors.append(f"EMPTY translation for '{row['word']}' (row {i})")

        if row["level"] not in VALID_LEVELS:
            errors.append(f"INVALID level '{row['level']}' for '{row['word']}' (row {i})")

        if row["type"] not in VALID_TYPES:
            errors.append(f"INVALID type '{row['type']}' for '{row['word']}' (row {i})")

        if row["type"] == "Nomen":
            if not row["article"].strip():
                errors.append(f"Nomen '{row['word']}' missing article (row {i})")
            elif row["article"] not in ("der", "die", "das"):
                errors.append(f"Nomen '{row['word']}' invalid article '{row['article']}' (row {i})")
            if not row["plural"].strip():
                errors.append(f"Nomen '{row['word']}' missing plural (row {i})")

        if row["type"] == "Verb":
            if not row["preteritum"].strip():
                errors.append(f"Verb '{row['word']}' missing preteritum (row {i})")
            if not row["partizip_ii"].strip():
                errors.append(f"Verb '{row['word']}' missing partizip_ii (row {i})")

        if row["type"] == "Adjektiv":
            if not (row["positiv"].strip() and row["komparativ"].strip() and row["superlativ"].strip()):
                errors.append(f"Adjektiv '{row['word']}' missing a degree column (row {i})")

        if not row["example"].strip():
            errors.append(f"EMPTY example for '{row['word']}' (row {i})")

    level_counts = Counter(r["level"] for r in rows)
    type_counts = Counter(r["type"] for r in rows)

    print(f"Total rows: {len(rows)}")
    print(f"Unique words: {len(seen)}")
    print("Per level:", dict(sorted(level_counts.items())))
    print("Per type:", dict(type_counts))
    print(f"Duplicate count: {sum(1 for e in errors if e.startswith('DUPLICATE'))}")
    print(f"Errors: {len(errors)}")
    for e in errors:
        print(" -", e)

    if errors:
        print("\nVALIDATION FAILED")
        return False

    print("\nVALIDATION PASSED")
    return True


if __name__ == "__main__":
    ok = validate(sys.argv[1] if len(sys.argv) > 1 else CSV_PATH)
    sys.exit(0 if ok else 1)
