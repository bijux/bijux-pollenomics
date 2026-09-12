"""Immutable source and output identities for the admission audit."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, cast


@dataclass(frozen=True)
class SourceRow:
    """Exact declared part/row locator with an immutable serialized source row."""

    surface: str
    path: str
    row_index: int
    canonical_json: bytes

    def payload(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self.canonical_json))

    def locator(self) -> dict[str, object]:
        return {
            "authority": "normalized",
            "surface": self.surface,
            "path": self.path,
            "row_index": self.row_index,
            "row_sha256": hashlib.sha256(self.canonical_json).hexdigest(),
        }


@dataclass(frozen=True)
class AdmissionReport:
    """An accounting projection, never an accepted scientific reconstruction."""

    output_directory: Path
    manifest_sha256: str
    available_samples: int
    selected_samples: int
    available_observations: int
    selected_observations: int


def canonical_bytes(value: object) -> bytes:
    """Serialize audit values without coercing source scalars or missing values."""
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def producer_identity() -> dict[str, object]:
    """Conservatively bind all host Python implementation bytes used by the audit."""
    root = Path(__file__).resolve().parents[3]
    records = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in sorted(root.rglob("*.py"))
    ]
    return {
        "scope": "bijux_pollenomics_python_package",
        "files": records,
        "sha256": hashlib.sha256(canonical_bytes(records)).hexdigest(),
    }
