"""Read source references only after exact path and byte validation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ...contracts import ValidationRefusal, canonical_json
from .model import InputReference, object_mapping


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON field: {key}")
        result[key] = value
    return result


def _reference_bytes(root: Path, reference: InputReference) -> bytes:
    """Verify exact bytes inside a real, nonsymlink input root."""
    root = root.absolute()
    target = root / reference.path
    try:
        if root.is_symlink() or any(
            path.is_symlink()
            for path in (target, *target.parents)
            if path == root or root in path.parents
        ):
            raise ValueError("Symbolic links are not admitted")
        target.resolve(strict=True).relative_to(root.resolve(strict=True))
        if not target.is_file():
            raise ValueError("Input must be a regular file")
        content = target.read_bytes()
        if hashlib.sha256(content).hexdigest() != reference.sha256:
            raise ValueError("Input bytes differ from the frozen reference")
        return content
    except (OSError, ValueError, TypeError) as exc:
        raise ValidationRefusal(
            "invalid_experiment_input", f"{reference.path}: {exc}"
        ) from exc


def read_reference(root: Path, reference: InputReference) -> dict[str, object]:
    """Parse finite JSON from a verified raw or geometric source reference."""
    content = _reference_bytes(root, reference)
    try:
        value = json.loads(content, object_pairs_hook=_unique_pairs)
        canonical_json(value)
        return object_mapping(value, reference.path)
    except (ValueError, TypeError) as exc:
        raise ValidationRefusal(
            "invalid_experiment_input", f"{reference.path}: {exc}"
        ) from exc
