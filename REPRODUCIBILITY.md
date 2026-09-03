# Reproducibility record

## Licence

Dataset and non-software research materials are licensed CC BY-NC 4.0. Source
code is licensed AGPL-3.0-or-later. The repository's `LICENSE` file defines the
file-category mapping.

This repository is the release source for ArabicITSM-9K. It contains the generation and repair contracts, taxonomy, retained raw output, validation and analysis scripts, final dataset, cross-generator test set, and privacy-safe expert-audit materials.

## Provenance boundaries

- All 10,000 released records identify `gemini-3-flash` in the `model` field.
- `prompts/generation_v1.md` is the production generation contract.
- `prompts/fixer_v1.md` is the same-generator repair contract.
- Intermediate rejection/repair artifacts and execution logs were not retained. Exact repair counts, error frequencies, and repaired-ticket identities therefore cannot be reconstructed.
- `scripts/generate_tickets_local.py` is a template-based development utility and was not used as the production LLM generator.
- `cross_generator_test.*` contains 144 Claude Sonnet 4.6 tickets, three per L3 class. It is a cross-generator synthetic test, not authentic ITSM data.
- `scripts/sample_for_annotation.py` records the deterministic audit-sampling procedure, `assets/annotation_template.csv` is the blank rating instrument, and `assets/iaa_results.json` contains aggregate agreement results. Completed individual rating sheets and signed consent records are not part of this public release because the consent terms permit aggregate reporting only.

## Primary file checksums

SHA-256 checksums for the version 1.0.0 release source:

```text
5EF7BC752E074708B754E628324AD95F7D0D7C443679AAA0874164EF307928CE  dataset_clean.csv
1CD0A73F165DA24EFD448ADFEBABDFD1F92375051E09127FD0058E2D6D5D64E2  dataset_clean.jsonl
4BA4746F0DB8CE032C817D42289557DD32F121A3A5F161914AEA086118D246B7  parts/part_001.jsonl
13DDAF51A82AE03392E150E26209446D20E87C41B27DB36BA8821D5794CA8C8D  cross_generator_test.csv
5EDF725C6D7C2CF3FB9477D607E97F3EE18BFA3947F32B7BF889557F8E628D09  cross_generator_test.jsonl
B66073CEA239D0D2DF01A34B4C54E6A8763C241B5B6C9E4209ACD2B764F44EAC  assets/iaa_results.json
A6D2D1ABA57743A4EFBEB9DF02E1260CBBAEC5999C51293B742B5FA91CBC41D5  assets/annotation_template.csv
```

## Build and validation

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python scripts/build_dataset.py
python scripts/dq_report.py dataset_clean.jsonl
```

Rebuilding writes `dataset_clean.csv` and `dataset_clean.jsonl` from `parts/part_*.jsonl`. Historical repair intermediates are not required to validate or use the released dataset and are not recoverable.

## Related release

Training, fixed splits, saved evaluation metrics, and analysis code are released separately at <https://github.com/bazokhan/arabic-itsm-classification>.
