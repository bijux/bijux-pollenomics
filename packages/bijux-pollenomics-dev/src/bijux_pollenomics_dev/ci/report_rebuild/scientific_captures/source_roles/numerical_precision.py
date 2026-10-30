"""Bind reviewed numerical precision changes to their dated source evidence."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import _regular_confined_file
from ...retained_source import SourceCapsule

METRICS_SOURCE = "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/lra_validation/metrics.py"
_HISTORICAL_SHA256 = "8c90297434e12dc5d5c14a2bed1857c9f19fbdbbdccd54d1454f3bb112ea5219"
_HISTORICAL_BYTES = 9355
_QUALIFIED_CAPTURES = {
    "data/method-certification/author-optimizer-diagnostic-source-capture": (
        "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93",
        "executions/optimizer-diagnostics/first-party-inputs/",
    ),
    "data/surface-reference/swedish-direct-pollen-source-capture": (
        "fed646a3620b7266f8ab87dd44cdbfac72461179d74df29410460deb81672449",
        "original-source/source/",
    ),
}

_OLD_RETURN = b"""    return sqrt(
        0.5
        * sum(
            (sqrt(prediction[taxon]) - sqrt(observation[taxon])) ** 2
            for taxon in prediction
        )
    )"""
_NEW_RETURN = b"""    # Rationalize the root difference before taking its scaled Euclidean norm.
    # Separate square roots can coincide for distinct adjacent fractions, and
    # squaring a representable root difference can underflow before the norm.
    return hypot(
        *(
            (prediction[taxon] - observation[taxon])
            / (sqrt(prediction[taxon]) + sqrt(observation[taxon]))
            if prediction[taxon] or observation[taxon]
            else 0.0
            for taxon in prediction
        )
    ) / sqrt(2.0)"""


def hellinger_precision_extension_matches(historical: bytes, current: bytes) -> bool:
    """Reconstruct every old byte by reversing only the reviewed Hellinger span."""
    return (
        len(historical) == _HISTORICAL_BYTES
        and hashlib.sha256(historical).hexdigest() == _HISTORICAL_SHA256
        and len(current) <= 16 * 1024
        and historical.count(_OLD_RETURN) == 1
        and current.count(_NEW_RETURN) == 1
        and current.replace(_NEW_RETURN, _OLD_RETURN, 1) == historical
    )


def validated_hellinger_precision_source(
    repository: Path,
    historical: JsonObject,
    logical: str,
    source_buffer: SourceCapsule,
) -> JsonObject:
    """Preserve dated outputs while admitting one explicitly bound precision change."""
    binding = _QUALIFIED_CAPTURES.get(source_buffer.prefix)
    expected = {"sha256": _HISTORICAL_SHA256, "bytes": _HISTORICAL_BYTES}
    if (
        binding is None
        or repository != repository.resolve()
        or source_buffer.repository != repository
        or source_buffer.descriptor.capture.get("sha256") != binding[0]
        or set(historical) != {"path", "sha256", "bytes"}
        or type(historical.get("bytes")) is not int
        or historical != {"path": METRICS_SOURCE, **expected}
        or logical != binding[1] + METRICS_SOURCE
        or logical not in source_buffer.detached
        or source_buffer.descriptor.members.get(logical) != expected
        or [
            path
            for group in source_buffer.descriptor.groups
            for member, path in group["resolved_paths"]
            if member == logical
        ]
        != [METRICS_SOURCE]
    ):
        raise ReportRebuildError("Hellinger precision source binding differs")
    source_buffer.fresh()
    captured = source_buffer.read_source(logical)
    current_file = _regular_confined_file(repository, METRICS_SOURCE, "current metrics")
    before = current_file.stat()
    if before.st_nlink != 1 or not 0 < before.st_size <= 16 * 1024:
        raise ReportRebuildError("Current metrics must be bounded and single-link")
    current = current_file.read_bytes()
    if not hellinger_precision_extension_matches(captured, current):
        raise ReportRebuildError("Metrics differ beyond the finite Hellinger law")
    source_buffer.fresh()
    again = _regular_confined_file(repository, METRICS_SOURCE, "current metrics")
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
        raise ReportRebuildError("Current metrics changed during correspondence")
    return {
        "path": METRICS_SOURCE,
        "classification": "finite_hellinger_precision_extension",
        "original_member": logical,
        "original_sha256": _HISTORICAL_SHA256,
        "original_bytes": _HISTORICAL_BYTES,
        "whole_old_module_reconstructed": True,
        "current_regular_single_link_and_stable": True,
        "historical_numeric_outputs_regenerated": False,
        "historical_native_software_equal_current_claimed": False,
        "saved_output_equality_from_source_law_claimed": False,
        "scope": "Only the rationalized Hellinger root difference and scaled hypot norm change. All other module bytes reconstruct the authenticated old source. Historical outputs and native epochs remain literal; current analytical and retained-pair metric checks are separate software qualification, not a new model execution.",
    }
