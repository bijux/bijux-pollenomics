"""Strict standalone reading of preserved native-index windows and their identities."""

from __future__ import annotations

import base64
from dataclasses import asdict, fields
import io
from pathlib import Path

from ...quarantine import IntakeRefusal
from ..local import BoundArchiveMember
from ..local.contracts import (
    array,
    checked_path,
    decode,
    digest,
    encode,
    integer,
    object_fields,
    relative_path,
    sha256,
    text,
)
from .contracts import (
    FORMAT,
    POSTURE,
    SCHEMA,
    AsciiWindowLimits,
    AsciiWindowSelection,
    NativeAsciiWindow,
)
from .parsing import number, parse_header


def selection_from_payload(value: object) -> AsciiWindowSelection:
    row = object_fields(
        value, {field.name for field in fields(AsciiWindowSelection)}, "selection"
    )
    labels = []
    for pair in array(row["native_labels"], "native labels"):
        items = array(pair, "label")
        if len(items) != 2:
            raise IntakeRefusal("hyde_ascii_labels_invalid", repr(pair))
        labels.append((text(items[0], "role"), text(items[1], "label")))
    return AsciiWindowSelection(
        relative_path(row["archive_path"]),
        integer(row["member_index"], "member index"),
        text(row["expected_member_name"], "member name"),
        integer(row["row_start"], "row start"),
        integer(row["row_stop"], "row stop"),
        integer(row["column_start"], "column start"),
        integer(row["column_stop"], "column stop"),
        tuple(labels),
    )


def bound_from_payload(value: object) -> BoundArchiveMember:
    row = object_fields(
        value, {field.name for field in fields(BoundArchiveMember)}, "bound member"
    )
    return BoundArchiveMember(
        digest(row["custody_manifest_sha256"]),
        digest(row["dataset_inventory_sha256"]),
        relative_path(row["archive_path"]),
        digest(row["archive_sha256"]),
        integer(row["archive_bytes"], "archive bytes"),
        integer(row["member_index"], "member index"),
        text(row["name"], "native name"),
        text(row["occurrence_json"], "occurrence"),
        text(row["archive_directory_json"], "directory"),
    )


def _raw(root: Path, expected: str) -> dict[str, bytes]:
    root = checked_path(root)
    if not root.is_dir() or {p.name for p in root.iterdir()} != {
        "manifest.json",
        "window.json",
    }:
        raise IntakeRefusal("hyde_ascii_product_inventory_invalid", str(root))
    result = {}
    for name, limit in (
        ("manifest.json", 65_536),
        ("window.json", AsciiWindowLimits().maximum_retained_bytes),
    ):
        path = checked_path(root / name)
        if not path.is_file():
            raise IntakeRefusal("hyde_ascii_product_inventory_invalid", name)
        with path.open("rb") as stream:
            content = stream.read(limit + 1)
        if len(content) > limit:
            raise IntakeRefusal("hyde_ascii_output_limit", name)
        if name == "manifest.json" and sha256(content) != digest(expected):
            raise IntakeRefusal("hyde_ascii_manifest_digest_mismatch", str(root))
        result[name] = content
    return result


def _read(root: Path, expected: str) -> NativeAsciiWindow:
    raw = _raw(root, expected)
    manifest = object_fields(
        decode(raw["manifest.json"]),
        {
            "schema_version",
            "format_profile",
            *POSTURE,
            "producer",
            "custody_manifest_sha256",
            "dataset_inventory_sha256",
            "archive_member",
            "selection",
            "limits",
            "files",
            "member_payload",
            "counts",
        },
        "manifest",
    )
    if (
        manifest["schema_version"] != SCHEMA
        or manifest["format_profile"] != FORMAT
        or any(
            type(manifest[key]) is not type(value) or manifest[key] != value
            for key, value in POSTURE.items()
        )
    ):
        raise IntakeRefusal("hyde_ascii_product_posture_invalid", str(root))
    producer = object_fields(
        manifest["producer"], {"files", "files_sha256", "attestation"}, "producer"
    )
    if (
        not isinstance(producer["files"], dict)
        or not producer["files"]
        or producer["attestation"] != "source_bytes_not_loaded_runtime"
    ):
        raise IntakeRefusal("hyde_ascii_producer_invalid", str(root))
    identities = {
        relative_path(key): digest(value) for key, value in producer["files"].items()
    }
    required = {
        "collection/sources/hyde/ascii/" + name + ".py"
        for name in (
            "__init__",
            "contracts",
            "parsing",
            "streaming",
            "preparation",
            "reading",
        )
    } | {"core/owned_tree.py", "collection/sources/hyde/local/reading.py"}
    if not required <= set(identities) or digest(producer["files_sha256"]) != sha256(
        encode(identities)
    ):
        raise IntakeRefusal("hyde_ascii_producer_invalid", str(root))
    limits_payload = object_fields(
        manifest["limits"],
        {field.name for field in fields(AsciiWindowLimits)},
        "limits",
    )
    limits = AsciiWindowLimits(
        **{key: integer(value, key) for key, value in limits_payload.items()}
    )
    selection = selection_from_payload(manifest["selection"])
    selected = bound_from_payload(manifest["archive_member"])
    occurrence = selected.occurrence()
    if (
        selected.custody_manifest_sha256 != digest(manifest["custody_manifest_sha256"])
        or selected.dataset_inventory_sha256
        != digest(manifest["dataset_inventory_sha256"])
        or selection.archive_path != selected.archive_path
        or selection.member_index != selected.member_index
        or selection.expected_member_name != selected.name
        or occurrence["directory"]
        or occurrence["symlink"]
        or not occurrence["safe_relative_name"]
        or integer(occurrence["flags"], "flags") & 1
        or Path(selected.name).suffix.casefold() != ".asc"
    ):
        raise IntakeRefusal("hyde_ascii_retained_selection_mismatch", selected.name)
    inventory = object_fields(manifest["files"], {"window.json"}, "files")
    identity = object_fields(
        inventory["window.json"], {"bytes", "sha256"}, "window identity"
    )
    if (
        integer(identity["bytes"], "bytes") != len(raw["window.json"])
        or digest(identity["sha256"]) != sha256(raw["window.json"])
        or len(raw["window.json"]) > limits.maximum_retained_bytes
    ):
        raise IntakeRefusal("hyde_ascii_window_digest_mismatch", str(root))
    window = object_fields(
        decode(raw["window.json"]),
        {"header", "source_tokens", "missing_mask"},
        "window",
    )
    header_payload = object_fields(
        window["header"], {"bytes_base64", "tokens", "rows", "columns"}, "header"
    )
    header_bytes = base64.b64decode(
        text(header_payload["bytes_base64"], "header bytes"), validate=True
    )
    header = parse_header(io.BytesIO(header_bytes), limits)
    if encode(asdict(header)) != encode(header_payload):
        raise IntakeRefusal("hyde_ascii_retained_header_mismatch", str(root))
    if selection.row_stop > header.rows or selection.column_stop > header.columns:
        raise IntakeRefusal("hyde_ascii_window_outside_source", str(root))
    tokens = tuple(
        text(value, "source token")
        for value in array(window["source_tokens"], "tokens")
    )
    raw_mask = array(window["missing_mask"], "missingness")
    if any(type(value) is not bool for value in raw_mask):
        raise IntakeRefusal("hyde_ascii_missingness_invalid", str(root))
    mask = tuple(value is True for value in raw_mask)
    cell_count = (selection.row_stop - selection.row_start) * (
        selection.column_stop - selection.column_start
    )
    if (
        cell_count > limits.maximum_selected_cells
        or len(tokens) != cell_count
        or len(mask) != cell_count
    ):
        raise IntakeRefusal("hyde_ascii_retained_cell_count_mismatch", str(root))
    nodata = number(header.value("nodata_value"), limits)
    values = tuple(number(token, limits) for token in tokens)
    if mask != tuple(value == nodata for value in values):
        raise IntakeRefusal("hyde_ascii_missingness_invalid", str(root))
    expected_counts = {
        "source_cells": header.rows * header.columns,
        "selected_cells": cell_count,
        "selected_missing": sum(mask),
        "selected_nonmissing": cell_count - sum(mask),
        "selected_zero": sum(
            not missing and value == 0
            for value, missing in zip(values, mask, strict=True)
        ),
    }
    counts = object_fields(manifest["counts"], set(expected_counts), "counts")
    if any(
        integer(counts[key], key) != value for key, value in expected_counts.items()
    ):
        raise IntakeRefusal("hyde_ascii_retained_counts_mismatch", str(root))
    payload = object_fields(
        manifest["member_payload"],
        {"sha256", "bytes", "crc32", "complete_eof_verified"},
        "member payload",
    )
    member_sha = digest(payload["sha256"])
    if (
        payload["complete_eof_verified"] is not True
        or integer(payload["bytes"], "expanded bytes") != occurrence["bytes"]
        or integer(payload["crc32"], "crc32") != occurrence["crc32"]
        or integer(payload["bytes"], "expanded bytes") > limits.maximum_member_bytes
        or integer(payload["bytes"], "bytes")
        > integer(occurrence["compressed_bytes"], "compressed bytes")
        * limits.maximum_expansion_ratio
    ):
        raise IntakeRefusal("hyde_ascii_member_integrity_mismatch", selected.name)
    if _raw(root, expected) != raw:
        raise IntakeRefusal("hyde_ascii_product_changed", str(root))
    return NativeAsciiWindow(
        root,
        expected,
        selected.custody_manifest_sha256,
        member_sha,
        selection,
        header,
        tokens,
        mask,
    )


def read_hyde_ascii_window(
    destination: Path, *, expected_manifest_sha256: str
) -> NativeAsciiWindow:
    """Authenticate a retained native preview; historical producer identity is preserved."""
    try:
        return _read(checked_path(destination), expected_manifest_sha256)
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        OverflowError,
        RecursionError,
    ) as exc:
        if isinstance(exc, IntakeRefusal):
            raise
        raise IntakeRefusal("hyde_ascii_read_failed", str(exc)) from exc
