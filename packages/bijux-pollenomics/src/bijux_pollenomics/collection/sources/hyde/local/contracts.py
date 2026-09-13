"""Bounded byte-custody contracts, independent of native scientific interpretation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re

from ...quarantine import IntakeRefusal

SCHEMA = "hyde-local-custody.v1"
POSTURE: dict[str, object] = {
    "custody_status": "local_bytes_inventoried",
    "requested_release_scope": "3.5",
    "native_release_status": "unverified",
    "scientific_acceptance": "not_evaluated",
    "public_release_allowed": False,
    "evidence_role": "modeled_context_pending_source_review",
    "native_metadata_interpretation": "not_performed",
    "archive_payload_verification": "not_performed",
}
REVIEW_REQUIRED = (
    "release_identity",
    "release_specific_rights",
    "native_time_convention",
    "variable_units_and_missingness",
    "grid_geometry",
    "scenario_semantics",
    "source_independence",
)


@dataclass(frozen=True)
class LocalInventoryLimits:
    """Bounds on memory, metadata and byte-stream buffers; native size is unrestricted."""

    chunk_bytes: int = 4 * 1024 * 1024
    maximum_files: int = 100_000
    maximum_archive_members: int = 100_000
    maximum_central_directory_bytes: int = 16 * 1024 * 1024
    maximum_metadata_file_bytes: int = 64 * 1024
    maximum_metadata_total_bytes: int = 1024 * 1024
    maximum_retained_bytes: int = 32 * 1024 * 1024

    def __post_init__(self) -> None:
        caps = {
            "chunk_bytes": 8 * 1024 * 1024,
            "maximum_files": 100_000,
            "maximum_archive_members": 100_000,
            "maximum_central_directory_bytes": 16 * 1024 * 1024,
            "maximum_metadata_file_bytes": 64 * 1024,
            "maximum_metadata_total_bytes": 1024 * 1024,
            "maximum_retained_bytes": 32 * 1024 * 1024,
        }
        for name, value in vars(self).items():
            if type(value) is not int or value <= 0 or value > caps[name]:
                raise IntakeRefusal("hyde_custody_limit_invalid", name)
        if self.chunk_bytes > 8 * 1024 * 1024:
            raise IntakeRefusal("hyde_custody_limit_invalid", "chunk_bytes exceeds8MiB")


@dataclass(frozen=True)
class LocalHydeInventory:
    """An authenticated compact inventory; it grants no scientific or public admission."""

    directory: Path
    manifest_sha256: str
    file_count: int
    byte_count: int
    dataset_file_count: int
    dataset_byte_count: int
    archive_member_count: int
    dataset_inventory_sha256: str


def object_fields(value: object, fields: set[str], label: str) -> dict[str, object]:
    if (
        not isinstance(value, Mapping)
        or set(value) != fields
        or any(not isinstance(k, str) for k in value)
    ):
        raise IntakeRefusal("hyde_custody_schema_invalid", label)
    return dict(value)


def array(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise IntakeRefusal("hyde_custody_schema_invalid", label)
    return list(value)


def integer(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise IntakeRefusal("hyde_custody_integer_invalid", label)
    return value


def text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise IntakeRefusal("hyde_custody_text_invalid", label)
    return value


def relative_path(value: object) -> str:
    name = text(value, "relative_path")
    if (
        Path(name).is_absolute()
        or Path(name).as_posix() != name
        or any(p in {"", ".", ".."} for p in name.split("/"))
    ):
        raise IntakeRefusal("hyde_custody_path_invalid", name)
    return name


def digest(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise IntakeRefusal("hyde_custody_digest_invalid", repr(value))
    return value


def encode(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def decode(content: bytes) -> object:
    value: object = json.loads(content, object_pairs_hook=_unique)
    if encode(value) != content:
        raise IntakeRefusal(
            "hyde_custody_noncanonical_json", "Exact canonical representation required"
        )
    return value


def checked_path(value: Path) -> Path:
    """Refuse symlink ancestors before and after lexical absolute normalization."""
    result = Path(os.path.abspath(value))
    for path in (value, *value.parents, result, *result.parents):
        if path.is_symlink():
            raise IntakeRefusal("hyde_custody_path_symlink", str(path))
    return result


def implementation_identity() -> dict[str, str]:
    """Bind owned/source-imported Python files, not cached loaded-runtime attestation."""
    owner = Path(__file__).resolve().parent
    package = owner.parents[3]
    paths = set(owner.glob("*.py")) | set(owner.parent.glob("*.py"))
    paths.update((owner.parent.parent / "quarantine").glob("*.py"))
    paths.add(package / "core/owned_tree.py")
    for parent in (owner, *owner.parents):
        if parent == package.parent:
            break
        initializer = parent / "__init__.py"
        if initializer.is_file():
            paths.add(initializer)
    return {
        path.relative_to(package).as_posix(): sha256(path.read_bytes())
        for path in sorted(paths)
    }
