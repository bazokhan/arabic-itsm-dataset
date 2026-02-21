"""
One-time script to create and populate the Hugging Face dataset repo.
Run this after `hf login` (or `.venv\Scripts\hf.exe login`).
"""

from huggingface_hub import HfApi

REPO_ID = "albaz2000/arabic-itsm-dataset"
FILES = ["dataset_clean.csv", "dataset_clean.jsonl"]

api = HfApi()

api.create_repo(REPO_ID, repo_type="dataset", exist_ok=True)
print(f"Repo ready: https://huggingface.co/datasets/{REPO_ID}")

for filename in FILES:
    print(f"Uploading {filename} ...")
    api.upload_file(
        path_or_fileobj=filename,
        path_in_repo=filename,
        repo_id=REPO_ID,
        repo_type="dataset",
    )
    print(f"  done: {filename}")

print("\nAll files pushed.")
print(f"View at: https://huggingface.co/datasets/{REPO_ID}")
