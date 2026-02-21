#!/usr/bin/env python3
import json, random, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

TAGS_FALLBACK = ["bug","error","request","network","wifi","vpn","outlook","dns","mfa","sso","printer","laptop","policy","security"]

TITLE_TEMPLATES = {
    ("Access","Account","Password Reset"): ["نسيت الباسورد","تغيير كلمة السر","عاوز أعمل Reset للباسورد"],
    ("Access","Account","Account Locked"): ["الأكونت اتقفل","حساب مغلق","Account Locked"],
    ("Access","Account","Profile Update"): ["تحديث البروفايل","تعديل بياناتي","تغيير رقم الموبايل"],
    ("Access","Permissions","Role Request"): ["طلب صلاحيات","عاوز Role جديد","ترقية صلاحياتي"],
    ("Access","Permissions","Permission Denied"): ["معنديش صلاحية","Permission Denied","رفض الدخول"],
    ("Access","Permissions","Admin Access"): ["صلاحيات أدمن","عايز Admin Access","رفع الصلاحيات"],
    ("Access","MFA/SSO","MFA Failure"): ["MFA مش شغال","مش بيوصل OTP","الموثّق واقع"],
    ("Access","MFA/SSO","SSO Login Issue"): ["مشكلة SSO","مش عارف أعمل Login","الدخول الموحد مش شغال"],
    ("Access","MFA/SSO","Authenticator Issue"): ["مشكلة في الـ Authenticator","الموثّق بيهنج","الموبايل مش بيطلع كود"],
    ("Network","WiFi","Connectivity"): ["الواي فاي فاصل","مش عارف ألقط WiFi","مشكلة في النت"],
    ("Network","WiFi","Authentication"): ["مشكلة دخول WiFi","كلمة سر الواي فاي","مش بيقبل الـ SSID"],
    ("Network","WiFi","Slow Speed"): ["النت بطيء","Slow WiFi","سرعة ضعيفة"],
    ("Network","VPN","Connection Failure"): ["الـ VPN مش شغال","VPN Timeout","مشكلة في Remote Access"],
    ("Network","VPN","Credentials"): ["بيانات VPN غلط","مش راضي يقبل اليوزر","Credential Error"],
    ("Network","VPN","Split Tunnel"): ["مشكلة Split Tunnel","بعض المواقع بتقف مع VPN","Traffic رايح كله على الـ Tunnel"],
    ("Network","Internet/LAN","No Internet"): ["مفيش إنترنت","النت قاطع","الدنيا واقفة"],
    ("Network","Internet/LAN","DNS"): ["ترجمة الأسماء","DNS مش شغال","المواقع تفتح بـ IP بس"],
    ("Network","Internet/LAN","Latency"): ["Latency عالي","البنج عالي","تقطيع في الشبكة"],
    ("Hardware","Laptop/Desktop","Boot Issue"): ["الجهاز مش بيفتح","مشكلة إقلاع","OS مش داخل"],
    ("Hardware","Laptop/Desktop","Performance"): ["الجهاز تقيل","تهنيج في الجهاز","الأداء بطيء"],
    ("Hardware","Laptop/Desktop","Battery"): ["البطارية بتخلص بسرعة","شاحن اللابتوب","الجهاز بيسخن"],
    ("Hardware","Printer/Scanner","Print Failure"): ["البرنتر مش بتطبع","الطباعة واقفة","الطابعة معلقة"],
    ("Hardware","Printer/Scanner","Driver"): ["تعريف البرنتر","Driver مشكلة","الاسكانر مش ظاهر"],
    ("Hardware","Printer/Scanner","Paper Jam"): ["ورق معلق","Paper Jam","الطابعة عاملة صوت"],
    ("Hardware","Peripherals","Keyboard/Mouse"): ["الكيبورد/الماوس مش شغال","زرار بايظ","الماوس بيفصل"],
    ("Hardware","Peripherals","Monitor"): ["مشكلة في الشاشة","HDMI مش قارئ","السكرين بتفصل"],
    ("Hardware","Peripherals","Docking Station"): ["الدّوك مش قارئ","USB-C Dock","المنافذ مش شغالة"],
    ("Software","Email/Calendar","Outlook Issue"): ["الأوتلوك بيهنج","Outlook Not Responding","مش بيوصل إيميلات"],
    ("Software","Email/Calendar","Mailbox Access"): ["مش قادر أفتح الميلبوكس","Access للميلبوكس","Shared Mailbox"],
    ("Software","Email/Calendar","Sync Problem"): ["مشكلة سينك","الإيميل مش بيتزامن","Calendar مش بتتحدث"],
    ("Software","Office Apps","Word/Excel"): ["مشكلة Word/Excel","الإكسيل بيقفل","الورد مش بيفتح"],
    ("Software","Office Apps","License"): ["طلب تفعيل الأوفيس","License Error","الأوفيس محتاج تفعيل"],
    ("Software","Office Apps","Crash"): ["البرنامج بيقع","App Crash","السوفتوير بيقفل"],
    ("Software","Business App","Bug"): ["Bug في الأبلكيشن","غلط في السيستم","الأبلكيشن مش بيسيف"],
    ("Software","Business App","Feature Request"): ["طلب ميزة جديدة","Feature Request","نحتاج إضافة جديدة"],
    ("Software","Business App","Integration"): ["تكامل API","Integration Issue","الـ Webhook مش شغال"],
    ("Security","Malware/Phishing","Phishing Email"): ["إيميل مشكوك فيه","بلاغ عن سبام","Phishing"],
    ("Security","Malware/Phishing","Suspicious Link"): ["لينك مريب","رابط مش آمن","تحذير أمن"],
    ("Security","Malware/Phishing","Virus Alert"): ["تنبيه فيروس","Virus Alert","مالوير"],
    ("Security","Policy/Compliance","Blocked Site"): ["موقع محجوب","Blocked Site","السياسة مانعة الموقع"],
    ("Security","Policy/Compliance","Device Encryption"): ["تشفير الجهاز","Encryption","طلب BitLocker"],
    ("Security","Policy/Compliance","Data Access"): ["وصول للبيانات","Data Access","DLP"],
    ("Service","Request","New Device"): ["طلب لابتوب جديد","طلب شاشة إضافية","طلب ماوس/كيبورد"],
    ("Service","Request","New Account"): ["أكونت جديد","حساب موظف جديد","تهيئة مستخدم"],
    ("Service","Request","Software Install"): ["تنزيل برنامج","Software Install","طلب Setup"],
    ("Service","Incident","Outage"): ["السيستم واقع","توقف الخدمة","عطل عام"],
    ("Service","Incident","Degradation"): ["الخدمة بطيئة","Degraded","الأداء متذبذب"],
    ("Service","Incident","Intermittent"): ["الخدمة بتقطع","انقطاع متكرر","Intermittent Issue"],
}

DESC_TEMPLATES = {
    ("Network","VPN","Connection Failure"): [
        "كل ما أحاول أربط بالـ VPN بيطلعلي Timeout أو Error 809. جربت كذا مرة من البيت ومن الداتا لسه نفس المشكلة.",
        "الـ VPN بيقطع بعد 2-3 دقايق. محتاج أشتغل ريموت ومش عارف أكمل شغلي.",
    ],
    ("Software","Email/Calendar","Outlook Issue"): [
        "Outlook مش بيرد وكتير بيعمل Not Responding. جربت Repair ولسه المشكلة موجودة.",
        "الإيميلات بتتأخر توصل في Outlook بس بتكون موجودة على الويب. غالباً مشكلة Sync.",
    ],
    ("Network","Internet/LAN","DNS"): [
        "مش عارف أفتح المواقع بالاسم، لكن بالـ IP بيفتح. واضح إن في مشكلة DNS عندي أو في الشبكة.",
    ],
}

SENTIMENTS = ["positive","neutral","negative","mixed"]
CHANNELS = ["email","portal","chatbot","phone"]

def load_taxonomy(path: Path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    combos = []
    for item in data["taxonomy"]:
        l1 = item["l1"]; l2 = item["l2"]; tags = item.get("tags") or TAGS_FALLBACK
        for l3 in item["l3"]:
            combos.append((l1,l2,l3,tags))
    return combos

def rand_ts():
    day = random.randint(1, 20)
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    tz = timezone(timedelta(hours=2))
    created = datetime(2026, 2, day, hour, minute, 0, tzinfo=tz)
    add_hours = random.randint(0, 72)
    add_minutes = random.randint(0, 59)
    updated = created + timedelta(hours=add_hours, minutes=add_minutes)
    return created.isoformat(timespec='seconds'), updated.isoformat(timespec='seconds')

def round_priority(i, u):
    val = (i + u) / 2.0
    pr = int(val + 0.5)
    return max(1, min(5, pr))

def pick_title_desc(l1,l2,l3):
    key = (l1,l2,l3)
    titles = TITLE_TEMPLATES.get(key) or [f"مشكلة في {l3}", f"طلب متعلق بـ {l2}"]
    descs = DESC_TEMPLATES.get(key) or [
        f"فيه مشكلة مرتبطة بـ {l1} / {l2} / {l3}. الموضوع مأثر على الشغل ومحتاج يتحل بسرعة.",
        f"المشكلة مستمرة من يومين. جربت Restart وبرضه نفس الوضع. لو محتاجين لوجز أنا جاهز."
    ]
    return random.choice(titles), random.choice(descs)

def gen(index: str, count: int, outfile: Path, model_name: str = "gemini-3-flash", dialect: str = "Egyptian"):
    combos = load_taxonomy(Path("taxonomy.json"))
    rng = random.Random()
    with outfile.open('w', encoding='utf-8') as f:
        for seq in range(1, count+1):
            l1,l2,l3,tags_pool = rng.choice(combos)
            created_at, updated_at = rand_ts()
            impact = rng.randint(1,5)
            urgency = rng.randint(1,5)
            priority = round_priority(impact, urgency)
            tags_sel = rng.sample(tags_pool if len(tags_pool)>=2 else TAGS_FALLBACK, k=min(len(tags_pool), rng.randint(2,6)) if len(tags_pool)>=2 else 2)
            title, desc = pick_title_desc(l1,l2,l3)
            ticket = {
                "ticket_id": f"TCKT-{index}-{seq:03d}",
                "created_at": created_at,
                "updated_at": updated_at,
                "channel": rng.choice(CHANNELS),
                "model": model_name,
                "dialect": dialect,
                "title_ar": title,
                "description_ar": desc,
                "category_level_1": l1,
                "category_level_2": l2,
                "category_level_3": l3,
                "category_path": f"{l1} > {l2} > {l3}",
                "tags": tags_sel,
                "labels_json": {"l1": l1, "l2": l2, "l3": l3, "tags": tags_sel},
                "impact": impact,
                "urgency": urgency,
                "priority": priority,
                "sentiment": rng.choice(SENTIMENTS),
            }
            f.write(json.dumps(ticket, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: generate_tickets_local.py <INDEX> <OUTFILE> [COUNT=500] [MODEL=gemini-3-flash]", file=sys.stderr)
        sys.exit(2)
    index = sys.argv[1]
    outfile = Path(sys.argv[2])
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 500
    model_name = sys.argv[4] if len(sys.argv) > 4 else "gemini-3-flash"
    outfile.parent.mkdir(parents=True, exist_ok=True)
    gen(index, count, outfile, model_name=model_name)
