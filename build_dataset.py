import json
import glob
import re
from datetime import datetime
from typing import Dict, Any, List, Tuple
import pandas as pd

# ---------- Config ----------
TAXONOMY_PATH = "taxonomy_itsm.json"
INPUT_GLOB = "parts/part_*.jsonl"     # folder for partial generations
OUT_JSONL = "dataset_clean.jsonl"
OUT_CSV = "dataset_clean.csv"

# ---------- Arabic preprocessing (script-derived) ----------
_AR_DIACRITICS = re.compile(r"[\u0617-\u061A\u064B-\u0652\u0657-\u065F\u0670]")
_AR_TATWEEL = "\u0640"

def preprocess_ar(text: str) -> str:
    if text is None:
        return ""
    t = str(text)

    # remove tatweel & diacritics
    t = t.replace(_AR_TATWEEL, "")
    t = _AR_DIACRITICS.sub("", t)

    # normalize common Arabic variants
    t = t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    t = t.replace("ى", "ي")
    t = t.replace("ؤ", "و").replace("ئ", "ي")
    t = t.replace("ة", "ه")  # optional; you may comment this out if you prefer keeping ة

    # collapse elongation like حلوووو -> حلوو (keep slight emphasis)
    t = re.sub(r"(.)\1{3,}", r"\1\1", t)

    # normalize whitespace
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = t.strip()
    return t

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
    return clamp(int(round((impact + urgency) / 2)), 1, 5)

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

# ---------- Main ----------
def main():
    allowed_paths, _ = load_taxonomy(TAXONOMY_PATH)

    # Read all partial jsonl files
    files = sorted(glob.glob(INPUT_GLOB))
    if not files:
        raise SystemExit(f"No files matched: {INPUT_GLOB}")

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

                if errs:
                    rejected.append({"source": fp, "line": line_no, "reason": errs, "ticket_id": tid})
                    continue

                seen_ids.add(tid)

                # Derived fields (script-derived)
                obj["preprocessed_ar"] = preprocess_ar(obj["title_ar"] + "\n" + obj["description_ar"])

                # Make tags stable (trim + lower for english tags)
                obj["tags"] = [t.strip() for t in obj["tags"] if t and str(t).strip()]

                cleaned.append(obj)

    # Write clean JSONL
    with open(OUT_JSONL, "w", encoding="utf-8") as f:
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
        "title_ar", "description_ar", "preprocessed_ar",
        "category_level_1", "category_level_2", "category_level_3", "category_path",
        "tags", "labels_json",
        "impact", "urgency", "priority", "sentiment"
    ]
    df = df[[c for c in col_order if c in df.columns]]

    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    print(f"✅ Clean rows: {len(cleaned)}")
    print(f"❌ Rejected rows: {len(rejected)}")
    if rejected:
        # small sample report
        sample = rejected[:10]
        print("\nSample rejected:")
        for r in sample:
            print(r)

    # Optional: print allowed paths for prompt pasting
    print("\n--- Allowed category paths (copy into prompt) ---")
    for p in sorted(allowed_paths):
        print(p)

if __name__ == "__main__":
    main()

