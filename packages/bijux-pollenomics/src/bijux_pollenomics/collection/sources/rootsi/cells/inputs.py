"""Admit exact retained workbook inventory and local byte bindings."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import os
from pathlib import Path, PurePosixPath

from ..authority import ARCHIVE_SHA256
from .models import (
    Capture,
    WorkbookInput,
    decoded,
    digest,
    integer,
    object_value,
    refuse,
    sequence,
    text,
)

# Existing retained capture identity; this is not a new accepted-source registry.
RETAINED_INVENTORY_SHA256 = (
    "3353156471c2d04f2dce4138d29ad1a4891896d223c2c37dd5c531ba51c17b5a"
)


def local_path(path: Path) -> Path:
    """Reject symlink components before normalizing lexical dot segments."""
    path = path.absolute()
    if any(part.is_symlink() for part in (path, *path.parents)):
        refuse("symlink_path", str(path))
    return Path(os.path.abspath(path))


def read_bytes(
    path: Path, expected_sha256: str, expected_bytes: int | None = None
) -> bytes:
    """Read a regular nonsymlink input under an explicit digest pin."""
    path = local_path(path)
    if not path.is_file():
        refuse("missing_input", str(path))
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        refuse("input_digest_mismatch", str(path))
    if expected_bytes is not None and len(payload) != expected_bytes:
        refuse("input_size_mismatch", str(path))
    return payload


def member_name(value: object) -> str:
    """Preserve exact safe original member names; never reduce to basename."""
    name = text(value, "archive_member")
    parts = name.split("/")
    if (
        "\x00" in name
        or "\\" in name
        or PurePosixPath(name).is_absolute()
        or any(part in {"", ".", ".."} for part in parts)
        or not name.endswith(".xls")
    ):
        refuse("invalid_member", name)
    return name


def inventory_workbooks(payload: bytes) -> dict[str, tuple[str, int]]:
    """Parse the one source-owned roster contract after its bytes are pinned."""
    inventory = object_value(decoded(payload), "inventory")
    if (
        inventory.get("archive_sha256") != ARCHIVE_SHA256
        or inventory.get("source_unchanged") is not True
    ):
        refuse("inventory_posture", "archive identity or historical unchanged claim")
    rows = sequence(inventory.get("workbooks"), "workbooks")
    if (
        integer(inventory.get("workbook_count"), "workbook_count", minimum=1)
        != len(rows)
        or len(rows) != 79
    ):
        refuse("inventory_count", "workbook_count")
    available: dict[str, tuple[str, int]] = {}
    for raw in rows:
        row = object_value(raw, "workbook")
        name = member_name(row.get("archive_member"))
        if name in available:
            refuse("duplicate_member", name)
        available[name] = (
            digest(row.get("sha256"), name),
            integer(row.get("byte_count"), name, minimum=1),
        )
    return available


def bind_capture(
    *,
    inventory_path: Path,
    expected_inventory_sha256: str,
    workbook_files: Mapping[str, Path],
    scope: str,
) -> Capture:
    """Bind selected files to the recognized retained capture, not a new registry."""
    pin = digest(expected_inventory_sha256, "inventory_sha256")
    if pin != RETAINED_INVENTORY_SHA256:
        refuse("unrecognized_capture", pin)
    payload = read_bytes(inventory_path, pin)
    available = inventory_workbooks(payload)
    if not isinstance(scope, str) or scope not in {
        "selected_workbooks",
        "complete_retained_capture",
    }:
        refuse("invalid_scope", repr(scope))
    selected = set(workbook_files)
    if (
        not selected
        or any(not isinstance(key, str) for key in selected)
        or not selected <= available.keys()
    ):
        refuse("unknown_selection", repr(selected))
    if scope == "complete_retained_capture" and (
        len(available) != 79 or selected != available.keys()
    ):
        refuse("incomplete_capture", "all 79 retained XLS members required")
    workbooks = tuple(
        WorkbookInput(name, local_path(workbook_files[name]), *available[name])
        for name in sorted(selected)
    )
    for workbook in workbooks:
        read_bytes(workbook.path, workbook.sha256, workbook.byte_count)
    return Capture(
        local_path(inventory_path),
        pin,
        len(payload),
        ARCHIVE_SHA256,
        scope,
        len(available),
        workbooks,
    )


def verify_capture(capture: Capture) -> None:
    """Recheck every source byte binding after preparation/replay."""
    read_bytes(
        capture.inventory_path, capture.inventory_sha256, capture.inventory_bytes
    )
    for workbook in capture.workbooks:
        read_bytes(workbook.path, workbook.sha256, workbook.byte_count)


def output_path(path: Path, capture: Capture) -> Path:
    """Refuse source/output overlap and existing outputs before staging."""
    result = local_path(path)
    for source in (capture.inventory_path, *(item.path for item in capture.workbooks)):
        if (
            result == source
            or result.is_relative_to(source.parent)
            or source.is_relative_to(result)
        ):
            refuse("unsafe_output", str(result))
    if result.exists():
        refuse("output_exists", str(result))
    return result
