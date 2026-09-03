"""
Boilerplate phrase analysis.

Finds repeated multi-word phrases across the corpus and reports:
  - Which phrases appear in many tickets
  - How many distinct L3 classes they span (a truly generic phrase spans all classes)
  - What % of the corpus contains each phrase
  - Whether phrases are class-discriminative or class-neutral

Usage:
    python scripts/boilerplate_analysis.py
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[1]
CLASSIFICATION_ROOT = REPO_ROOT.parent / "arabic-itsm-classification"
TRAIN = CLASSIFICATION_ROOT / "data/processed/train.csv"
TEST = CLASSIFICATION_ROOT / "data/processed/test.csv"
VAL = CLASSIFICATION_ROOT / "data/processed/val.csv"
OUTPUT = REPO_ROOT / "analysis/boilerplate_report.json"

MIN_TICKETS  = 50    # phrase must appear in at least this many tickets
NGRAM_SIZES  = [5, 6, 7, 8]   # word n-gram lengths to check


def word_ngrams(text: str, n: int) -> list[str]:
    tokens = text.split()
    return [" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def main():
    dfs = [pd.read_csv(p) for p in [TRAIN, VAL, TEST]]
    df = pd.concat(dfs, ignore_index=True)
    df["text"] = (df["description_ar"].fillna("") + " " + df["title_ar"].fillna("")).str.strip()
    n_total = len(df)

    print(f"Corpus: {n_total} tickets")

    # Count phrase occurrences: phrase -> list of (ticket_idx, l3_label)
    phrase_tickets  = defaultdict(set)   # phrase -> set of ticket indices
    phrase_l3       = defaultdict(set)   # phrase -> set of L3 labels
    phrase_l1       = defaultdict(set)   # phrase -> set of L1 labels

    for idx, row in df.iterrows():
        text = row["text"]
        l3   = row.get("category_level_3", "?")
        l1   = row.get("category_level_1", "?")
        seen = set()
        for n in NGRAM_SIZES:
            for phrase in word_ngrams(text, n):
                if phrase not in seen:
                    phrase_tickets[phrase].add(idx)
                    phrase_l3[phrase].add(l3)
                    phrase_l1[phrase].add(l1)
                    seen.add(phrase)

        if idx % 1000 == 0:
            print(f"  Processed {idx}/{n_total}...", end="\r")

    print(f"\nTotal unique phrases found: {len(phrase_tickets):,}")

    # Filter: only phrases appearing in >= MIN_TICKETS tickets
    frequent = {
        p: {
            "n_tickets":   len(phrase_tickets[p]),
            "pct_corpus":  round(len(phrase_tickets[p]) / n_total * 100, 1),
            "n_l3_classes": len(phrase_l3[p]),
            "n_l1_classes": len(phrase_l1[p]),
            "l1_classes":  sorted(phrase_l1[p]),
        }
        for p in phrase_tickets
        if len(phrase_tickets[p]) >= MIN_TICKETS
    }

    # Sort by n_l3_classes desc (most generic first), then n_tickets desc
    ranked = sorted(
        frequent.items(),
        key=lambda x: (-x[1]["n_l3_classes"], -x[1]["n_tickets"]),
    )

    # Deduplicate: if a shorter phrase is a substring of a more common longer phrase,
    # prefer the longer phrase (suppress the shorter sub-phrases)
    final = []
    suppressed = set()
    for phrase, stats in ranked:
        if any(phrase in kept for kept in suppressed):
            continue
        final.append((phrase, stats))
        suppressed.add(phrase)
        if len(final) >= 30:
            break

    print(f"\nTop boilerplate phrases (appearing in >= {MIN_TICKETS} tickets):")
    print(f"{'Phrase':<60}  Tickets  %corpus  L3 span  L1 span")
    print("-" * 100)
    for phrase, s in final[:20]:
        print(
            f"{phrase[:58]:<60}  {s['n_tickets']:>6}   {s['pct_corpus']:>5}%"
            f"   {s['n_l3_classes']:>4}/48   {s['n_l1_classes']:>2}/6"
        )

    # Summary statistics
    generic   = [p for p, s in frequent.items() if s["n_l3_classes"] >= 40]
    moderate  = [p for p, s in frequent.items() if 20 <= s["n_l3_classes"] < 40]
    specific  = [p for p, s in frequent.items() if s["n_l3_classes"] < 20]

    # Tickets containing at least one fully generic phrase (spans all 6 L1)
    generic_all_l1 = [p for p, s in frequent.items() if s["n_l1_classes"] == 6]
    affected_tickets = set()
    for p in generic_all_l1:
        affected_tickets.update(phrase_tickets[p])

    print(f"\n=== Summary ===")
    print(f"Frequent phrases (>={MIN_TICKETS} tickets): {len(frequent)}")
    print(f"  Cross-all-L3 (spans >=40 L3 classes):    {len(generic)}")
    print(f"  Moderately generic (20-39 L3 classes):    {len(moderate)}")
    print(f"  Category-specific (<20 L3 classes):       {len(specific)}")
    print(f"Tickets containing >=1 fully generic phrase (all 6 L1): "
          f"{len(affected_tickets)} / {n_total} ({len(affected_tickets)/n_total*100:.1f}%)")

    result = {
        "corpus_size": n_total,
        "min_ticket_threshold": MIN_TICKETS,
        "n_frequent_phrases": len(frequent),
        "cross_all_l3_phrases": len(generic),
        "moderately_generic_phrases": len(moderate),
        "category_specific_phrases": len(specific),
        "tickets_with_generic_phrase": len(affected_tickets),
        "pct_tickets_with_generic_phrase": round(len(affected_tickets) / n_total * 100, 1),
        "top_phrases": [
            {"phrase": p, **s} for p, s in final[:30]
        ],
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nFull report saved to: {OUTPUT}")


if __name__ == "__main__":
    main()
