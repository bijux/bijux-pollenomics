"""Admit only the 129 raw report members of one reviewed native macOS R capture."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import cast

from bijux_pollenomics_dev.ci.rebuild_reports import (
    InventoryEntry,
    ReproducibleReportError,
    inventory_reports,
)
from bijux_pollenomics_dev.lra_validation.native_reference.capture import (
    REPORT_PREFIX,
    validated_native_capture,
)

from ..contracts import JsonObject, ReportRebuildError
from ..ownership import _regular_confined_file

_MAINTAINED_SOURCE_MEMBERS = frozenset(
    {
        "source-domains/r_support.R",
        "source-domains/run_source_domains.py",
        "source-domains/source_domains.R",
    }
)


def _native_r_reference(
    repository: Path, policy: JsonObject
) -> tuple[InventoryEntry, ...]:
    """Check source identity; retained native bytes are never claimed regenerated."""
    report_root = cast(str, policy["tracked_report_root"])
    if report_root != "docs/report":
        raise ReportRebuildError("native R source requires the governed report root")
    before = validated_native_capture(repository)
    prefix = REPORT_PREFIX.removeprefix("docs/report/")
    by_name: dict[str, InventoryEntry] = {}
    for folder in ("oracle", "source-domains"):
        for entry in inventory_reports(repository / REPORT_PREFIX / folder, policy):
            by_name[f"{folder}/{entry.path}"] = entry
    if set(by_name) != set(before.report_source_members) | _MAINTAINED_SOURCE_MEMBERS:
        raise ReportRebuildError("native R report source has missing or extra members")
    for name in _MAINTAINED_SOURCE_MEMBERS:
        _regular_confined_file(
            repository, f"{REPORT_PREFIX}/{name}", "maintained native R source code"
        )
    selected: list[InventoryEntry] = []
    for name in before.report_source_members:
        path = _regular_confined_file(
            repository, f"{REPORT_PREFIX}/{name}", "native R report source"
        )
        if path.stat().st_nlink != 1:
            raise ReportRebuildError("native R report source cannot share an inode")
        if hashlib.sha256(path.read_bytes()).hexdigest() != before.raw_sha256[name]:
            raise ReportRebuildError(
                "native R report source differs from qualified capture"
            )
        selected_entry = by_name.get(name)
        if (
            selected_entry is None
            or selected_entry.kind != "file"
            or selected_entry.sha256 != before.raw_sha256[name]
        ):
            raise ReportRebuildError("native R report source inventory changed")
        selected.append(
            InventoryEntry(
                f"{prefix}/{name}",
                selected_entry.kind,
                selected_entry.size,
                selected_entry.sha256,
                selected_entry.canonical_sha256,
            )
        )
    final = {
        f"{folder}/{entry.path}": entry
        for folder in ("oracle", "source-domains")
        for entry in inventory_reports(repository / REPORT_PREFIX / folder, policy)
    }
    if final != by_name:
        raise ReportRebuildError(
            "native R report source changed during retained admission"
        )
    if validated_native_capture(repository) != before or len(selected) != 129:
        raise ReportRebuildError("native R source changed during retained admission")
    return tuple(selected)


def validated_native_r_reference(
    repository: Path, policy: JsonObject
) -> tuple[InventoryEntry, ...]:
    """Require the fixed native capture, preserving report-boundary refusal types."""
    try:
        return _native_r_reference(repository, policy)
    except (OSError, ValueError, ReproducibleReportError) as error:
        raise ReportRebuildError(
            "native R retained source validation failed"
        ) from error
