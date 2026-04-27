"""Load repo-root `.env` before other `server` imports read `os.environ`."""

import os
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[1]
if os.getenv("SKIP_DOTENV", "").strip().lower() not in ("1", "true", "yes"):
    load_dotenv(_REPO_ROOT / ".env")
