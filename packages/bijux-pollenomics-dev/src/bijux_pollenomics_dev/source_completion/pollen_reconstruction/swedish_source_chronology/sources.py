"""Authenticate captured aggregate inputs without admitting new raw sources."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from bijux_pollenomics_dev.ci.report_rebuild.source_paths import safe_source_file

from .authority import CAPTURE_PINS, DESCRIPTOR, DESCRIPTOR_SHA256, FAMILY


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, child in pairs:
        if key in value:
            raise ValueError("duplicate captured JSON key")
        value[key] = child
    return value


def _finite(value: object) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("nonfinite captured JSON value")
    if isinstance(value, dict):
        for child in value.values():
            _finite(child)
    if isinstance(value, list):
        for child in value:
            _finite(child)


def load_inputs(repository: Path) -> dict[str, dict]:
    """Require all original bytes, including the failed capture predecessors."""
    values = {}
    for relative, expected in {DESCRIPTOR: DESCRIPTOR_SHA256, **CAPTURE_PINS}.items():
        source = safe_source_file(repository, relative, "Tibetanus retained source")
        body = source.read_bytes()
        if hashlib.sha256(body).hexdigest() != expected:
            raise ValueError("Tibetanus retained source bytes changed")
        value = json.loads(body, object_pairs_hook=_pairs)
        if not isinstance(value, dict):
            raise ValueError("Tibetanus retained source must be an object")
        _finite(value)
        values[relative.removeprefix(FAMILY + "/")] = value
    descriptor = values["inputs/retained-source-identities.json"]
    if descriptor["files_sha256"] != CAPTURE_PINS:
        raise ValueError("Tibetanus source descriptor membership changed")
    if values["report.json"]["protocol"] != values["assumptions/protocol.json"]:
        raise ValueError("Tibetanus captured protocol differs")
    return values
