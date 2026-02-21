"""
One-time script to create the Hugging Face dataset repo and do the initial push.
Run this after logging in: .venv\Scripts\hf.exe login

After this, future syncs are handled automatically by the GitHub Action.
"""

from huggingface_hub import HfApi

REPO_ID = "albaz2000/arabic-itsm-dataset"

api = HfApi()
api.create_repo(REPO_ID, repo_type="dataset", exist_ok=True)
print(f"Repo ready: https://huggingface.co/datasets/{REPO_ID}")

# Delegate to sync_hf.py for the actual upload
import subprocess, sys
subprocess.run([sys.executable, "scripts/sync_hf.py"], check=True)
