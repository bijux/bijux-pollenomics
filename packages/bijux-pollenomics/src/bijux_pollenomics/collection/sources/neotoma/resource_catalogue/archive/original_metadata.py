"""Pin only original dataset metadata; the relational numerical snapshot is not copied."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import stat
from typing import Any

from ...capture.receipts import _object, _read, _safe_root
from ..custody import _original_metadata
from .files import MAX_BYTES, MAX_FILES, _digest, _member

_PREFIX = "captures/original-metadata/"
_SCOPE = "original_relational_dataset_metadata_only"
_FIELDS = {
    "scope",
    "manifest_path",
    "manifest_sha256",
    "dataset_row_count",
    "dataset_part_count",
}


def preflight_metadata(root: Path) -> tuple[dict[str, Any], dict[str, str]]:
    """Bound the declared ordinary metadata files before any part buffer opens."""
    root = _safe_root(root)
    raw = _read(root / "manifest.json", 1024 * 1024)
    if (root / "manifest.json").stat().st_nlink != 1:
        raise ValueError("Original metadata witness manifest is not an ordinary file")
    manifest = _object(raw)
    surfaces = manifest.get("surfaces")
    surface = surfaces.get("datasets") if isinstance(surfaces, dict) else None
    if (
        not isinstance(surface, dict)
        or type(surface.get("row_count")) is not int
        or surface["row_count"] < 0
        or not isinstance(surface.get("parts"), list)
        or len(surface["parts"]) + 1 > MAX_FILES
    ):
        raise ValueError("Original metadata witness dataset population is malformed")
    members = {"manifest.json": sha256(raw).hexdigest()}
    total = len(raw)
    for part in surface["parts"]:
        if not isinstance(part, dict) or not _digest(part.get("sha256")):
            raise ValueError("Original metadata witness part identity is malformed")
        relative = _member(part.get("path"))
        if not relative.startswith("surfaces/datasets/") or relative in members:
            raise ValueError("Original metadata witness dataset part scope differs")
        path = _safe_root(root / relative)
        try:
            identity = path.stat(follow_symlinks=False)
        except OSError as error:
            raise ValueError("Original metadata witness part is unavailable") from error
        if (
            not stat.S_ISREG(identity.st_mode)
            or identity.st_nlink != 1
            or identity.st_size > 16 * 1024 * 1024
        ):
            raise ValueError(
                "Original metadata witness part is not bounded and regular"
            )
        total += identity.st_size
        if total > MAX_BYTES:
            raise ValueError("Original metadata witness exceeds its finite byte budget")
        members[relative] = part["sha256"]
    return surface, members


def metadata_inventory(root: Path) -> tuple[dict[str, Any], dict[str, str]]:
    """Authenticate the native metadata owner and its exact minimal file closure."""
    surface, members = preflight_metadata(root)
    originals, _ = _original_metadata(root)
    if originals is None or len(originals) != surface["row_count"]:
        raise ValueError("Original metadata witness dataset population differs")
    return {
        "scope": _SCOPE,
        "manifest_path": _PREFIX + "manifest.json",
        "manifest_sha256": members["manifest.json"],
        "dataset_row_count": len(originals),
        "dataset_part_count": len(surface["parts"]),
    }, members


def resolve_original_metadata(
    root: Path, claim: object, external: Path | None
) -> tuple[Path, set[str]]:
    """Use internal bytes; an explicitly supplied external witness must agree."""
    if (
        not isinstance(claim, dict)
        or set(claim) != _FIELDS
        or claim["scope"] != _SCOPE
        or claim["manifest_path"] != _PREFIX + "manifest.json"
        or not _digest(claim["manifest_sha256"])
        or any(
            type(claim[name]) is not int or claim[name] < 0
            for name in ("dataset_row_count", "dataset_part_count")
        )
    ):
        raise ValueError("Original metadata witness fields or scope differ")
    internal = root / "captures/original-metadata"
    actual, members = metadata_inventory(internal)
    if actual != claim:
        raise ValueError("Original metadata witness differs from its native source")
    if external is not None:
        other, external_members = metadata_inventory(external)
        if other != actual or external_members != members:
            raise ValueError(
                "External original metadata conflicts with archive witness"
            )
    return internal, {_PREFIX + relative for relative in members}
