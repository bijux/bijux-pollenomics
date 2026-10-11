"""Shared paths for LandClim published-inventory tests."""

from __future__ import annotations

from pathlib import Path

from tests.support.repository import REPOSITORY_ROOT

RAW_ROOT = REPOSITORY_ROOT / "data" / "landclim" / "raw"


def source_path(filename: str) -> Path:
    """Return one governed LandClim raw path."""
    return RAW_ROOT / filename
