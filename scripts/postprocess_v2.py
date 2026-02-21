#!/usr/bin/env python3
import sys, json, re, random
from pathlib import Path
from datetime import datetime

ALLOWED_L3_MAP = {
    ("Software","Office Apps","Excel Crash"): ("Software","Office Apps","Crash"),
    ("Software","Office Apps","Performance"): ("Software","Office Apps","Word/Excel"),
}

OS_CHOICES = ["Windows 10","Windows 11","macOS 14","Ubuntu 22.04"]
OFFICE_VERS = ["Office 365 v2401","Office 365 v2402","Office 2019","Office LTSC 2021"]
WIFI_SSIDS = ["Company-Secure","Company-Guest","HQ-Floor3","Warehouse-AP"]
VPN_ERRORS = ["Error 809","Timeout","IKE Auth failed","Certificate expired"]
OUTLOOK_ERRORS = ["0x8004010F","0x800CCC0E","OST corruption","Add-in conflict"]
TONE_SNIPPETS = [
 "محتاج الموضوع يتحل بسرعة لو سمحتوا.",
 "جربت ريستارت وكمان عملت Repair بس نفس المشكلة.",
 "المشكلة بتظهر وتختفي، ومش ثابتة على طول.",
 "لو محتاجين لوجز أو سكرينشوت أنا جاهز أبعتها.",
]


def prio(impact:int, urgency:int)->int:
    return max(1,min(5,int((impact+urgency)/2+0.5)))


def expand_desc(seed:int,l1,l2,l3,title,desc):
    rng = random.Random(seed)
    extra=[]
    # category-specific enrichment
    if (l1,l2)==("Network","VPN"):
        extra.append(f"بتحصل وانا على {rng.choice(OS_CHOICES)} من البيت، وبيظهر {rng.choice(VPN_ERRORS)}.")
    if (l1,l2,l3)==("Software","Email/Calendar","Outlook Issue"):
        extra.append(f"Outlook على {rng.choice(OS_CHOICES)} ونسخة {rng.choice(OFFICE_VERS)}.")
        extra.append(f"جربت امسح الـ OST واعمل Profile جديد.")
        extra.append(f"أحياناً بيظهر كود {rng.choice(OUTLOOK_ERRORS)}.")
    if (l1,l2)==("Network","WiFi"):
        extra.append(f"على شبكة {rng.choice(WIFI_SSIDS)} في مبنى A الدور {rng.randint(1,6)}، الإشارة {rng.choice(['ضعيفة','متوسطة','كويسة'])}.")
    if (l1,l2,l3)==("Hardware","Laptop/Desktop","Performance"):
        extra.append(f"الجهاز عليه {rng.choice(OS_CHOICES)} وBusy وقت التشغيل. حصلت المشكلة بعد آخر تحديث.")
    if (l1,l2)==("Software","Office Apps"):
        extra.append(f"نسخة الأوفيس: {rng.choice(OFFICE_VERS)}. الملفات على Share داخلي.")
    # generic details
    extra.append(f"بقالها {rng.randint(1,48)} ساعة تقريبا.")
    extra.append(rng.choice(TONE_SNIPPETS))
    # ensure 2-5 sentences total
    base = desc.rstrip('.')
    sentences = [base] + extra[:rng.randint(2,4)]
    return " ".join(s if s.endswith('.') else s+"." for s in sentences)


def main():
    if len(sys.argv)<3:
        print("Usage: postprocess_v2.py <IN.jsonl> <OUT.jsonl>", file=sys.stderr)
        sys.exit(2)
    inp = Path(sys.argv[1]); outp=Path(sys.argv[2])
    outp.parent.mkdir(parents=True, exist_ok=True)
    with inp.open('r', encoding='utf-8') as fi, outp.open('w', encoding='utf-8') as fo:
        for line in fi:
            if not line.strip():
                continue
            obj=json.loads(line)
            l1=obj.get('category_level_1'); l2=obj.get('category_level_2'); l3=obj.get('category_level_3')
            key=(l1,l2,l3)
            if key in ALLOWED_L3_MAP:
                nl1,nl2,nl3=ALLOWED_L3_MAP[key]
                obj['category_level_1']=nl1; obj['category_level_2']=nl2; obj['category_level_3']=nl3
                obj['category_path']=f"{nl1} > {nl2} > {nl3}"
                obj['labels_json']={'l1':nl1,'l2':nl2,'l3':nl3,'tags':obj.get('tags',[])}
            # fix priority
            try:
                imp=int(obj.get('impact',0)); urg=int(obj.get('urgency',0))
                obj['priority']=prio(imp,urg)
            except Exception:
                pass
            # enrich short or duplicate-looking descriptions
            desc = obj.get('description_ar') or ''
            title = obj.get('title_ar') or ''
            seed = sum(ord(c) for c in obj.get('ticket_id',''))
            if len(desc)<90:
                obj['description_ar']=expand_desc(seed,l1,l2,obj.get('category_level_3'),title,desc)
            fo.write(json.dumps(obj, ensure_ascii=False)+"\n")

if __name__=='__main__':
    main()
