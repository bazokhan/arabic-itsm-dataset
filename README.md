# arabic-itsm-dataset

Generate a **synthetic Arabic ITSM ticket dataset** (JSONL → validated/cleaned CSV) using LLM batches, then merge/validate safely.

## Folder
- `taxonomy_itsm.json` — source-of-truth taxonomy (allowed `L1 > L2 > L3` paths + suggested tags)
- `generation_contract_prompt_v1.md` — prompt to generate **JSONL** batches (e.g., 100 tickets/run)
- `fixer_prompt_v1.md` — prompt to repair rejected/invalid JSONL lines
- `build_dataset.py` — merges `parts/part_*.jsonl`, validates, derives `preprocessed_ar`, exports `dataset_clean.jsonl` + `dataset_clean.csv`

## Workflow (safe)
1) **Create batches** (do not edit existing batches in-place)
   - Make a folder: `parts/`
   - Generate JSONL files like: `parts/part_001.jsonl`, `parts/part_002.jsonl`, ...

2) **Build the dataset**
   ```bash
   python build_dataset.py
   ```
   Outputs:
   - `dataset_clean.jsonl`
   - `dataset_clean.csv`

3) **If you have rejected lines**
   - Re-run generation for more data, OR
   - Use `fixer_prompt_v1.md` on the rejected items and save repaired lines into a new file like:
     `parts/part_001_fixed.jsonl` (never overwrite the original).
   - Run `python build_dataset.py` again.

## Do-not-destroy rules
- Never overwrite `taxonomy_itsm.json` without versioning (copy to `taxonomy_itsm_v2.json` and update the script path if needed).
- Never overwrite `parts/part_*.jsonl` files; create new `*_fixed.jsonl` or `part_###_v2.jsonl`.
- Treat `dataset_clean.*` as generated artifacts: safe to delete/regenerate anytime.

## Notes
- `preprocessed_ar` is **script-derived** normalization (not LLM-generated).
- `priority` is enforced by the rule: `round((impact + urgency)/2)` clamped to 1..5.
