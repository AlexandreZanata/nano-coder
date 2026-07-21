"""Load project .env into os.environ (setdefault — does not override existing vars)."""

from __future__ import annotations

import os
from pathlib import Path


def load_project_env(project_root: Path | None = None) -> bool:
    """Load ``.env`` from project root. Returns True if file was found."""
    root = project_root or Path(__file__).resolve().parents[1]
    env_path = root / ".env"
    if not env_path.is_file():
        return False
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)
    return True
