"""
Near-duplicate analysis across train/test splits.

Computes TF-IDF cosine similarity between each test ticket and its nearest
neighbor in the training set. Reports the distribution of nearest-neighbor
scores and flags any pairs above a configurable threshold.

Usage:
    python scripts/near_duplicate_analysis.py \
        --train data/processed/train.csv \
        --test  data/processed/test.csv \
        --threshold 0.9 \
        --output results/near_duplicate_report.json
"""

import argparse
import json
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def load_text(path: str) -> pd.Series:
    df = pd.read_csv(path)
    # Combine title and description, same as model input
    return (df["title_ar"].fillna("") + " " + df["description_ar"].fillna("")).str.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default="D:/AI/arabic-itsm-classification/data/processed/train.csv")
    parser.add_argument("--test",  default="D:/AI/arabic-itsm-classification/data/processed/test.csv")
    parser.add_argument("--threshold", type=float, default=0.9)
    parser.add_argument("--output", default="D:/AI/arabic-itsm-paper/results/near_duplicate_report.json")
    args = parser.parse_args()

    print("Loading data...")
    train_texts = load_text(args.train)
    test_texts  = load_text(args.test)
    print(f"  Train: {len(train_texts)} tickets")
    print(f"  Test:  {len(test_texts)} tickets")

    print("Fitting TF-IDF vectorizer (word + char n-grams)...")
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 4),
        max_features=50_000,
        sublinear_tf=True,
    )
    all_texts = pd.concat([train_texts, test_texts], ignore_index=True)
    vectorizer.fit(all_texts)

    train_matrix = vectorizer.transform(train_texts)
    test_matrix  = vectorizer.transform(test_texts)

    print("Computing nearest-neighbor similarities (test vs train)...")
    # Process in batches to avoid memory issues
    batch_size = 200
    nn_scores = []
    nn_indices = []

    for i in range(0, len(test_texts), batch_size):
        batch = test_matrix[i : i + batch_size]
        sims = cosine_similarity(batch, train_matrix)
        nn_scores.extend(sims.max(axis=1).tolist())
        nn_indices.extend(sims.argmax(axis=1).tolist())
        print(f"  Processed {min(i + batch_size, len(test_texts))}/{len(test_texts)}", end="\r")

    print()
    nn_scores = np.array(nn_scores)

    flagged = [(int(ti), int(nn_indices[ti]), float(nn_scores[ti]))
               for ti in range(len(nn_scores)) if nn_scores[ti] >= args.threshold]

    report = {
        "threshold": args.threshold,
        "n_test": len(test_texts),
        "n_train": len(train_texts),
        "nn_similarity": {
            "mean":   float(nn_scores.mean()),
            "median": float(np.median(nn_scores)),
            "max":    float(nn_scores.max()),
            "p95":    float(np.percentile(nn_scores, 95)),
            "p99":    float(np.percentile(nn_scores, 99)),
        },
        "n_flagged_above_threshold": len(flagged),
        "flagged_pairs": [
            {
                "test_idx": ti,
                "train_idx": tri,
                "similarity": sim,
                "test_text":  test_texts.iloc[ti][:200],
                "train_text": train_texts.iloc[tri][:200],
            }
            for ti, tri, sim in flagged[:20]  # cap at 20 examples
        ],
    }

    import os
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n=== Near-Duplicate Analysis Results ===")
    print(f"Nearest-neighbor similarity (test->train):")
    print(f"  Mean:   {report['nn_similarity']['mean']:.4f}")
    print(f"  Median: {report['nn_similarity']['median']:.4f}")
    print(f"  P95:    {report['nn_similarity']['p95']:.4f}")
    print(f"  P99:    {report['nn_similarity']['p99']:.4f}")
    print(f"  Max:    {report['nn_similarity']['max']:.4f}")
    print(f"Pairs above threshold ({args.threshold}): {len(flagged)}")
    print(f"Report saved to: {args.output}")


if __name__ == "__main__":
    main()
