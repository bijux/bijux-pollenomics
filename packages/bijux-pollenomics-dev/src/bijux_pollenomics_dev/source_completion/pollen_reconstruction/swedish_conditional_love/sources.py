"""Authenticate complete immutable external capture membership."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.author_snapshot import SCHEMA
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.evidence import producer_input_identity
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import _object
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)

from .authority import CAPTURE_PINS, DESCRIPTOR, DESCRIPTOR_SHA256, SOURCE_ID


def _finite(value: object) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Captured numerical value is not finite")
    if isinstance(value, dict):
        for child in value.values():
            _finite(child)
    elif isinstance(value, list):
        for child in value:
            _finite(child)


def load_inputs(
    repository: Path, source_root: Path, descriptor: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Authenticate the exact captured source population before deriving reader products."""
    qualified = validated_external_report_sources(repository, source_root, descriptor)
    if (
        descriptor.as_posix() != DESCRIPTOR
        or qualified.descriptor_sha256 != DESCRIPTOR_SHA256
    ):
        raise ReportRebuildError("Conditional LOVE descriptor authority changed")
    body = qualified.inputs[DESCRIPTOR].read_bytes()
    control = _object(body)
    if control["schema_version"] != SCHEMA or control["source_id"] != SOURCE_ID:
        raise ReportRebuildError("Conditional LOVE source role differs")
    if {row["path"]: row["sha256"] for row in control["files"]} != CAPTURE_PINS:
        raise ReportRebuildError("Conditional LOVE original capture identities changed")
    expected = {DESCRIPTOR, f"external/{SOURCE_ID}/{control['manifest']['path']}"}
    expected.update(f"external/{SOURCE_ID}/{name}" for name in CAPTURE_PINS)
    if set(qualified.inputs) != expected:
        raise ReportRebuildError("Conditional LOVE source input coverage differs")
    before = producer_input_identity(qualified.inputs, repository)
    values: dict[str, Any] = {}
    for name, expected_hash in CAPTURE_PINS.items():
        path = qualified.inputs[f"external/{SOURCE_ID}/{name}"]
        captured = path.read_bytes()
        if hashlib.sha256(captured).hexdigest() != expected_hash:
            raise ReportRebuildError("Conditional LOVE capture changed before parsing")
        if name in ("model-native-stages.json", "oracle-native-stages.json"):
            value = json.loads(captured)
            if not isinstance(value, list) or not all(
                isinstance(row, dict) for row in value
            ):
                raise ReportRebuildError("Conditional LOVE stage capture shape differs")
            values[name] = value
        else:
            values[name] = _object(captured)
        _finite(values[name])
    if producer_input_identity(qualified.inputs, repository) != before:
        raise ReportRebuildError("Conditional LOVE input bytes changed during parsing")
    return values, before
