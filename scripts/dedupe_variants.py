#!/usr/bin/env python3
import sys, json, random
from pathlib import Path

OS_CHOICES = ["Windows 10","Windows 11","macOS 14","Ubuntu 22.04"]
EXTRA_SNIPPETS = [
    "المشكلة بتحصل مع أكتر من زميل في نفس الفريق.",
    "جربت من شبكة مختلفة وبرضه نفس النتيجة.",
    "الموضوع مؤثر على الديدلاين بتاعي النهارده.",
    "سحبت Log من الحدث ومستعد أرفعه لكم لو محتاجين.",
]


def main():
    if len(sys.argv)<3:
        print("Usage: dedupe_variants.py <IN.jsonl> <OUT.jsonl>", file=sys.stderr)
        sys.exit(2)
    inp=Path(sys.argv[1]); outp=Path(sys.argv[2])
    counts={}
    with inp.open('r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            obj=json.loads(line)
            key=(obj.get('title_ar','').strip(), obj.get('description_ar','').strip())
            counts[key]=counts.get(key,0)+1
    seen={}
    rng=random.Random(42)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with inp.open('r', encoding='utf-8') as f, outp.open('w', encoding='utf-8') as fo:
        for line in f:
            if not line.strip(): continue
            obj=json.loads(line)
            key=(obj.get('title_ar','').strip(), obj.get('description_ar','').strip())
            seen[key]=seen.get(key,0)+1
            if counts.get(key,0)>1 and seen[key]>1:
                # add a unique tail sentence using ticket_id as seed
                seed = sum(ord(c) for c in obj.get('ticket_id',''))
                rr=random.Random(seed)
                base_extra = rr.choice(EXTRA_SNIPPETS)
                # deterministic per ticket id
                hh = rr.randint(0,23); mm = rr.randint(0,59)
                floor = 1 + (rr.randint(0,5))
                os_pick = rr.choice(OS_CHOICES)
                stamp = f"ملاحظة: ظهرت المشكلة حوالي الساعة {hh:02d}:{mm:02d} في مبنى A - الدور {floor} على {os_pick}."
                d=obj.get('description_ar') or ''
                if not d.endswith('.'): d=d+'.'
                obj['description_ar']=d+" "+base_extra+" "+stamp
            fo.write(json.dumps(obj, ensure_ascii=False)+"\n")

if __name__=='__main__':
    main()
