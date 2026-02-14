You are generating synthetic ITSM support tickets in Arabic.

REQUIRED VARIABLES (ask the user for any that were not provided before executing):
- TAXONOMY_FILE: path to the taxonomy JSON file
- N: number of tickets to generate
- DIALECT: Arabic dialect to use (e.g., Egyptian colloquial)
- OUTPUT_FILE: path to save the output JSONL file (e.g., parts/part_001.jsonl)

OUTPUT FORMAT (STRICT):
- Return JSON Lines (JSONL) only.
- One JSON object per line.
- No markdown, no commentary, no extra text.
- Save output to OUTPUT_FILE.

TASK:
- Generate N tickets in DIALECT Arabic
- You may keep common technical terms in English (e.g., VPN, WiFi, Outlook, DNS, MFA, SSO)

SCHEMA (REQUIRED KEYS EXACTLY):
ticket_id: string (unique, format "TCKT-000001" etc.)
created_at: ISO timestamp string (e.g., "2026-02-14T10:23:00+02:00")
updated_at: ISO timestamp string (>= created_at)
channel: one of ["email","portal","chatbot","phone"]
model: string (the model name you are)

dialect: string (e.g., "Egyptian")
title_ar: string (short)
description_ar: string (multi-line allowed)

category_level_1: string
category_level_2: string
category_level_3: string
category_path: string formatted "L1 > L2 > L3"

tags: array of strings (2 to 6 tags)
labels_json: object with keys { "l1","l2","l3","tags" }

impact: integer 1..5
urgency: integer 1..5
priority: integer 1..5  (MUST follow the rule below)
sentiment: one of ["positive","neutral","negative","mixed"]

PRIORITY RULE (MUST FOLLOW):
priority = round((impact + urgency)/2) clamped to 1..5
Examples:
impact 5 & urgency 5 => priority 5
impact 1 & urgency 5 => priority 3
impact 2 & urgency 2 => priority 2

CATEGORY CONSTRAINT:
Choose category_level_1/2/3 ONLY from the allowed taxonomy in TAXONOMY_FILE.
category_path MUST exactly match the chosen levels.
Use only the valid "L1 > L2 > L3" combinations from that file.

REALISM CONSTRAINTS:
- Each ticket should sound like a real user request/complaint.
- Use varied writing styles: concise, detailed, frustrated, polite, etc.
- Ensure category matches the described problem.

RETURN EXACTLY N JSON OBJECTS, ONE PER LINE.
