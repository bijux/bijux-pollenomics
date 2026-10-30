"""Bind stricter whole-pollen contract refusals to two original source contexts."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import _regular_confined_file
from ...retained_source import SourceCapsule

PROPAGATION_QUALIFICATION_SOURCE = (
    "packages/bijux-pollenomics/src/bijux_pollenomics/"
    "analysis/propagation/outputs/contracts.py"
)
_SOURCE_BYTES = 10067
_SOURCE_SHA256 = "bf955aa90b22269d8c8b6d662b715e2c0ad17b76b61dfc5f11470d0d3843ab5f"
_CAPTURE_CONTEXTS = {
    "data/method-certification/author-optimizer-diagnostic-source-capture": (
        "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93",
        "executions/optimizer-diagnostics/first-party-inputs/",
    ),
    "data/atlas/sample-chronology-source-view-capture": (
        "2491a59a0d5cde5dffd05397c4a7dcc95ab98ba922019863e5ea2662681dba62",
        "source/",
    ),
}
_QUALIFICATION_SPANS = (
    (
        (
            b"    denominators = _required_contract_section(denominators)\n"
            b'    spatial = default.get("spatial")\n'
        ),
        (
            b"    denominators = _required_contract_section(denominators)\n"
            b'    pair_compatibility = _required_contract_section(contract.get("pair_compatibility"))\n'
            b"    whole_pollen = _required_contract_section(\n"
            b'        pair_compatibility.get("whole_pollen_resolution")\n'
            b"    )\n"
            b'    spatial = default.get("spatial")\n'
        ),
    ),
    (
        (
            b'        or output_edge_contract.get("route_interpretation_allowed") is not False\n'
            b'        or output_edge_contract.get("map_geometry")\n'
        ),
        (
            b'        or output_edge_contract.get("route_interpretation_allowed") is not False\n'
            b'        or whole_pollen.get("heterogeneous_taxa_warning_required") is not True\n'
            b'        or whole_pollen.get("interpretive_strength_cap") != "exploratory_aggregate"\n'
            b'        or output_edge_contract.get("map_geometry")\n'
        ),
    ),
)


def propagation_qualification_extension_matches(
    captured: bytes, current: bytes
) -> bool:
    """Reverse only the two anchored normative whole-pollen qualification checks."""
    if (
        len(captured) != _SOURCE_BYTES
        or hashlib.sha256(captured).hexdigest() != _SOURCE_SHA256
    ):
        return False
    restored = current
    for original, refinement in _QUALIFICATION_SPANS:
        if captured.count(original) != 1 or restored.count(refinement) != 1:
            return False
        restored = restored.replace(refinement, original, 1)
    return restored == captured


def validated_propagation_qualification_source(
    repository: Path, historical: JsonObject, logical: str, source_buffer: SourceCapsule
) -> JsonObject:
    """Authenticate a refusal refinement without revalidating historical outputs."""
    context = _CAPTURE_CONTEXTS.get(source_buffer.prefix)
    expected = {"sha256": _SOURCE_SHA256, "bytes": _SOURCE_BYTES}
    if (
        context is None
        or repository != repository.resolve()
        or source_buffer.repository != repository
        or source_buffer.descriptor.capture.get("sha256") != context[0]
        or set(historical) != {"path", "sha256", "bytes"}
        or type(historical.get("bytes")) is not int
        or historical != {"path": PROPAGATION_QUALIFICATION_SOURCE, **expected}
        or logical != context[1] + PROPAGATION_QUALIFICATION_SOURCE
        or logical not in source_buffer.detached
        or source_buffer.descriptor.members.get(logical) != expected
        or [
            path
            for group in source_buffer.descriptor.groups
            for original, path in group["resolved_paths"]
            if original == logical
        ]
        != [PROPAGATION_QUALIFICATION_SOURCE]
    ):
        raise ReportRebuildError("Whole-pollen qualification source binding differs")
    source_buffer.fresh()
    captured = source_buffer.read_source(logical)
    current_path = _regular_confined_file(
        repository,
        PROPAGATION_QUALIFICATION_SOURCE,
        "current propagation qualification",
    )
    before = current_path.stat()
    if before.st_nlink != 1 or not 0 < before.st_size <= 64 * 1024:
        raise ReportRebuildError(
            "Propagation qualification source is linked or unbounded"
        )
    current = current_path.read_bytes()
    if not propagation_qualification_extension_matches(captured, current):
        raise ReportRebuildError(
            "Propagation qualification differs beyond its two refusal checks"
        )
    source_buffer.fresh()
    again = _regular_confined_file(
        repository,
        PROPAGATION_QUALIFICATION_SOURCE,
        "current propagation qualification",
    )
    after = again.stat()
    fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    if (
        any(getattr(before, field) != getattr(after, field) for field in fields)
        or again.read_bytes() != current
    ):
        raise ReportRebuildError(
            "Propagation qualification source changed during verification"
        )
    return {
        "path": PROPAGATION_QUALIFICATION_SOURCE,
        "classification": "whole_pollen_contract_refusal_refinement",
        "original_member": logical,
        "original_bytes": _SOURCE_BYTES,
        "original_sha256": _SOURCE_SHA256,
        "whole_old_module_reconstructed": True,
        "all_other_old_source_bytes_exact": True,
        "current_regular_single_link_and_stable": True,
        "missing_or_invalid_whole_pollen_qualification_newly_refused": True,
        "current_refusal_behavior_intentionally_stricter": True,
        "historical_outputs_revalidated_under_current_contract_claimed": False,
        "old_native_equal_current_admission_claimed": False,
        "new_native_or_scientific_execution_claimed": False,
    }
