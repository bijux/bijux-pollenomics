"""Admit exact scalar-reference account bytes and their separate retained owners."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import _regular_confined_file


def validated_scalar_reference_account(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
    *,
    owner_id: str,
    product: str,
    sha256: str,
    size: int,
    schema: str,
    label: str,
    scope: str,
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Require one separate exact owner and reviewed product; preserve old captures."""
    selected = [row for row in owners if row.get("owner_id") == owner_id]
    touching = []
    for row in owners:
        paths = row.get("paths", [])
        if not isinstance(paths, list) or any(
            not isinstance(name, str) for name in paths
        ):
            raise ReportRebuildError(f"{label} owner paths must be strings")
        if product in paths:
            touching.append(row)
    if not selected and not touching and product not in tracked_by_path:
        return (), {}
    if len(selected) != 1 or touching != selected:
        raise ReportRebuildError(f"{label} owner differs")
    owner = selected[0]
    if (
        owner.get("role") != "retained_source"
        or owner.get("paths") != [product]
        or owner.get("producer_paths") != []
        or owner.get("producer_inputs") != []
    ):
        raise ReportRebuildError(f"{label} declaration differs")
    try:
        path = _regular_confined_file(repository, product, label)
        info = path.stat()
        if info.st_nlink != 1 or info.st_size != size:
            raise ReportRebuildError(f"{label} physical identity differs")
        body = path.read_bytes()
        entry = tracked_by_path.get(product)
        if (
            len(body) != size
            or hashlib.sha256(body).hexdigest() != sha256
            or entry is None
            or entry.kind != "file"
            or entry.size != size
            or entry.sha256 != sha256
        ):
            raise ReportRebuildError(f"{label} bytes changed")
        value = json.loads(body)
        if not isinstance(value, dict) or value["schema_version"] != schema:
            raise ReportRebuildError(f"{label} schema differs")
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise ReportRebuildError(f"{label} input refused") from error
    assert entry is not None
    return (entry,), {
        "owner_id": owner_id,
        "reviewed_capture_sha256": {product: sha256},
        "paths": [entry.path],
        "original_epochs": value["epochs"],
        "new_R_kernel_moment_or_model_calls": 0,
        "scope": scope,
    }
