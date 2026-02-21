# Arabic ITSM Dataset

A synthetic dataset of **10,000 Arabic IT support tickets**, labeled with a structured 3-level ITSM taxonomy, generated using LLMs, and validated programmatically before release.

Tickets are written in Egyptian Arabic (عامية مصرية) and cover the full range of helpdesk scenarios: access issues, network problems, hardware faults, software errors, security incidents, and service requests. Arabic technical vocabulary is mixed with English terms as they naturally appear in real Egyptian workplace communication (VPN، WiFi، Outlook، MFA…).

[![View Notebook](https://img.shields.io/badge/Notebook-View%20on%20GitHub-blue?logo=jupyter)](https://github.com/bazokhan/arabic-itsm-dataset/blob/master/notebooks/inspect_data.ipynb)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bazokhan/arabic-itsm-dataset/blob/master/notebooks/inspect_data.ipynb)

---

## Dataset

| Format | File | Size |
|--------|------|------|
| CSV | [`dataset_clean.csv`](dataset_clean.csv) | ~6.5 MB |
| JSONL | [`dataset_clean.jsonl`](dataset_clean.jsonl) | ~9 MB |

Load directly from GitHub without cloning:

```python
import pandas as pd

df = pd.read_csv(
    "https://raw.githubusercontent.com/bazokhan/arabic-itsm-dataset/master/dataset_clean.csv"
)
df.head()
```

---

## Schema

| Field | Type | Description |
|-------|------|-------------|
| `ticket_id` | string | Unique ID, format `TCKT-NNN-NNN` |
| `created_at` | ISO 8601 | Ticket creation timestamp with timezone |
| `updated_at` | ISO 8601 | Last update timestamp (≥ `created_at`) |
| `channel` | string | Submission channel: `email` `portal` `chatbot` `phone` |
| `model` | string | LLM model that generated the ticket |
| `dialect` | string | Arabic dialect (e.g. `Egyptian`) |
| `title_ar` | string | Short Arabic title |
| `description_ar` | string | Full Arabic description body |
| `category_level_1` | string | Top-level category (6 classes) |
| `category_level_2` | string | Sub-category (14 classes) |
| `category_level_3` | string | Leaf category (31 classes) |
| `category_path` | string | Composite `"L1 > L2 > L3"` — always consistent with the three levels |
| `tags` | JSON array | 2–6 keyword tags |
| `labels_json` | JSON object | `{l1, l2, l3, tags}` — structured label object |
| `impact` | int 1–5 | Business impact score |
| `urgency` | int 1–5 | Resolution urgency score |
| `priority` | int 1–5 | Computed: `round((impact + urgency) / 2)`, clamped to 1–5 |
| `sentiment` | string | `positive` `neutral` `negative` `mixed` |

---

## Taxonomy

6 top-level categories → 14 sub-categories → 31 leaf categories:

| L1 | L2 | L3 |
|----|----|----|
| Access | Account | Password Reset, Account Locked, Profile Update |
| Access | Permissions | Role Request, Permission Denied, Admin Access |
| Access | MFA/SSO | MFA Failure, SSO Login Issue, Authenticator Issue |
| Network | WiFi | Connectivity, Authentication, Slow Speed |
| Network | VPN | Connection Failure, Credentials, Split Tunnel |
| Network | Internet/LAN | No Internet, DNS, Latency |
| Hardware | Laptop/Desktop | Boot Issue, Performance, Battery |
| Hardware | Printer/Scanner | Print Failure, Driver, Paper Jam |
| Hardware | Peripherals | Keyboard/Mouse, Monitor, Docking Station |
| Software | Email/Calendar | Outlook Issue, Mailbox Access, Sync Problem |
| Software | Office Apps | Word/Excel, License, Crash |
| Software | Business App | Bug, Feature Request, Integration |
| Security | Malware/Phishing | Phishing Email, Suspicious Link, Virus Alert |
| Security | Policy/Compliance | Blocked Site, Device Encryption, Data Access |
| Service | Request | New Device, New Account, Software Install |
| Service | Incident | Outage, Degradation, Intermittent |

Full taxonomy with suggested tags per category: [`taxonomy_itsm_v1.json`](taxonomy_itsm_v1.json)

---

## How It Was Built

Generation was agentic and iterative — not a one-shot bulk prompt.

**1. Design the taxonomy**
A 3-level ITSM hierarchy was hand-crafted to reflect real IT helpdesk category trees. Each node includes a list of suggested tags to guide generation toward realistic, domain-appropriate vocabulary.

**2. Write the generation prompt**
[`prompts/generation_v1.md`](prompts/generation_v1.md) specifies the full schema, the priority formula, the target dialect, category constraints, and realism requirements. The LLM receives the taxonomy file and outputs raw JSONL — one ticket per line, no commentary.

**3. Generate in batches**
Tickets were generated in batches (~1,000 per run) and saved to `parts/part_NNN.jsonl`. Egyptian colloquial Arabic was used throughout, with common technical terms kept in English as they naturally appear.

**4. Validate programmatically**
[`build_dataset.py`](build_dataset.py) checks every row against the schema:
- All required fields present and correctly typed
- `channel` and `sentiment` within allowed values
- `created_at` ≤ `updated_at`
- `category_path` exactly matches the three level fields and is a valid taxonomy path
- `priority` satisfies `round((impact + urgency) / 2)`
- No duplicate `ticket_id`

Rows that pass go to `dataset_clean.*`. Rows that fail go to `dataset_rejected.jsonl` with the specific error codes attached.

**5. Fix and reintegrate rejects**
Rejected rows were fed to [`prompts/fixer_v1.md`](prompts/fixer_v1.md), which repairs schema violations while preserving the original Arabic text. Fixed rows are merged back using `python build_dataset.py --apply-fixes`, which splices the fixed records into the original part files and rebuilds the clean dataset.

**6. Final build**
The output — `dataset_clean.csv` and `dataset_clean.jsonl` — is the merged, validated result of all passes.

---

## Explore the Data

The notebook [`notebooks/inspect_data.ipynb`](notebooks/inspect_data.ipynb) covers:

- Class distribution across all 3 taxonomy levels (count + share)
- Class balance analysis (imbalance ratio per level)
- Sentiment, channel, and dialect breakdowns
- Text length statistics — title and description
- Tag frequency (top 20)
- Duplicate and missing-value checks
- Cross-tabulations: category × sentiment, category × dialect

**View rendered:** [GitHub](https://github.com/bazokhan/arabic-itsm-dataset/blob/master/notebooks/inspect_data.ipynb) · [Run in Colab](https://colab.research.google.com/github/bazokhan/arabic-itsm-dataset/blob/master/notebooks/inspect_data.ipynb)

---

## Reproduce or Extend

```bash
pip install -r requirements.txt

# Build the clean dataset from parts
python build_dataset.py

# Custom paths
python build_dataset.py \
  --taxonomy taxonomy_itsm_v1.json \
  --input-glob "parts/part_*.jsonl" \
  --out-jsonl dataset_clean.jsonl \
  --out-csv dataset_clean.csv

# After fixing rejected rows, merge fixes and rebuild
python build_dataset.py --apply-fixes
```

To generate additional tickets, use the prompts in [`prompts/`](prompts/) with any capable LLM:

```
Execute prompts/generation_v1.md with:
  TAXONOMY_FILE = taxonomy_itsm_v1.json
  N = 1000
  DIALECT = Egyptian
  OUTPUT_FILE = parts/part_002.jsonl
```

---

## Repository Structure

```
arabic-itsm-dataset/
├── dataset_clean.csv          # Final dataset — 10,000 rows (CSV)
├── dataset_clean.jsonl        # Final dataset — 10,000 rows (JSONL)
├── build_dataset.py           # Validation + merge script
├── taxonomy_itsm_v1.json      # 3-level ITSM taxonomy with tag suggestions
├── requirements.txt
├── prompts/
│   ├── generation_v1.md       # LLM prompt for generating tickets
│   └── fixer_v1.md            # LLM prompt for repairing rejected rows
├── parts/
│   └── part_001.jsonl         # Raw generation output (10,000 tickets)
├── examples/
│   └── sample_ticket.jsonl    # Single example record showing the schema
└── notebooks/
    └── inspect_data.ipynb     # Data exploration and validation notebook
```

---

## Notes

- **No text preprocessing is applied.** The dataset contains raw Arabic text as generated. Consumers should apply their own normalization (diacritics removal, alif normalization, etc.) as appropriate for their use case.
- `priority` is enforced by the validator: `round((impact + urgency) / 2)` clamped to 1–5. Minor violations were auto-corrected during the build; rows with other errors went through the fix loop.
- `dataset_rejected.jsonl` is a build artifact — not committed. It only appears locally when there are validation failures.

---

## License

MIT
