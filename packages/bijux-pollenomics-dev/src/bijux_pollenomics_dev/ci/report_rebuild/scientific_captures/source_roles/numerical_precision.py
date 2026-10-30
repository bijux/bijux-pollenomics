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


_HISTORICAL_PROFILE_SPANS: tuple[tuple[bytes, bytes], ...] = (
    (b"from typing import Literal\n", b""),
    (
        b'HellingerArithmeticProfile = Literal["stable", "source-compatible-22c6e480"]\n\n\n',
        b"",
    ),
    (
        b'def hellinger_distance(\n    predicted: Mapping[str, float],\n    observed: Mapping[str, float],\n    *,\n    arithmetic_profile: HellingerArithmeticProfile = "stable",\n) -> float:\n    """Distance on a shared taxon axis with explicit arithmetic provenance.\n\n    The stable default preserves small representable distances. The source-compatible\n    profile retains the arithmetic order of the named historical source, including\n    its cancellation and underflow limitations; it supplies no tolerance allowance.\n    """\n    if arithmetic_profile not in ("stable", "source-compatible-22c6e480"):\n        raise ValueError("Unknown Hellinger arithmetic profile")\n',
        b'def hellinger_distance(\n    predicted: Mapping[str, float], observed: Mapping[str, float]\n) -> float:\n    """Distance between two closed compositions on the same named taxon axis."""\n',
    ),
    (
        b'    if arithmetic_profile == "source-compatible-22c6e480":\n        # The source used Python 3.11\'s left-to-right float sum. Accumulate\n        # explicitly because newer Python versions compensate builtin sum.\n        total = 0.0\n        for taxon in prediction:\n            total += (sqrt(prediction[taxon]) - sqrt(observation[taxon])) ** 2\n        return sqrt(0.5 * total)\n',
        b"",
    ),
)


def stable_hellinger_profile_basis(current: bytes) -> bytes | None:
    """Remove only the declared opt-in profile while retaining every stable byte."""
    if not current or len(current) > 16 * 1024:
        return None
    if b"HellingerArithmeticProfile = Literal[" not in current:
        return current
    basis = current
    for inserted, original in _HISTORICAL_PROFILE_SPANS:
        if basis.count(inserted) != 1:
            return None
        basis = basis.replace(inserted, original, 1)
    return basis


def hellinger_precision_extension_matches(historical: bytes, current: bytes) -> bool:
    """Reconstruct every old byte by reversing only the reviewed Hellinger span."""
    basis = stable_hellinger_profile_basis(current)
    return (
        basis is not None
        and len(historical) == _HISTORICAL_BYTES
        and hashlib.sha256(historical).hexdigest() == _HISTORICAL_SHA256
        and len(current) <= 16 * 1024
        and historical.count(_OLD_RETURN) == 1
        and basis.count(_NEW_RETURN) == 1
        and basis.replace(_NEW_RETURN, _OLD_RETURN, 1) == historical
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
        "default_arithmetic_profile": "stable",
        "explicit_historical_profile_available": b"HellingerArithmeticProfile = Literal["
        in current,
        "historical_profile_requires_explicit_selection": True,
        "historical_native_software_equal_current_claimed": False,
        "saved_output_equality_from_source_law_claimed": False,
        "scope": "The default uses the reviewed rationalized Hellinger root difference and scaled hypot norm. A separately named opt-in historical arithmetic branch, exact profile declaration and stable default header can be removed only by the finite complete-source inverse. Reversing that addition and the existing precision span reconstructs every authenticated old source byte. The explicit historical profile is not silently selected or equated with stable-default results. Historical outputs and native epochs remain literal; current analytical and retained-pair metric checks are separate software qualification, not a new model execution.",
    }
