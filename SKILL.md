# skill.md — Agent Playbook (arabic-itsm-dataset)

You are an agent working **inside this folder**. Goal: generate/repair/merge Arabic ITSM JSONL tickets safely.

## Golden rules
- **Never overwrite** existing `parts/part_*.jsonl`. Create new files (`*_fixed.jsonl`, `*_v2.jsonl`).
- **Never change taxonomy in-place**. If updating taxonomy, create a new version file (e.g., `taxonomy_itsm_v2.json`) and keep the old.
- `dataset_clean.jsonl` / `dataset_clean.csv` are **generated**; safe to delete/regenerate.

## Inputs/Outputs
- Inputs: `parts/part_*.jsonl` (LLM-generated), `taxonomy_itsm.json`
- Outputs: `dataset_clean.jsonl`, `dataset_clean.csv`
- Derivation: `preprocessed_ar` is computed by `build_dataset.py`

## Standard operating procedure
1) Generate a batch using `generation_contract_prompt_v1.md`
   - Ensure output is **JSONL only**
   - Ensure category path is from taxonomy
   - Save as `parts/part_###.jsonl`

2) Validate/build
   - Run: `python build_dataset.py`
   - Check printed counts: clean vs rejected

3) Fix rejected rows (optional)
   - Feed rejected items to `fixer_prompt_v1.md`
   - Save repaired tickets to a new file: `parts/part_###_fixed.jsonl`
   - Re-run `python build_dataset.py`

## Quality checklist (before committing new parts)
- Unique `ticket_id` per row
- Valid ISO timestamps with timezone; `updated_at >= created_at`
- `category_path == l1 > l2 > l3` and allowed by taxonomy
- `impact`, `urgency` in 1..5; `priority` matches rule
- `tags` is a JSON array (2..6 strings)
- Arabic dialect matches requested dialect (e.g., Egyptian); technical terms may remain English

## Common maintenance tasks
- Add categories: create `taxonomy_itsm_v2.json`, update script constant `TAXONOMY_PATH`
- Add more validation: extend `validate_row()` in `build_dataset.py`
- Export variants: post-process `dataset_clean.csv` (do not edit raw parts)
