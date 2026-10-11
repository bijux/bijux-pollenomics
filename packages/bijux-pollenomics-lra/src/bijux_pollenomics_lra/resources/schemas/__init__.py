"""Access to the package's versioned JSON Schemas."""

from __future__ import annotations

from importlib.resources import files
import json
from pathlib import Path
from typing import Any

SCHEMAS = (
    "run-manifest.schema.json",
    "extension-descriptor.schema.json",
)


def schema_path(name: str) -> Path:
    """Return a filesystem path for a bundled schema."""
    if name not in SCHEMAS:
        raise KeyError(f"Unknown schema {name!r}; available: {SCHEMAS}")
    return Path(str(files(__package__).joinpath(name)))


def load_schema(name: str) -> dict[str, Any]:
    """Load a bundled JSON Schema by filename."""
    if name not in SCHEMAS:
        raise KeyError(f"Unknown schema {name!r}; available: {SCHEMAS}")
    resource = files(__package__).joinpath(name)
    return json.loads(resource.read_text(encoding="utf-8"))


__all__ = ["SCHEMAS", "load_schema", "schema_path"]
