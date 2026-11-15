"""Proof buffers keep their independent size and digest gate before decoding."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from typing import Any

from ...receipts import _object, _read, _safe_root
from ..models import EVIDENCE_SCHEMA

Reader = Callable[[Path, str, int], bytes]


def _part(
    root: Path, descriptor: dict[str, Any], *, reader: Reader | None = None
) -> list[dict[str, Any]]:
    path = _safe_root(root / "proofs" / (descriptor["sha256"] + ".json"))
    raw = (
        _read(path, descriptor["bytes"])
        if reader is None
        else reader(path, descriptor["sha256"], descriptor["bytes"])
    )
    if (
        type(raw) is not bytes
        or len(raw) != descriptor["bytes"]
        or sha256(raw).hexdigest() != descriptor["sha256"]
    ):
        raise ValueError("Linked evidence proof part identity differs")
    value = _object(raw)
    if (
        set(value) != {"schema_version", "proofs"}
        or value["schema_version"] != EVIDENCE_SCHEMA
        or not isinstance(value["proofs"], list)
        or len(value["proofs"]) != descriptor["rows"]
        or any(not isinstance(row, dict) for row in value["proofs"])
    ):
        raise ValueError("Linked evidence proof part population differs")
    return value["proofs"]
