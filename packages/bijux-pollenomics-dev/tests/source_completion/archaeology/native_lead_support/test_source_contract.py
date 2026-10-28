"""Retain source-native byte identity and false admission flags independently."""

from __future__ import annotations

from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.source_contracts.raa_native_geopackage import (
    SOURCE_BYTES,
    SOURCE_SHA256,
    SOURCE_URL,
    check_capture,
)


def fixture_capture() -> tuple[dict[str, Any], dict[str, Any]]:
    return {
        "sha256": SOURCE_SHA256,
        "byte_count": SOURCE_BYTES,
        "file": "lamningar_sverige.gpkg",
        "url": SOURCE_URL,
        "scientific_admission": False,
        "canonical_adoption": False,
    }, {"sha256": SOURCE_SHA256, "size": SOURCE_BYTES}


def test_original_capture_metadata_keeps_false_admission_flags() -> None:
    capture, native = fixture_capture()
    check_capture(capture, native)


@pytest.mark.parametrize(
    "field,value",
    [
        ("scientific_admission", True),
        ("canonical_adoption", 0),
        ("byte_count", float(SOURCE_BYTES)),
        ("url", "https://example.org/foreign"),
        ("sha256", "0" * 64),
    ],
)
def test_capture_qualification_never_promotes_or_coerces_source(
    field: str, value: object
) -> None:
    capture, native = fixture_capture()
    capture[field] = value
    with pytest.raises(ReportRebuildError, match="capture identity|nonadmission"):
        check_capture(capture, native)


def test_native_source_member_cannot_be_replaced() -> None:
    capture, native = fixture_capture()
    native["sha256"] = "0" * 64
    with pytest.raises(ReportRebuildError, match="national byte identity"):
        check_capture(capture, native)
