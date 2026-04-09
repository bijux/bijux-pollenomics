from __future__ import annotations

import json
from pathlib import Path


def write_json(path: Path, payload: object) -> None:
    """Write JSON with stable formatting."""
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    """Write UTF-8 text content."""
    path.write_text(content, encoding="utf-8")
