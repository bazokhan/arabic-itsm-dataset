# Arabic ITSM Dataset

A synthetic dataset of **10,000 Arabic IT support tickets**, labeled with a structured 3-level ITSM taxonomy, generated using LLMs, and validated programmatically before release.

Tickets are written in Egyptian Arabic (عامية مصرية) and cover the full range of helpdesk scenarios: access issues, network problems, hardware faults, software errors, security incidents, and service requests. Arabic technical vocabulary is mixed with English terms as they naturally appear in real Egyptian workplace communication (VPN، WiFi، Outlook، MFA…).

[![View Notebook](https://img.shields.io/badge/Notebook-View%20on%20GitHub-blue?logo=jupyter)](https://github.com/bazokhan/arabic-itsm-dataset/blob/master/notebooks/inspect_data.ipynb)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bazokhan/arabic-itsm-dataset/blob/master/notebooks/inspect_data.ipynb)
[![Browse Dataset](https://img.shields.io/badge/Dataset-FlatGitHub-lightgrey?logo=github)](https://flatgithub.com/bazokhan/arabic-itsm-dataset?filename=dataset_clean.csv)
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-Dataset-yellow?logo=huggingface)](https://huggingface.co/datasets/albaz2000/arabic-itsm-dataset)

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

**1. Design the taxonomy**
The 3-level ITSM hierarchy in [`taxonomy_itsm_v1.json`](taxonomy_itsm_v1.json) was hand-crafted to reflect real IT helpdesk category trees. Each node includes suggested tags to guide generation toward realistic, domain-appropriate vocabulary.

**2. Write the generation contract**
[`prompts/generation_v1.md`](prompts/generation_v1.md) defines the full schema, the priority formula, the target dialect, category constraints, and realism requirements. This contract is what gets passed to the LLM alongside the taxonomy file.

**3. Automated generation on a hosted VPS**
The actual generation was done by [@DrEmadAgha](https://github.com/DrEmadAgha) using [CLIProxyAPI](https://help.router-for.me/) on a self-hosted agentic framework running his own models on a VPS. The bots handled the full pipeline autonomously: generating tickets in chunks, running quality checks, deduplicating, enriching short descriptions, and validating against the taxonomy. The complete output of that run is `parts/part_001.jsonl` — all 10,000 tickets in one automated pass.

The scripts driving that pipeline (all authored by @DrEmadAgha) are in [`scripts/`](scripts/):

| Script | What it does |
|--------|--------------|
| [`generate_tickets_local.py`](scripts/generate_tickets_local.py) | Template-based ticket generator — covers all 31 leaf categories with hardcoded Egyptian Arabic title/description templates |
| [`dq_report.py`](scripts/dq_report.py) | Data quality report — validates a JSONL file and prints violation counts, distributions, and duplicate stats |
| [`dedupe_variants.py`](scripts/dedupe_variants.py) | Deduplication pass — detects exact title+description duplicates and appends a unique contextual sentence to each duplicate to differentiate them |
| [`postprocess_v2.py`](scripts/postprocess_v2.py) | Post-processing pass — remaps invalid L3 categories, fixes priority, and enriches short descriptions (<90 chars) with category-specific details (VPN error codes, Outlook error codes, WiFi SSIDs, etc.) |

**4. Final validation and merge**
[`build_dataset.py`](build_dataset.py) provides a final schema validation pass on the generated parts:
- All required fields present and correctly typed
- `channel` and `sentiment` within allowed values
- `created_at` ≤ `updated_at`
- `category_path` consistent with the three level fields and within the taxonomy
- `priority` satisfies `round((impact + urgency) / 2)`
- No duplicate `ticket_id`

Rows that pass are written to `dataset_clean.*`. Rows that fail go to `dataset_rejected.jsonl` with specific error codes. The fixer prompt at [`prompts/fixer_v1.md`](prompts/fixer_v1.md) can be used to repair rejects, which are then reintegrated with `python build_dataset.py --apply-fixes`.

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
├── build_dataset.py           # Final validation + merge script
├── taxonomy_itsm_v1.json      # 3-level ITSM taxonomy with tag suggestions
├── requirements.txt
├── prompts/
│   ├── generation_v1.md       # LLM prompt / generation contract
│   └── fixer_v1.md            # LLM prompt for repairing rejected rows
├── scripts/                   # Generation + QA pipeline (by @DrEmadAgha)
│   ├── generate_tickets_local.py  # Template-based ticket generator
│   ├── dq_report.py               # Data quality report
│   ├── dedupe_variants.py         # Deduplication pass
│   ├── postprocess_v2.py          # Enrichment + category fix pass
│   └── publish_hf.py              # One-time Hugging Face upload
├── parts/
│   └── part_001.jsonl         # Raw pipeline output (10,000 tickets)
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

## Credits

- **[@DrEmadAgha](https://github.com/DrEmadAgha)** — built and ran the automated generation pipeline using [CLIProxyAPI](https://help.router-for.me/) on a self-hosted VPS. Authored the generation, QA, deduplication, and post-processing scripts in `scripts/`. The 10,000 tickets in `parts/part_001.jsonl` are the output of his pipeline.
- **[@bazokhan](https://github.com/bazokhan)** — designed the taxonomy, wrote the generation contract and fixer prompts, ran the final validation pass, and published the dataset.

---

## License

MIT
