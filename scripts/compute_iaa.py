"""
Compute inter-annotator agreement (IAA) from completed annotation spreadsheets.

Computes:
  - Weighted Cohen's kappa for naturalness (ordinal 1-5, linear weights)
  - Cohen's kappa for l1_correct, l2_correct, l3_correct (nominal Y/N/U)
  - Raw agreement rates and per-L1 breakdown

Usage:
    python scripts/compute_iaa.py \
        --rater_a annotation/annotation_rater_A.csv \
        --rater_b annotation/annotation_rater_B.csv \
        --output  annotation/iaa_results.json
"""

import argparse
import json
import os
import pandas as pd
from sklearn.metrics import cohen_kappa_score


def weighted_kappa_ordinal(a, b, min_val=1, max_val=5):
    """Cohen's kappa with linear weights for ordinal scale."""
    labels = list(range(min_val, max_val + 1))
    return cohen_kappa_score(a, b, labels=labels, weights="linear")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rater_a", required=True)
    parser.add_argument("--rater_b", required=True)
    parser.add_argument("--output", default="assets/iaa_results.json")
    args = parser.parse_args()

    ra = pd.read_csv(args.rater_a, encoding="utf-8-sig")
    rb = pd.read_csv(args.rater_b, encoding="utf-8-sig")

    assert len(ra) == len(rb), "Rater files must have the same number of rows."
    assert (ra["ticket_id"] == rb["ticket_id"]).all(), \
        "Ticket IDs must match and be in the same order."

    nat_col = "naturalness (1-5)"
    lc_cols = {
        "L1": "l1_correct (Y/N/U)",
        "L2": "l2_correct (Y/N/U)",
        "L3": "l3_correct (Y/N/U)",
    }

    # ── Naturalness ───────────────────────────────────────────────────────────
    valid_nat = ra[nat_col].notna() & rb[nat_col].notna()
    nat_a = ra.loc[valid_nat, nat_col].astype(int)
    nat_b = rb.loc[valid_nat, nat_col].astype(int)
    kappa_nat       = weighted_kappa_ordinal(nat_a, nat_b)
    mean_nat_pooled = float(pd.concat([nat_a, nat_b]).mean())
    pct_nat_4_or_5  = float(((nat_a >= 4) & (nat_b >= 4)).mean())

    # Per-L1 naturalness breakdown
    per_l1 = {}
    if "L1_label" in ra.columns:
        for l1 in sorted(ra["L1_label"].dropna().unique()):
            mask     = (ra["L1_label"] == l1) & valid_nat
            sub_mask = mask[valid_nat]
            if sub_mask.sum() > 0:
                per_l1[l1] = {
                    "n": int(sub_mask.sum()),
                    "mean_naturalness": round(
                        float(pd.concat([nat_a[sub_mask], nat_b[sub_mask]]).mean()), 2
                    ),
                }

    # ── Label correctness per level ───────────────────────────────────────────
    label_results = {}
    for level, col in lc_cols.items():
        if col not in ra.columns:
            continue
        valid = ra[col].notna() & rb[col].notna()
        a = ra.loc[valid, col].str.strip().str.upper()
        b = rb.loc[valid, col].str.strip().str.upper()
        kappa = cohen_kappa_score(a, b)
        agree = float((a == b).mean())
        pct_both_y = float(((a == "Y") & (b == "Y")).mean())
        label_results[level] = {
            "n":                 int(valid.sum()),
            "cohen_kappa":       round(kappa, 4),
            "raw_agreement_pct": round(agree * 100, 1),
            "pct_both_correct":  round(pct_both_y * 100, 1),
        }

    # ── Assemble & save ───────────────────────────────────────────────────────
    results = {
        "n_annotated": int(valid_nat.sum()),
        "naturalness": {
            "weighted_kappa_linear": round(kappa_nat, 4),
            "mean_pooled":           round(mean_nat_pooled, 3),
            "pct_both_rated_4_or_5": round(pct_nat_4_or_5 * 100, 1),
        },
        "label_correctness_by_level": label_results,
        "per_l1_naturalness": per_l1,
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("=== Inter-Annotator Agreement Results ===")
    print(f"Naturalness (linear-weighted kappa): {kappa_nat:.3f}")
    print(f"  Mean naturalness (pooled):  {mean_nat_pooled:.2f} / 5")
    print(f"  Both rated >= 4:            {pct_nat_4_or_5*100:.1f}%")
    print()
    for level, s in label_results.items():
        print(f"Label Correct {level}  kappa={s['cohen_kappa']:.3f}  "
              f"agree={s['raw_agreement_pct']}%  both-Y={s['pct_both_correct']}%")
    print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
