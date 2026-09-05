"""Fail-closed atlas projection validation tests."""

from __future__ import annotations

from copy import deepcopy
from typing import cast

import pytest

from bijux_pollenomics.reporting.source_chronology import (
    SourceChronologyAtlasProjection,
    validate_source_chronology_atlas_projection,
)

from .support import DETAIL_ID, projection


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("record_id", "neotoma:site:unknown"),
        ("propagation_eligible", True),
        ("time_start_bp", 126),
        ("edge_id", "invented-edge"),
    ],
)
def test_projection_rejects_semantic_tampering(field: str, value: object) -> None:
    result, atlas = projection()
    layers = deepcopy(atlas.point_layers)
    feature = cast(list[dict[str, object]], layers[0]["features"])[0]
    feature[field] = value
    tampered = SourceChronologyAtlasProjection(
        point_layers=layers,
        reconciliation=atlas.reconciliation,
    )

    with pytest.raises(ValueError):
        validate_source_chronology_atlas_projection(
            result,
            tampered,
            detail_record_ids={DETAIL_ID},
        )


def test_projection_rejects_missing_canonical_site_detail() -> None:
    result, atlas = projection()

    with pytest.raises(ValueError, match="has no site detail"):
        validate_source_chronology_atlas_projection(
            result,
            atlas,
            detail_record_ids=set(),
        )
