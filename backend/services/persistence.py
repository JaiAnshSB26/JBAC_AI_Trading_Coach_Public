"""
backend.services.persistence

Tiny file-based persistence for demo users. Provides `load_user` and
`save_user` helpers that store JSON blobs under a configurable data
directory. This is intentionally simple for local development; in production
replace with S3 or a database.
"""

import os, json
from pathlib import Path

# Use /tmp for Lambda (read-only filesystem elsewhere)
# Falls back to .data for local development
default_dir = "/tmp" if os.getenv("AWS_EXECUTION_ENV") else ".data"
DATA_DIR = Path(os.getenv("DATA_DIR", default_dir))
DATA_DIR.mkdir(exist_ok=True)

def load_user(user_id: str):
    p = DATA_DIR / f"{user_id}.json"
    if p.exists():
        return json.loads(p.read_text())
    return None

def save_user(user_id: str, obj: dict):
    p = DATA_DIR / f"{user_id}.json"
    p.write_text(json.dumps(obj, indent=2))