import json
import glob
import argparse
import os
from datetime import datetime
from typing import Dict, Any, List, Tuple
import pandas as pd

# ---------- CLI ----------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate and merge Arabic ITSM JSONL parts into a clean dataset."
    )
    parser.add_argument(
        "--taxonomy", default="taxonomy_itsm_v1.json",
        help="Path to taxonomy JSON file (default: taxonomy_itsm_v1.json)"
    )
    parser.add_argument(
        "--input-glob", default="parts/part_*.jsonl",
        help="Glob pattern for input JSONL part files (default: parts/part_*.jsonl)"
    )
    parser.add_argument(
        "--out-jsonl", default="dataset_clean.jsonl",
        help="Output path for clean JSONL (default: dataset_clean.jsonl)"
    )
    parser.add_argument(
        "--out-csv", default="dataset_clean.csv",
        help="Output path for clean CSV (default: dataset_clean.csv)"
    )
    parser.add_argument(
        "--out-rejected", default="dataset_rejected.jsonl",
        help="Output path for rejected rows JSONL (default: dataset_rejected.jsonl)"
    )
    parser.add_argument(
        "--apply-fixes", action="store_true",
        help="Before building, merge *_fixed.jsonl rows into their original part files, then delete the fixed and rejected files"
    )
    return parser.parse_args()

# ---------- Taxonomy ----------
def load_taxonomy(path: str) -> Tuple[set, Dict[Tuple[str,str,str], Dict[str, Any]]]:
    data = json.load(open(path, "r", encoding="utf-8"))
    allowed_paths = set()
    triple_meta = {}

    for node in data["taxonomy"]:
        l1 = node["l1"]
        l2 = node["l2"]
        for l3 in node["l3"]:
            p = f"{l1} > {l2} > {l3}"
            allowed_paths.add(p)
            triple_meta[(l1, l2, l3)] = node

    return allowed_paths, triple_meta

# ---------- Validation ----------
REQUIRED_KEYS = [
    "ticket_id", "created_at", "updated_at", "channel", "model",
    "dialect", "title_ar", "description_ar",
    "category_level_1", "category_level_2", "category_level_3", "category_path",
    "tags", "labels_json",
    "impact", "urgency", "priority", "sentiment"
]

ALLOWED_CHANNELS = {"email", "portal", "chatbot", "phone"}
ALLOWED_SENTIMENT = {"positive", "neutral", "negative", "mixed"}

def parse_iso(ts: str) -> datetime:
    # Accept ISO strings; raise if invalid
    return datetime.fromisoformat(ts)

def clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))

def compute_priority(impact: int, urgency: int) -> int:
    # Use (a+b+1)//2 for round-half-up; Python's round(4.5)==4 (banker's rounding)
    return clamp((impact + urgency + 1) // 2, 1, 5)

def validate_row(obj: Dict[str, Any], allowed_paths: set) -> List[str]:
    errors = []

    for k in REQUIRED_KEYS:
        if k not in obj:
            errors.append(f"missing:{k}")

    if errors:
        return errors

    # channel
    if obj["channel"] not in ALLOWED_CHANNELS:
        errors.append("bad:channel")

    # sentiment
    if obj["sentiment"] not in ALLOWED_SENTIMENT:
        errors.append("bad:sentiment")

    # impact/urgency/priority types
    for k in ["impact", "urgency", "priority"]:
        if not isinstance(obj[k], int):
            errors.append(f"bad:type:{k}")
        else:
            if obj[k] < 1 or obj[k] > 5:
                errors.append(f"bad:range:{k}")

    # timestamps
    try:
        c = parse_iso(obj["created_at"])
        u = parse_iso(obj["updated_at"])
        if u < c:
            errors.append("bad:updated_at<created_at")
    except Exception:
        errors.append("bad:timestamp")

    # category consistency
    l1 = obj["category_level_1"]
    l2 = obj["category_level_2"]
    l3 = obj["category_level_3"]
    path = obj["category_path"]
    expected_path = f"{l1} > {l2} > {l3}"
    if path != expected_path:
        errors.append("bad:category_path_mismatch")

    if path not in allowed_paths:
        errors.append("bad:category_not_allowed")

    # tags
    if not isinstance(obj["tags"], list) or not all(isinstance(x, str) for x in obj["tags"]):
        errors.append("bad:tags")

    # labels_json
    lj = obj["labels_json"]
    if not isinstance(lj, dict):
        errors.append("bad:labels_json_type")
    else:
        for k in ["l1", "l2", "l3", "tags"]:
            if k not in lj:
                errors.append(f"bad:labels_json_missing:{k}")

    # priority rule
    if isinstance(obj["impact"], int) and isinstance(obj["urgency"], int) and isinstance(obj["priority"], int):
        expected_pr = compute_priority(obj["impact"], obj["urgency"])
        if obj["priority"] != expected_pr:
            errors.append("bad:priority_rule")

    return errors

# ---------- Apply fixes ----------
def apply_fixes(input_glob: str, rejected_path: str):
    """Merge *_fixed.jsonl back into originals, then delete fixed + rejected files."""
    parts_dir = os.path.dirname(input_glob) or "."
    fixed_files = sorted(glob.glob(os.path.join(parts_dir, "*_fixed.jsonl")))
    if not fixed_files:
        print("No *_fixed.jsonl files found, nothing to apply.")
        return

    for fixed_path in fixed_files:
        # parts/part_001_fixed.jsonl -> parts/part_001.jsonl
        base = fixed_path.rsplit("_fixed.jsonl", 1)[0] + ".jsonl"
        if not os.path.exists(base):
            print(f"Warning: no original found for {fixed_path}, skipping")
            continue

        # Build replacement map: ticket_id -> fixed line
        replacements = {}
        with open(fixed_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    replacements[obj["ticket_id"]] = line
                except Exception:
                    pass

        # Read original, replace rows whose ticket_id has a fix
        merged = []
        with open(base, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    tid = obj.get("ticket_id")
                    if tid in replacements:
                        merged.append(replacements.pop(tid))
                    else:
                        merged.append(line)
                except Exception:
                    merged.append(line)

        # Append any fixed rows with new ticket_ids
        for line in replacements.values():
            merged.append(line)

        # Write merged back to original
        with open(base, "w", encoding="utf-8") as f:
            for line in merged:
                f.write(line + "\n")

        os.remove(fixed_path)
        print(f"Merged {fixed_path} -> {base}")

    # Delete stale rejected file
    if os.path.exists(rejected_path):
        os.remove(rejected_path)
        print(f"Deleted {rejected_path}")

# ---------- Main ----------
def main():
    args = parse_args()

    if args.apply_fixes:
        apply_fixes(args.input_glob, args.out_rejected)

    allowed_paths, _ = load_taxonomy(args.taxonomy)

    # Read all partial jsonl files
    files = sorted(glob.glob(args.input_glob))
    if not files:
        raise SystemExit(f"No files matched: {args.input_glob}")

    seen_ids = set()
    cleaned: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []

    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    rejected.append({"source": fp, "line": line_no, "reason": ["bad:json_parse"], "raw": line})
                    continue

                errs = validate_row(obj, allowed_paths)

                # Deduplicate ticket_id
                tid = obj.get("ticket_id")
                if tid in seen_ids:
                    errs.append("bad:duplicate_ticket_id")

                # Auto-fix priority when it's the only error
                if errs == ["bad:priority_rule"] and isinstance(obj.get("impact"), int) and isinstance(obj.get("urgency"), int):
                    obj["priority"] = compute_priority(obj["impact"], obj["urgency"])
                    errs = []

                if errs:
                    rejected.append({"source": fp, "line": line_no, "reason": errs, "ticket": obj})
                    continue

                seen_ids.add(tid)

                # Make tags stable (trim + lower for english tags)
                obj["tags"] = [t.strip() for t in obj["tags"] if t and str(t).strip()]

                cleaned.append(obj)

    # Write clean JSONL
    with open(args.out_jsonl, "w", encoding="utf-8") as f:
        for obj in cleaned:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    # Write CSV (flatten labels_json to string)
    df = pd.DataFrame(cleaned)
    df["labels_json"] = df["labels_json"].apply(lambda x: json.dumps(x, ensure_ascii=False))
    df["tags"] = df["tags"].apply(lambda x: json.dumps(x, ensure_ascii=False))

    # Recommended column order
    col_order = [
        "ticket_id", "created_at", "updated_at", "channel", "model",
        "dialect",
        "title_ar", "description_ar",
        "category_level_1", "category_level_2", "category_level_3", "category_path",
        "tags", "labels_json",
        "impact", "urgency", "priority", "sentiment"
    ]
    df = df[[c for c in col_order if c in df.columns]]

    df.to_csv(args.out_csv, index=False, encoding="utf-8-sig")

    # Write rejected JSONL (or clean up stale file)
    if rejected:
        with open(args.out_rejected, "w", encoding="utf-8") as f:
            for obj in rejected:
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    elif os.path.exists(args.out_rejected):
        os.remove(args.out_rejected)

    print(f"Clean rows: {len(cleaned)}")
    print(f"Rejected rows: {len(rejected)}")
    if rejected:
        print(f"Rejected rows written to: {args.out_rejected}")
        print("\n--- Rejected rows (id, cause) ---")
        for r in rejected:
            row_id = r.get("ticket", {}).get("ticket_id") or f"{r.get('source', '?')}:{r.get('line', '?')}"
            causes = ", ".join(r.get("reason", []))
            print(f"{row_id}\t{causes}")

    # Optional: print allowed paths for prompt pasting
    print("\n--- Allowed category paths (copy into prompt) ---")
    for p in sorted(allowed_paths):
        print(p)

if __name__ == "__main__":
    main()

