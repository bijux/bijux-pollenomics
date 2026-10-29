"""Only the named package exports may differ from authenticated historical bytes."""

from __future__ import annotations

from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.spatial_source_exports import (
    spatial_export_extension_matches,
)

OLD = b"\n".join(
    [
        b'"""Existing package bindings."""',
        b"",
        b"from .configuration import SiteCoordinate, SpatialConfig",
        b"from .counts import HALF_COUNT, HALF_COUNT_POLICY, half_count_composition",
        b"from .model import FittedSpatialModel, SpatialPrediction, fit_spatial_model",
        b"",
        b"__all__ = [",
        b'    "FittedSpatialModel",',
        b'    "HALF_COUNT",',
        b'    "HALF_COUNT_POLICY",',
        b'    "SiteCoordinate",',
        b'    "SpatialConfig",',
        b'    "SpatialPrediction",',
        b'    "fit_spatial_model",',
        b'    "half_count_composition",',
        b"]",
        b"",
    ]
)
NEW = (
    OLD.replace(
        b"from .model import",
        b"from .identifiability import spatial_identifiability\nfrom .model import",
    )
    .replace(
        b"\n\n__all__",
        b"\nfrom .uncertainty import (\n"
        b"    JointSpatialDraw,\n    UnavailableSpatialDraw,\n"
        b"    propagate_withheld_spatial_draws,\n)\n\n__all__",
    )
    .replace(
        b'    "FittedSpatialModel",\n',
        b'    "FittedSpatialModel",\n    "JointSpatialDraw",\n'
        b'    "UnavailableSpatialDraw",\n    "propagate_withheld_spatial_draws",\n'
        b'    "spatial_identifiability",\n',
    )
)


def test_named_exports_preserve_original_bindings() -> None:
    assert spatial_export_extension_matches(OLD, NEW)
    assert not spatial_export_extension_matches(OLD, OLD)
    assert not spatial_export_extension_matches(NEW, NEW)


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (b"HALF_COUNT, HALF_COUNT_POLICY", b"OTHER as HALF_COUNT, HALF_COUNT_POLICY"),
        (b"import spatial_identifiability", b"import other as spatial_identifiability"),
        (b"import spatial_identifiability\n", b"import spatial_identifiability; f()\n"),
        (
            b"import spatial_identifiability\n",
            b"import spatial_identifiability # comment\n",
        ),
        (b'    "JointSpatialDraw",\n', b'    "JointSpatialDraw", f(),\n'),
        (b'    "JointSpatialDraw",\n', b'    "JointSpatialDraw", # comment\n'),
        (
            b'    "JointSpatialDraw",\n',
            b'    "JointSpatialDraw",\n    "JointSpatialDraw",\n',
        ),
        (b'    "JointSpatialDraw",\n', b'    "Unexpected",\n'),
        (b'    "HALF_COUNT",\n', b""),
        (b"Existing package bindings", b"Altered package bindings"),
        (b"from .uncertainty import (", b"from .other import ("),
        (b"from .identifiability import", b"from .uncertainty import"),
        (b"__all__ = [", b"__all__ = list(["),
    ],
)
def test_unregistered_or_hidden_changes_are_refused(
    before: bytes, after: bytes
) -> None:
    assert not spatial_export_extension_matches(OLD, NEW.replace(before, after))


@pytest.mark.parametrize("suffix", [b"f()\n", b"# extra comment\n", b"__all__ = []\n"])
def test_additional_statements_or_comments_are_refused(suffix: bytes) -> None:
    assert not spatial_export_extension_matches(OLD, NEW + suffix)


@pytest.mark.parametrize(
    "value", [None, True, "text", bytearray(b"body"), b"", b"x" * 4097]
)
def test_invalid_or_unbounded_current_input_is_refused(value: Any) -> None:
    assert not spatial_export_extension_matches(OLD, value)


def test_invalid_historical_or_syntax_inputs_are_refused() -> None:
    assert not spatial_export_extension_matches(b"", NEW)
    assert not spatial_export_extension_matches(b"x" * 4097, NEW)
    assert not spatial_export_extension_matches(OLD, b"\xff")
    assert not spatial_export_extension_matches(OLD, b"def invalid(")
