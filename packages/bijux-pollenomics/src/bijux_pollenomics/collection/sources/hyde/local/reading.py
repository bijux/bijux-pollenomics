"""Strict retained schema/identity validation and full external byte replay."""

from __future__ import annotations

import base64
from collections import Counter
from dataclasses import asdict
from pathlib import Path
import re
import zipfile

from ...quarantine import IntakeRefusal
from .archives import safe_member_name
from .contracts import (
    POSTURE,
    REVIEW_REQUIRED,
    SCHEMA,
    LocalHydeInventory,
    LocalInventoryLimits,
    array,
    checked_path,
    decode,
    digest,
    encode,
    implementation_identity,
    integer,
    object_fields,
    relative_path,
    sha256,
)
from .inventory import (
    collect_sources,
    metadata_candidate,
    source_snapshot,
    summary,
    unchanged,
)

_MEMBERS = {"files.json", "archives.json", "metadata.json"}
_ARCHIVE_FIELDS = {
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


def _owned_bytes(root: Path) -> dict[str, bytes]:
    root = checked_path(root)
    if (
        root.is_symlink()
        or not root.is_dir()
        or {p.name for p in root.iterdir()} != _MEMBERS | {"manifest.json"}
    ):
        raise IntakeRefusal("hyde_custody_inventory_invalid", str(root))
    result = {}
    total = 0
    for name in sorted(_MEMBERS | {"manifest.json"}):
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise IntakeRefusal("hyde_custody_member_invalid", name)
        with path.open("rb") as stream:
            value = stream.read(LocalInventoryLimits().maximum_retained_bytes + 1)
        total += len(value)
        if total > LocalInventoryLimits().maximum_retained_bytes + 65_536:
            raise IntakeRefusal("hyde_custody_output_limit", str(total))
        result[name] = value
    return result


def _file_rows(value: object, limits: LocalInventoryLimits) -> list[dict[str, object]]:
    rows = []
    names = []
    for item in array(value, "files"):
        row = object_fields(
            item,
            {"path", "bytes", "sha256", "classification", "archive_directory"},
            "file",
        )
        name = relative_path(row["path"])
        integer(row["bytes"], "bytes")
        digest(row["sha256"])
        if row["classification"] != (
            "ancillary" if Path(name).name == ".DS_Store" else "dataset"
        ):
            raise IntakeRefusal("hyde_custody_classification_invalid", name)
        if Path(name).suffix.casefold() == ".zip":
            directory = object_fields(
                row["archive_directory"],
                {
                    "profile",
                    "member_count",
                    "comment_hex",
                    "zip64",
                    "central_directory_bytes",
                    "central_directory_offset",
                },
                "archive directory",
            )
            if (
                directory["profile"] != "zip-central-directory-v1"
                or not isinstance(directory["comment_hex"], str)
                or re.fullmatch(r"(?:[0-9a-f]{2})*", directory["comment_hex"]) is None
            ):
                raise IntakeRefusal("hyde_custody_archive_directory_invalid", name)
            integer(directory["member_count"], "member_count")
            if (
                type(directory["zip64"]) is not bool
                or integer(directory["central_directory_bytes"], "directory bytes")
                > limits.maximum_central_directory_bytes
                or integer(directory["central_directory_offset"], "directory offset")
                + integer(directory["central_directory_bytes"], "directory bytes")
                > integer(row["bytes"], "archive bytes")
            ):
                raise IntakeRefusal("hyde_custody_archive_directory_invalid", name)
        elif row["archive_directory"] is not None:
            raise IntakeRefusal("hyde_custody_archive_directory_invalid", name)
        rows.append(row)
        names.append(name)
    if not rows or names != sorted(set(names)) or len(rows) > limits.maximum_files:
        raise IntakeRefusal(
            "hyde_custody_file_inventory_invalid",
            "sorted unique nonempty files required",
        )
    return rows


def _archive_rows(
    value: object, files: dict[str, dict[str, object]], limits: LocalInventoryLimits
) -> list[dict[str, object]]:
    import stat

    rows = []
    groups: dict[str, list[dict[str, object]]] = {}
    for item in array(value, "archives"):
        row = object_fields(item, _ARCHIVE_FIELDS, "archive occurrence")
        archive = relative_path(row["archive_path"])
        if (
            archive not in files
            or Path(archive).suffix.casefold() != ".zip"
            or row["archive_sha256"] != files[archive]["sha256"]
        ):
            raise IntakeRefusal("hyde_custody_archive_parent_invalid", archive)
        if not isinstance(row["name"], str) or not isinstance(
            row["decoded_filename"], str
        ):
            raise IntakeRefusal("hyde_custody_archive_name_invalid", archive)
        name = row["name"]
        for field in _ARCHIVE_FIELDS - {
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
        if integer(row["crc32"], "crc32") > 0xFFFFFFFF or integer(
            row["header_offset"], "offset"
        ) + integer(row["compressed_bytes"], "compressed") > integer(
            files[archive]["bytes"], "archive bytes"
        ):
            raise IntakeRefusal("hyde_custody_archive_bounds_invalid", archive)
        groups.setdefault(archive, []).append(row)
        rows.append(row)
    if len(rows) > limits.maximum_archive_members or [
        str(row["archive_path"]) for row in rows
    ] != sorted(str(row["archive_path"]) for row in rows):
        raise IntakeRefusal("hyde_custody_archive_inventory_invalid", "order or limit")
    for archive, source in files.items():
        if source["archive_directory"] is not None:
            directory = object_fields(
                source["archive_directory"],
                {
                    "profile",
                    "member_count",
                    "comment_hex",
                    "zip64",
                    "central_directory_bytes",
                    "central_directory_offset",
                },
                "archive directory",
            )
            if directory["member_count"] != len(groups.get(archive, [])):
                raise IntakeRefusal("hyde_custody_archive_inventory_invalid", archive)
    for archive, members in groups.items():
        totals = Counter(str(row["name"]) for row in members)
        seen: Counter[str] = Counter()
        for index, row in enumerate(members):
            name = str(row["name"])
            if (
                row["member_index"] != index
                or row["name_occurrence"] != seen[name]
                or row["name_occurrences"] != totals[name]
            ):
                raise IntakeRefusal("hyde_custody_occurrence_invalid", archive)
            seen[name] += 1
    return rows


def _metadata(
    value: object, files: dict[str, dict[str, object]], limits: LocalInventoryLimits
) -> None:
    names = []
    captured = 0
    for item in array(value, "metadata"):
        row = object_fields(
            item,
            {"path", "sha256", "bytes", "capture_status", "bytes_base64"},
            "metadata",
        )
        name = relative_path(row["path"])
        if (
            name not in files
            or row["sha256"] != files[name]["sha256"]
            or row["bytes"] != files[name]["bytes"]
        ):
            raise IntakeRefusal("hyde_custody_metadata_parent_invalid", name)
        size = integer(row["bytes"], "metadata bytes")
        expected = (
            size <= limits.maximum_metadata_file_bytes
            and captured + size <= limits.maximum_metadata_total_bytes
        )
        if expected:
            if not isinstance(row["bytes_base64"], str):
                raise IntakeRefusal("hyde_custody_metadata_capture_invalid", name)
            content = base64.b64decode(row["bytes_base64"], validate=True)
            if (
                len(content) != size
                or sha256(content) != row["sha256"]
                or row["capture_status"] != "exact_bytes_retained"
                or base64.b64encode(content).decode("ascii") != row["bytes_base64"]
            ):
                raise IntakeRefusal("hyde_custody_metadata_capture_invalid", name)
            captured += size
        elif (
            row["capture_status"] != "hash_reference_size_limit"
            or row["bytes_base64"] is not None
        ):
            raise IntakeRefusal("hyde_custody_metadata_capture_invalid", name)
        names.append(name)
    if names != [name for name in files if metadata_candidate(name)]:
        raise IntakeRefusal(
            "hyde_custody_metadata_inventory_invalid",
            "All native metadata candidates required",
        )


def _admit(
    root: Path, expected: str
) -> tuple[LocalHydeInventory, dict[str, object], LocalInventoryLimits, dict[str, str]]:
    root = checked_path(root)
    manifest_path = root / "manifest.json"
    if root.is_symlink() or manifest_path.is_symlink():
        raise IntakeRefusal("hyde_custody_inventory_invalid", str(root))
    with manifest_path.open("rb") as stream:
        initial_manifest = stream.read(65_537)
    if len(initial_manifest) > 65_536 or sha256(initial_manifest) != digest(expected):
        raise IntakeRefusal("hyde_custody_manifest_digest_mismatch", str(root))
    raw = _owned_bytes(root)
    if raw["manifest.json"] != initial_manifest:
        raise IntakeRefusal("hyde_custody_changed", str(root))
    if sha256(raw["manifest.json"]) != digest(expected):
        raise IntakeRefusal("hyde_custody_manifest_digest_mismatch", str(root))
    manifest = object_fields(
        decode(raw["manifest.json"]),
        {
            "schema_version",
            "producer",
            *POSTURE,
            "review_required",
            "files",
            "counts",
            "limits",
            "dataset_inventory_sha256",
        },
        "manifest",
    )
    if (
        manifest["schema_version"] != SCHEMA
        or any(
            manifest[key] != value or type(manifest[key]) is not type(value)
            for key, value in POSTURE.items()
        )
        or manifest["review_required"] != list(REVIEW_REQUIRED)
    ):
        raise IntakeRefusal("hyde_custody_posture_invalid", str(root))
    producer = object_fields(
        manifest["producer"],
        {"profile", "files", "files_sha256", "attestation"},
        "producer",
    )
    if (
        producer["profile"] != "hyde-custody-python-source-v1"
        or producer["attestation"] != "source_bytes_not_loaded_runtime"
        or not isinstance(producer["files"], dict)
        or not producer["files"]
    ):
        raise IntakeRefusal("hyde_custody_producer_invalid", str(root))
    producer_files = {
        relative_path(name): digest(value) for name, value in producer["files"].items()
    }
    required = {
        "collection/sources/hyde/local/" + name + ".py"
        for name in (
            "__init__",
            "contracts",
            "inventory",
            "archives",
            "preparation",
            "reading",
        )
    } | {"core/owned_tree.py"}
    if not required <= set(producer_files) or digest(
        producer["files_sha256"]
    ) != sha256(encode(producer_files)):
        raise IntakeRefusal("hyde_custody_producer_invalid", str(root))
    policy = object_fields(
        manifest["limits"], set(asdict(LocalInventoryLimits())), "limits"
    )
    limits = LocalInventoryLimits(
        **{key: integer(value, key) for key, value in policy.items()}
    )
    inventory = object_fields(manifest["files"], _MEMBERS, "members")
    for name in sorted(_MEMBERS):
        row = object_fields(inventory[name], {"sha256", "bytes"}, "member identity")
        if digest(row["sha256"]) != sha256(raw[name]) or integer(
            row["bytes"], "member bytes"
        ) != len(raw[name]):
            raise IntakeRefusal("hyde_custody_member_digest_mismatch", name)
    if sum(len(raw[name]) for name in _MEMBERS) > limits.maximum_retained_bytes:
        raise IntakeRefusal("hyde_custody_output_limit", str(root))
    values = {name: decode(raw[name]) for name in _MEMBERS}
    files = _file_rows(values["files.json"], limits)
    lookup = {str(row["path"]): row for row in files}
    dataset_digest = sha256(
        encode([row for row in files if row["classification"] == "dataset"])
    )
    if digest(manifest["dataset_inventory_sha256"]) != dataset_digest:
        raise IntakeRefusal("hyde_custody_dataset_identity_mismatch", str(root))
    archives = _archive_rows(values["archives.json"], lookup, limits)
    _metadata(values["metadata.json"], lookup, limits)
    counts = summary(files, archives)
    declared = object_fields(manifest["counts"], set(counts), "counts")
    if any(integer(declared[key], key) != value for key, value in counts.items()):
        raise IntakeRefusal("hyde_custody_counts_mismatch", str(root))
    if _owned_bytes(root) != raw:
        raise IntakeRefusal("hyde_custody_changed", str(root))
    result = LocalHydeInventory(
        root,
        expected,
        integer(counts["file_count"], "files"),
        integer(counts["byte_count"], "bytes"),
        integer(counts["dataset_file_count"], "dataset files"),
        integer(counts["dataset_byte_count"], "dataset bytes"),
        len(archives),
        dataset_digest,
    )
    return result, values, limits, producer_files


def read_local_hyde_inventory(
    destination: Path, *, expected_manifest_sha256: str
) -> LocalHydeInventory:
    """Authenticate retained custody only, with no external/native/scientific admission."""
    try:
        return _admit(destination.absolute(), expected_manifest_sha256)[0]
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        OverflowError,
        RecursionError,
        zipfile.BadZipFile,
    ) as exc:
        if isinstance(exc, IntakeRefusal):
            raise
        raise IntakeRefusal("hyde_custody_read_failed", str(exc)) from exc


def replay_local_hyde_inventory(product: LocalHydeInventory, source_root: Path) -> None:
    """Rehash the complete external tree and compare exact portable custody metadata."""
    try:
        current, values, limits, producer = _admit(
            product.directory, product.manifest_sha256
        )
        if current != product:
            raise IntakeRefusal(
                "hyde_custody_product_identity_mismatch", str(product.directory)
            )
        if implementation_identity() != producer:
            raise IntakeRefusal(
                "hyde_custody_producer_mismatch",
                "Full replay requires the exact recorded producer",
            )
        source_root = checked_path(source_root)
        snapshot = source_snapshot(source_root, limits)
        if collect_sources(source_root, snapshot, limits) != values:
            raise IntakeRefusal("hyde_source_replay_mismatch", str(source_root))
        unchanged(source_root, snapshot, limits)
        if implementation_identity() != producer:
            raise IntakeRefusal(
                "hyde_custody_producer_changed", "Producer changed during replay"
            )
        _admit(product.directory, product.manifest_sha256)
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        OverflowError,
        RecursionError,
        zipfile.BadZipFile,
    ) as exc:
        if isinstance(exc, IntakeRefusal):
            raise
        raise IntakeRefusal("hyde_source_replay_failed", str(exc)) from exc
