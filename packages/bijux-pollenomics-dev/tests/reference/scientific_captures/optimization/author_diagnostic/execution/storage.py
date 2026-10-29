"""Exclusive scientific observations beneath their admitted output root."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def destination(root: Path, path: Path) -> Path:
    if (
        not root.is_absolute()
        or root.resolve() != root
        or not path.is_absolute()
        or not path.is_relative_to(root)
        or path == root
        or ".." in path.parts
        or path.resolve() != path
    ):
        raise ValueError("Output must be a normalized child of its admitted root")
    if any(p.is_symlink() for p in (path, *path.parents)) or path.exists():
        raise ValueError("Output is linked or already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_json(root: Path, path: Path, value: Any) -> None:
    target = destination(root, path)
    with target.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
