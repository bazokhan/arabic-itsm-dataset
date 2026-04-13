#!/usr/bin/env python3
"""Validate exact taxonomy counts for the Arabic ITSM dataset.

This script reads dataset_clean.csv, reports raw corpus counts, applies the
paper's exact deduplication rule on (title_ar, description_ar), and then prints
exact L1/L2/L3 counts for the deduplicated corpus in taxonomy order.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate raw and deduplicated taxonomy counts from dataset_clean.csv."
        )
    )
    parser.add_argument(
        "--dataset",
        default="dataset_clean.csv",
        help="Path to dataset CSV (default: dataset_clean.csv)",
    )
    parser.add_argument(
        "--taxonomy",
        default="taxonomy_itsm_v1.json",
        help="Path to taxonomy JSON (default: taxonomy_itsm_v1.json)",
    )
    return parser.parse_args()


def load_rows(dataset_path: Path) -> list[dict[str, str]]:
    with dataset_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def dedupe_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, str]] = []
    for row in rows:
        key = (row["title_ar"], row["description_ar"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def load_taxonomy_rows(taxonomy_path: Path) -> list[tuple[str, str, str]]:
    payload = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    ordered_rows: list[tuple[str, str, str]] = []
    for node in payload["taxonomy"]:
        l1 = node["l1"]
        l2 = node["l2"]
        for l3 in node["l3"]:
            ordered_rows.append((l1, l2, l3))
    return ordered_rows


def print_section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def print_kv(label: str, value: object) -> None:
    print(f"{label:<28} {value}")


def main() -> int:
    args = parse_args()
    dataset_path = Path(args.dataset).resolve()
    taxonomy_path = Path(args.taxonomy).resolve()

    rows = load_rows(dataset_path)
    deduped_rows = dedupe_rows(rows)
    duplicate_count = len(rows) - len(deduped_rows)

    l1_raw = Counter(row["category_level_1"] for row in rows)
    l1_dedup = Counter(row["category_level_1"] for row in deduped_rows)
    l2_dedup = Counter(row["category_level_2"] for row in deduped_rows)
    l3_dedup = Counter(row["category_level_3"] for row in deduped_rows)
    taxonomy_rows = load_taxonomy_rows(taxonomy_path)

    print("Arabic ITSM Dataset Count Validation")
    print("===================================")
    print_kv("Dataset CSV", dataset_path)
    print_kv("Taxonomy JSON", taxonomy_path)

    print_section("Corpus Summary")
    print_kv("Raw rows", len(rows))
    print_kv("Exact duplicates removed", duplicate_count)
    print_kv("Deduplicated rows", len(deduped_rows))
    print_kv("Unique L1 classes", len(l1_dedup))
    print_kv("Unique L2 classes", len(l2_dedup))
    print_kv("Unique L3 classes", len(l3_dedup))

    print_section("L1 Counts (Deduplicated)")
    for label in sorted(l1_dedup):
        print(f"{label:<16} {l1_dedup[label]:>5}")

    print_section("L2 Counts (Deduplicated)")
    for label in sorted(l2_dedup):
        print(f"{label:<20} {l2_dedup[label]:>5}")

    print_section("L3 Leaf Counts (Deduplicated, Taxonomy Order)")
    print(f"{'L1':<10} {'L2':<20} {'L3':<22} {'Exact N':>7}")
    print(f"{'-' * 10} {'-' * 20} {'-' * 22} {'-' * 7}")
    for l1, l2, l3 in taxonomy_rows:
        print(f"{l1:<10} {l2:<20} {l3:<22} {l3_dedup[l3]:>7}")

    print_section("L1 Counts (Raw 10,000-row Release)")
    for label in sorted(l1_raw):
        print(f"{label:<16} {l1_raw[label]:>5}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
