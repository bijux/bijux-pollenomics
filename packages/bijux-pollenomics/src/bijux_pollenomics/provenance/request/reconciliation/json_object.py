"""Read optional governed JSON objects with fail-closed semantics."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from ...release_evidence.models import ReleaseEvidenceError
from ...release_evidence.repository import _read_repository_file


def optional_json_object(root: Path, relative_path: str) -> Mapping[str, object] | None:
    """Return an object or unavailable posture for absent and malformed JSON."""
    try:
        value = json.loads(_read_repository_file(root, relative_path))
    except (ReleaseEvidenceError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, Mapping) else None
