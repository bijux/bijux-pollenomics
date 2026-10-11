"""Bounded byte-custody contracts, independent of native scientific interpretation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat

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


ARCHIVE_FIELDS = {
    "archive_path",
    "archive_sha256",
    "member_index",
    "name",
    "decoded_filename",
    "name_occurrence",
    "name_occurrences",
    "bytes",
    "compressed_bytes",
    "crc32",
    "header_offset",
    "compression",
    "flags",
    "date_time",
    "create_system",
    "create_version",
    "extract_version",
    "internal_attributes",
    "external_attributes",
    "comment_hex",
    "extra_hex",
    "directory",
    "symlink",
    "safe_relative_name",
    "extraction_allowed",
}


def safe_member_name(name: str) -> bool:
    """A diagnostic only; no member is eligible for extraction through this API."""
    return not (
        PurePosixPath(name).is_absolute()
        or PureWindowsPath(name).drive
        or ".." in PurePosixPath(name).parts
        or "\\" in name
        or "\x00" in name
    )


def validate_archive_occurrence(value: object, archive_bytes: int) -> dict[str, object]:
    """Admit one native occurrence through the shared custody field/semantic rules."""
    row = object_fields(value, ARCHIVE_FIELDS, "archive occurrence")
    archive = relative_path(row["archive_path"])
    digest(row["archive_sha256"])
    integer(archive_bytes, "archive bytes")
    if Path(archive).suffix.casefold() != ".zip":
        raise IntakeRefusal("hyde_custody_archive_parent_invalid", archive)
    if not isinstance(row["name"], str) or not isinstance(row["decoded_filename"], str):
        raise IntakeRefusal("hyde_custody_archive_name_invalid", archive)
    name = row["name"]
    for field in ARCHIVE_FIELDS - {
        "archive_path",
        "archive_sha256",
        "name",
        "decoded_filename",
        "comment_hex",
        "extra_hex",
        "date_time",
        "directory",
        "symlink",
        "safe_relative_name",
        "extraction_allowed",
    }:
        integer(row[field], field)
    for field in ("comment_hex", "extra_hex"):
        hexadecimal = row[field]
        if (
            not isinstance(hexadecimal, str)
            or re.fullmatch(r"(?:[0-9a-f]{2})*", hexadecimal) is None
        ):
            raise IntakeRefusal("hyde_custody_archive_hex_invalid", field)
    date = array(row["date_time"], "date_time")
    if len(date) != 6:
        raise IntakeRefusal("hyde_custody_archive_date_invalid", archive)
    for component in date:
        integer(component, "date_time")
    for field in (
        "directory",
        "symlink",
        "safe_relative_name",
        "extraction_allowed",
    ):
        if type(row[field]) is not bool:
            raise IntakeRefusal("hyde_custody_archive_flag_invalid", field)
    safe = safe_member_name(name)
    if (
        row["decoded_filename"] != name.split("\x00", 1)[0]
        or row["directory"] != str(row["decoded_filename"]).endswith("/")
        or row["safe_relative_name"] != safe
        or row["symlink"]
        != stat.S_ISLNK(integer(row["external_attributes"], "attributes") >> 16)
        or row["extraction_allowed"] is not False
    ):
        raise IntakeRefusal("hyde_custody_archive_semantics_invalid", archive)
    if (
        integer(row["crc32"], "crc32") > 0xFFFFFFFF
        or integer(row["header_offset"], "offset")
        + integer(row["compressed_bytes"], "compressed")
        > archive_bytes
    ):
        raise IntakeRefusal("hyde_custody_archive_bounds_invalid", archive)
    return row


@dataclass(frozen=True)
class BoundArchiveMember:
    """One custody-authenticated ZIP occurrence, without native payload admission."""

    custody_manifest_sha256: str
    dataset_inventory_sha256: str
    archive_path: str
    archive_sha256: str
    archive_bytes: int
    member_index: int
    name: str
    occurrence_json: str
    archive_directory_json: str

    def __post_init__(self) -> None:
        for value in (
            self.custody_manifest_sha256,
            self.dataset_inventory_sha256,
            self.archive_sha256,
        ):
            digest(value)
        relative_path(self.archive_path)
        integer(self.archive_bytes, "archive bytes")
        integer(self.member_index, "member index")
        if not isinstance(self.name, str):
            raise IntakeRefusal(
                "hyde_custody_archive_name_invalid", "Native name must be text"
            )
        row = self.occurrence()
        if (
            row["archive_path"] != self.archive_path
            or row["archive_sha256"] != self.archive_sha256
            or row["member_index"] != self.member_index
            or row["name"] != self.name
        ):
            raise IntakeRefusal("hyde_custody_bound_member_mismatch", self.archive_path)
        directory = object_fields(
            decode(self.archive_directory_json.encode("ascii")),
            {
                "profile",
                "member_count",
                "comment_hex",
                "zip64",
                "central_directory_bytes",
                "central_directory_offset",
            },
            "bound archive directory",
        )
        if (
            directory["profile"] != "zip-central-directory-v1"
            or type(directory["zip64"]) is not bool
            or integer(directory["member_count"], "member count") <= self.member_index
        ):
            raise IntakeRefusal("hyde_custody_bound_member_mismatch", self.archive_path)
        if (
            integer(directory["central_directory_bytes"], "directory bytes")
            + integer(directory["central_directory_offset"], "directory offset")
            > self.archive_bytes
        ):
            raise IntakeRefusal("hyde_custody_bound_member_mismatch", self.archive_path)

    def occurrence(self) -> dict[str, object]:
        """Return an owned occurrence admitted by the same rules as full custody."""
        row = validate_archive_occurrence(
            decode(self.occurrence_json.encode("ascii")), self.archive_bytes
        )
        if integer(row["name_occurrence"], "occurrence") >= integer(
            row["name_occurrences"], "occurrences"
        ):
            raise IntakeRefusal("hyde_custody_bound_member_mismatch", self.archive_path)
        return row
