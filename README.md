# arabic-itsm-dataset

Synthetic Arabic ITSM ticket dataset — generate JSONL batches via LLM, then validate/merge into a clean dataset.

## Quick Start

```bash
pip install -r requirements.txt
python build_dataset.py
```

Requires **Python 3.9+** and `pandas` (see `requirements.txt`).

## Files

| File | Purpose |
|------|---------|
| `taxonomy_itsm_v1.json` | Source-of-truth taxonomy (6 L1 / 14 L2 / 31 L3 categories + suggested tags) |
| `generation_contract_prompt_v1.md` | LLM prompt template for generating JSONL batches |
| `fixer_prompt_v1.md` | LLM prompt for repairing rejected tickets |
| `build_dataset.py` | Validates + merges `parts/part_*.jsonl` into `dataset_clean.jsonl` / `.csv` / `dataset_rejected.jsonl` |
| `examples/sample_ticket.jsonl` | Sample record showing data shape |

## Data Schema

| Field | Type | Constraints |
|-------|------|-------------|
| `ticket_id` | string | Unique, e.g. `"TCKT-000001"` |
| `created_at` | string | ISO 8601 with timezone |
| `updated_at` | string | ISO 8601, must be >= `created_at` |
| `channel` | string | One of: `email`, `portal`, `chatbot`, `phone` |
| `model` | string | LLM model name |
| `dialect` | string | e.g. `"Egyptian"` |
| `title_ar` | string | Short Arabic title |
| `description_ar` | string | Arabic description (multi-line) |
| `category_level_1` | string | Must match taxonomy |
| `category_level_2` | string | Must match taxonomy |
| `category_level_3` | string | Must match taxonomy |
| `category_path` | string | `"L1 > L2 > L3"` — must match levels |
| `tags` | array[string] | 2-6 tags |
| `labels_json` | object | `{ "l1", "l2", "l3", "tags" }` |
| `impact` | int | 1-5 |
| `urgency` | int | 1-5 |
| `priority` | int | 1-5, computed: `round((impact+urgency)/2)` |
| `sentiment` | string | One of: `positive`, `neutral`, `negative`, `mixed` |

## Sample Record

```json
{
  "ticket_id": "TCKT-000001",
  "created_at": "2026-02-10T09:15:00+03:00",
  "updated_at": "2026-02-10T09:45:00+03:00",
  "channel": "portal",
  "model": "claude-opus-4-6",
  "dialect": "Egyptian",
  "title_ar": "مشكلة في الاتصال بشبكة الواي فاي",
  "description_ar": "من امبارح مش قادر اتصل بشبكة الواي فاي في المكتب...",
  "category_level_1": "Network",
  "category_level_2": "WiFi",
  "category_level_3": "Authentication",
  "category_path": "Network > WiFi > Authentication",
  "tags": ["wifi", "authentication", "disconnect"],
  "labels_json": {
    "l1": "Network",
    "l2": "WiFi",
    "l3": "Authentication",
    "tags": ["wifi", "authentication", "disconnect"]
  },
  "impact": 3,
  "urgency": 4,
  "priority": 4,
  "sentiment": "negative"
}
```

## CLI Usage

```bash
# Build (defaults)
python build_dataset.py

# Build with custom paths
python build_dataset.py \
  --taxonomy taxonomy_itsm_v1.json \
  --input-glob "parts/part_*.jsonl" \
  --out-jsonl dataset_clean.jsonl \
  --out-csv dataset_clean.csv \
  --out-rejected dataset_rejected.jsonl

# Apply fixes: merge *_fixed.jsonl into originals, then rebuild
python build_dataset.py --apply-fixes
```

## Workflow

1. **Generate batches** — use `generation_contract_prompt_v1.md`, save as `parts/part_001.jsonl`, `parts/part_002.jsonl`, etc.

   Example with Claude Code or similar agentic tools:
   ```
   Execute the prompt in @generation_contract_prompt_v1.md with
   TAXONOMY_FILE=@taxonomy_itsm_v1.json, N=100, DIALECT=Egyptian,
   OUTPUT_FILE=parts/part_001.jsonl
   ```

2. **Build** — run `python build_dataset.py`. Outputs `dataset_clean.jsonl` + `.csv`.

3. **Fix rejects** — feed `dataset_rejected.jsonl` to `fixer_prompt_v1.md`, saving output as `parts/part_<N>_fixed.jsonl` (matching the original part name).

   Example:
   ```
   Execute the prompt in @fixer_prompt_v1.md with
   TAXONOMY_FILE=@taxonomy_itsm_v1.json, INPUT_FILE=@dataset_rejected.jsonl,
   OUTPUT_FILE=parts/part_001_fixed.jsonl
   ```

4. **Apply fixes** — merge fixed rows back into the original part files, then rebuild.

   ```bash
   python build_dataset.py --apply-fixes
   ```

   This replaces rejected rows in `parts/part_001.jsonl` with their fixed versions from `parts/part_001_fixed.jsonl`, deletes the `*_fixed.jsonl` and `dataset_rejected.jsonl` files, then rebuilds the dataset.

## Do-not-destroy Rules

- Never overwrite `taxonomy_itsm_v1.json` without versioning.
- Never overwrite `parts/part_*.jsonl` files; create `*_fixed.jsonl` or `*_v2.jsonl`.
- `dataset_clean.*` and `dataset_rejected.jsonl` are generated artifacts — safe to delete/regenerate.

## Sanity Check

Quick test with sample data:

```bash
mkdir parts
cp examples/sample_ticket.jsonl parts/part_001.jsonl
python build_dataset.py
# Should output: Clean rows: 1, Rejected rows: 0
rm -rf parts dataset_clean.*
```

## Notes

- **No preprocessing is applied.** The output contains raw Arabic text as generated. Consumers should apply their own normalization (diacritics removal, alif normalization, etc.) as needed.
- `priority` is enforced by the rule: `round((impact + urgency) / 2)` clamped to 1..5.
