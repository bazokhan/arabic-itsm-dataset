"""
Sync dataset files and README to the Hugging Face Hub.
Requires HF_TOKEN env var (write access).
Run locally or via the GitHub Action.
"""

import os
from huggingface_hub import HfApi

REPO_ID = "albaz2000/arabic-itsm-dataset"
DATA_FILES = ["dataset_clean.csv", "dataset_clean.jsonl"]

api = HfApi(token=os.environ["HF_TOKEN"])

# ── Data files ────────────────────────────────────────────────────────
for filename in DATA_FILES:
    print(f"Uploading {filename} ...")
    api.upload_file(
        path_or_fileobj=filename,
        path_in_repo=filename,
        repo_id=REPO_ID,
        repo_type="dataset",
    )
    print(f"  done.")

# ── Dataset card (README) ─────────────────────────────────────────────
# HF dataset cards need a YAML frontmatter block at the top.
# We keep that in hf_readme_header.md and append the GitHub README below it.
with open("hf_readme_header.md", encoding="utf-8") as f:
    header = f.read().strip()

with open("README.md", encoding="utf-8") as f:
    body = f.read().strip()

hf_readme = header + "\n\n" + body

print("Uploading README.md (dataset card) ...")
api.upload_file(
    path_or_fileobj=hf_readme.encode("utf-8"),
    path_in_repo="README.md",
    repo_id=REPO_ID,
    repo_type="dataset",
)
print("  done.")

print(f"\nAll synced → https://huggingface.co/datasets/{REPO_ID}")
