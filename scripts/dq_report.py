#!/usr/bin/env python3
import sys, json, statistics, collections, re
from pathlib import Path

def load_taxonomy(path: Path):
    t = json.loads(path.read_text(encoding='utf-8'))
    allowed = set()
    for item in t["taxonomy"]:
        l1=item["l1"]; l2=item["l2"]
        for l3 in item["l3"]:
            allowed.add((l1,l2,l3))
    return allowed

REQ_KEYS = [
    "ticket_id","created_at","updated_at","channel","model","dialect",
    "title_ar","description_ar","category_level_1","category_level_2",
    "category_level_3","category_path","tags","labels_json","impact",
    "urgency","priority","sentiment"
]

CHANNELS = {"email","portal","chatbot","phone"}
SENTIMENTS = {"positive","neutral","negative","mixed"}


def priority_rule(impact:int, urgency:int)->int:
    pr = int((impact+urgency)/2 + 0.5)
    return 1 if pr<1 else 5 if pr>5 else pr


def main():
    if len(sys.argv)<3:
        print("Usage: dq_report.py <JSONL_FILE> <TAXONOMY_JSON> [OUT.txt]", file=sys.stderr)
        sys.exit(2)
    infile = Path(sys.argv[1])
    taxonomy = load_taxonomy(Path(sys.argv[2]))
    outpath = Path(sys.argv[3]) if len(sys.argv)>3 else None

    total=0
    missing_keys=0
    bad_channel=0
    bad_sentiment=0
    bad_priority=0
    bad_catpath=0
    bad_taxonomy=0

    l1_counter=collections.Counter()
    l2_counter=collections.Counter()
    l3_counter=collections.Counter()
    ch_counter=collections.Counter()
    sent_counter=collections.Counter()
    impact_counter=collections.Counter()
    urgency_counter=collections.Counter()
    priority_counter=collections.Counter()

    title_desc_hashes=collections.Counter()
    desc_lengths=[]
    title_lengths=[]

    first_10_bad_priority=[]
    first_10_bad_tax=[]

    with infile.open('r', encoding='utf-8') as f:
        for line in f:
            line=line.strip()
            if not line:
                continue
            total+=1
            try:
                obj=json.loads(line)
            except Exception:
                continue
            # keys
            if any(k not in obj for k in REQ_KEYS):
                missing_keys+=1
            # channel/sentiment
            if obj.get("channel") not in CHANNELS:
                bad_channel+=1
            if obj.get("sentiment") not in SENTIMENTS:
                bad_sentiment+=1
            # priority
            imp=obj.get("impact",0); urg=obj.get("urgency",0)
            pr_calc=priority_rule(int(imp), int(urg))
            if obj.get("priority")!=pr_calc:
                bad_priority+=1
                if len(first_10_bad_priority)<10:
                    first_10_bad_priority.append((obj.get("ticket_id"), imp, urg, obj.get("priority"), pr_calc))
            # taxonomy
            l1=obj.get("category_level_1"); l2=obj.get("category_level_2"); l3=obj.get("category_level_3")
            if (l1,l2,l3) not in taxonomy:
                bad_taxonomy+=1
                if len(first_10_bad_tax)<10:
                    first_10_bad_tax.append((obj.get("ticket_id"), l1,l2,l3))
            # category_path
            cp_expected=f"{l1} > {l2} > {l3}"
            if obj.get("category_path")!=cp_expected:
                bad_catpath+=1
            # counters
            l1_counter[l1]+=1; l2_counter[(l1,l2)]+=1; l3_counter[(l1,l2,l3)]+=1
            ch_counter[obj.get("channel")]+=1
            sent_counter[obj.get("sentiment")]+=1
            impact_counter[int(imp)]+=1
            urgency_counter[int(urg)]+=1
            priority_counter[int(obj.get("priority",0))]+=1
            # lengths
            t=obj.get("title_ar") or ""; d=obj.get("description_ar") or ""
            title_lengths.append(len(t))
            # rough word count not used yet; store char lengths
            desc_lengths.append(len(d))
            # dup hash
            key=(t.strip(), d.strip())
            title_desc_hashes[key]+=1

    # duplicate stats (exact title+description pairs)
    dup_pairs=sum(1 for k,c in title_desc_hashes.items() if c>1)
    dup_records=sum(c-1 for c in title_desc_hashes.values() if c>1)

    def pct(x):
        return 0 if total==0 else (100.0*x/total)

    lines=[]
    lines.append(f"Total: {total}")
    lines.append("== Violations ==")
    lines.append(f"Missing required keys: {missing_keys} ({pct(missing_keys):.2f}%)")
    lines.append(f"Bad channel: {bad_channel} ({pct(bad_channel):.2f}%)")
    lines.append(f"Bad sentiment: {bad_sentiment} ({pct(bad_sentiment):.2f}%)")
    lines.append(f"Priority rule mismatches: {bad_priority} ({pct(bad_priority):.2f}%)")
    lines.append(f"Taxonomy (L1/L2/L3) not allowed: {bad_taxonomy} ({pct(bad_taxonomy):.2f}%)")
    lines.append(f"category_path mismatch: {bad_catpath} ({pct(bad_catpath):.2f}%)")
    lines.append("")
    lines.append("First 10 priority mismatches (ticket, impact, urgency, priority, expected):")
    for r in first_10_bad_priority:
        lines.append(str(r))
    lines.append("First 10 taxonomy violations (ticket, L1,L2,L3):")
    for r in first_10_bad_tax:
        lines.append(str(r))
    lines.append("")

    lines.append("== Lengths (chars) ==")
    if desc_lengths:
        lines.append(f"Description len: mean {statistics.mean(desc_lengths):.1f}, median {statistics.median(desc_lengths):.1f}, min {min(desc_lengths)}, max {max(desc_lengths)}")
    if title_lengths:
        lines.append(f"Title len: mean {statistics.mean(title_lengths):.1f}, median {statistics.median(title_lengths):.1f}, min {min(title_lengths)}, max {max(title_lengths)}")
    lines.append("")

    def topn(counter, n=10, fmt=lambda k: str(k)):
        return [f"{fmt(k)}: {v}" for k,v in counter.most_common(n)]

    lines.append("== Distributions ==")
    lines.append("Top L1:")
    lines += topn(l1_counter)
    lines.append("Top L2 (by L1,L2):")
    lines += topn(l2_counter, fmt=lambda k: " > ".join(k))
    lines.append("Top L3 (by L1,L2,L3):")
    lines += topn(l3_counter, fmt=lambda k: " > ".join(k))
    lines.append("Channels:")
    lines += topn(ch_counter)
    lines.append("Sentiment:")
    lines += topn(sent_counter)
    lines.append("Impact:")
    lines += topn(impact_counter)
    lines.append("Urgency:")
    lines += topn(urgency_counter)
    lines.append("Priority:")
    lines += topn(priority_counter)
    lines.append("")

    lines.append("== Duplicates ==")
    lines.append(f"Duplicate (exact title+description) pairs: {dup_pairs}")
    lines.append(f"Duplicate extra records (beyond first): {dup_records}")

    report="\n".join(lines)+"\n"
    if outpath:
        outpath.parent.mkdir(parents=True, exist_ok=True)
        outpath.write_text(report, encoding='utf-8')
    else:
        print(report)

if __name__=="__main__":
    main()
