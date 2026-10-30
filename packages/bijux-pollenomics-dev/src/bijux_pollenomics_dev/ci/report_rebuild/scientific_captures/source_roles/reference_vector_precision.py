"""Bind exact token-parser extensions without equating current and native values."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import _regular_confined_file
from ...retained_source import SourceCapsule
from .native_reference_transport import native_reference_transport_extension_matches

_REFERENCE_VECTOR_IDENTITIES = {
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/live_reference_comparison.py": (
        12289,
        "8e725129e23f92c594084116c0d2a5e282af9fb71048b28ea58adac3f2e460d2",
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/reference_replay.py": (
        12286,
        "09414776bf42a8ae475e55d84a8874ba8afdc83523b845fd11ec4944cbdaf1fa",
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/retained_reference/comparison.py": (
        12359,
        "3dce275e685e0b868bf54f3b3fece648fc0be28089fafe46739f8c0e9844c3f5",
    ),
}

_REFERENCE_VECTOR_SPANS = {
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/live_reference_comparison.py": (
        (b"", b"    numeric_vector_values,\n"),
        (
            b'    return pd.to_numeric(\n        data["value"].replace({"NaN": np.nan, "NA": np.nan}), errors="raise"\n    ).to_numpy(float)\n',
            b'    return numeric_vector_values(data["value"])\n',
        ),
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/reference_replay.py": (
        (
            b"",
            b'\n\ndef numeric_vector_values(values: pd.Series) -> np.ndarray:\n    """Validate the established R lexical contract, then round original decimals."""\n    # Pandas\' numeric conversion can lose binary64 precision. Retain its\n    # existing refusals (including underscores and overflow) as validation,\n    # and obtain correctly rounded values from the original CSV tokens.\n    normalized = values.mask(values.isin(["NaN", "NA"]), np.nan)\n    pd.to_numeric(normalized, errors="raise")\n    return np.fromiter(\n        (np.nan if value in ("NaN", "NA", "") else float(value) for value in values),\n        dtype=float,\n        count=len(values),\n    )\n',
        ),
        (
            b'                else pd.to_numeric(\n                    raw["value"].replace({"NaN": np.nan, "NA": np.nan}), errors="raise"\n                ).to_numpy(float)\n',
            b'                else numeric_vector_values(raw["value"])\n',
        ),
        (
            b'            actual = pd.read_csv(bundle / "source-domains" / f"{case.id}-R.csv")[\n                "value"\n            ].to_numpy(float)\n',
            b'            raw = pd.read_csv(\n                bundle / "source-domains" / f"{case.id}-R.csv",\n                dtype=str,\n                keep_default_na=False,\n            )\n            actual = numeric_vector_values(raw["value"])\n',
        ),
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/retained_reference/comparison.py": (
        (b"", b"    numeric_vector_values,\n"),
        (
            b'    return pd.to_numeric(\n        raw["value"].replace({"NaN": np.nan, "NA": np.nan}), errors="raise"\n    ).to_numpy(float)\n',
            b'    return numeric_vector_values(raw["value"])\n',
        ),
    ),
}

REFERENCE_VECTOR_PRECISION_SOURCES = frozenset(_REFERENCE_VECTOR_IDENTITIES)

_REFERENCE_VECTOR_CAPTURES = {
    "data/method-certification/author-optimizer-diagnostic-source-capture": (
        "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93",
        "executions/optimizer-diagnostics/first-party-inputs/",
    ),
    "data/method-certification/linux-r-source-capture": (
        "fa6e9a4fa9c12013a04cc461fef52d0fd54044d517e132e802a9c176def2a913",
        "source/",
    ),
}


def reference_vector_precision_matches(
    name: str, historical: bytes, current: bytes
) -> bool:
    """Reverse only the original parser spans, then the existing finite IO law."""
    identity = _REFERENCE_VECTOR_IDENTITIES.get(name)
    spans = _REFERENCE_VECTOR_SPANS.get(name)
    if (
        identity is None
        or spans is None
        or len(historical) != identity[0]
        or hashlib.sha256(historical).hexdigest() != identity[1]
        or not 0 < len(current) <= 128 * 1024
    ):
        return False
    restored = current
    for previous, inserted in spans:
        if restored.count(inserted) != 1:
            return False
        restored = restored.replace(inserted, previous, 1)
    if restored == historical:
        return True
    return native_reference_transport_extension_matches(name, historical, restored)


def validated_reference_vector_precision_source(
    repository: Path,
    historical: JsonObject,
    logical: str,
    source_buffer: SourceCapsule,
) -> JsonObject:
    """Authenticate three exact parser paths in their two frozen source contexts."""
    name = historical.get("path")
    identity = _REFERENCE_VECTOR_IDENTITIES.get(name) if isinstance(name, str) else None
    context = _REFERENCE_VECTOR_CAPTURES.get(source_buffer.prefix)
    if identity is None or context is None or not isinstance(name, str):
        raise ReportRebuildError("Reference vector source is outside its fixed scope")
    expected = {"bytes": identity[0], "sha256": identity[1]}
    if (
        repository != repository.resolve()
        or source_buffer.repository != repository
        or source_buffer.descriptor.capture.get("sha256") != context[0]
        or set(historical) != {"path", "bytes", "sha256"}
        or type(historical.get("bytes")) is not int
        or historical != {"path": name, **expected}
        or logical != context[1] + name
        or logical not in source_buffer.detached
        or source_buffer.descriptor.members.get(logical) != expected
        or [
            path
            for group in source_buffer.descriptor.groups
            for member, path in group["resolved_paths"]
            if member == logical
        ]
        != [name]
    ):
        raise ReportRebuildError("Reference vector source member binding differs")
    source_buffer.fresh()
    captured = source_buffer.read_source(logical)
    current_file = _regular_confined_file(
        repository, name, "current reference vector reader"
    )
    before = current_file.stat()
    if before.st_nlink != 1 or not 0 < before.st_size <= 128 * 1024:
        raise ReportRebuildError(
            "Current reference vector reader is linked or unbounded"
        )
    current = current_file.read_bytes()
    if not reference_vector_precision_matches(name, captured, current):
        raise ReportRebuildError("Reference vector source differs beyond token parsing")
    source_buffer.fresh()
    again = _regular_confined_file(repository, name, "current reference vector reader")
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
            "Reference vector source changed during correspondence"
        )
    return {
        "path": name,
        "classification": "finite_reference_vector_precision_extension",
        "original_member": logical,
        "original_sha256": identity[1],
        "original_bytes": identity[0],
        "whole_old_module_reconstructed": True,
        "current_regular_single_link_and_stable": True,
        "current_numeric_parser_changes_binary64_coordinates": True,
        "current_csv_token_lexical_controls_required": True,
        "historical_native_outputs_equal_current_claimed": False,
        "historical_outputs_regenerated": False,
    }
