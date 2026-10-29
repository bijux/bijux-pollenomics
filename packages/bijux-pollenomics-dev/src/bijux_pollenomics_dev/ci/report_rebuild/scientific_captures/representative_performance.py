"""Admit exact retained performance observations without measuring them again."""

from __future__ import annotations

import hashlib
from pathlib import Path

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.native_backend.retained_performance import (
    CAPTURE as CAPTURE,
)
from bijux_pollenomics_dev.native_backend.retained_performance import (
    COMMON_SHA256,
    EXECUTION_CANDIDATE,
    OUTER_SHA256,
    REPORT_ROOT,
    sha,
    validated_capture,
)

from ..contracts import JsonObject, ReportRebuildError
from ..ownership import ReportOwnershipError, _regular_confined_file

CAPTURE_SHA256 = "4dba752c15d06a4d41b12ca3f4505adec102dd7da0a62d865ee4a8a09526e075"
OWNER = "numerical-performance/representative-public-calls/report-products"
REPORT = REPORT_ROOT + "/report.json"


def validated_representative_performance_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Keep the original execution epoch and published scientific/timing bytes exact."""
    selected = [row for row in owners if row.get("owner_id") == OWNER]
    if not selected and not (repository / CAPTURE).exists():
        return (), {}
    if (
        len(selected) != 1
        or selected[0].get("role") != "retained_source"
        or selected[0].get("producer_paths") != []
        or selected[0].get("producer_inputs") != []
        or selected[0].get("paths") != [REPORT]
        or any(
            row not in selected and REPORT in paths
            for row in owners
            if isinstance(paths := row.get("paths"), list)
        )
    ):
        raise ReportRebuildError("Retained performance exact owner declaration differs")
    try:
        report = validated_capture(repository, capture_sha256=CAPTURE_SHA256)
        current = _regular_confined_file(repository, REPORT, "retained performance")
        retained = _regular_confined_file(
            repository,
            str(Path(CAPTURE).parent / "publication/report.json"),
            "retained performance source",
        )
    except (OSError, ValueError, ReportOwnershipError) as error:
        raise ReportRebuildError("Retained performance custody refused") from error
    entry = tracked_by_path.get(REPORT)
    raw = current.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if (
        entry is None
        or entry.kind != "file"
        or entry.sha256 != digest
        or entry.size != len(raw)
        or raw != retained.read_bytes()
        or report["qualified_all_three_worker_hotspots"] != []
        or report["new_cpp_allowed"] is not False
        or report["source_R_same_input_comparison_executed"] is not False
        or sha(repository / CAPTURE) != CAPTURE_SHA256
    ):
        raise ReportRebuildError("Retained performance published output differs")
    return (entry,), {
        "owner_ids": [OWNER],
        "capture_sha256": CAPTURE_SHA256,
        "execution_candidate": EXECUTION_CANDIDATE,
        "original_common_terminal_sha256": COMMON_SHA256,
        "original_resource_terminal_sha256": OUTER_SHA256,
        "report_outputs": 1,
        "primary_measurements": 6,
        "all_worker_measurements": 14,
        "new_timing_profile_model_compiler_R_calls": 0,
        "scope": "Completed116 timing and scientific output transport only; original source/runtime/private authority and failed native adoption remain separate from current maintained metadata. No new performance, scientific, rights, human or release acceptance.",
    }
