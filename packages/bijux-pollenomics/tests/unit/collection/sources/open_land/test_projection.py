from __future__ import annotations

from decimal import Decimal

import pytest

from bijux_pollenomics.collection.sources.open_land.models import ModeledLandCoverCell
from bijux_pollenomics.collection.sources.open_land.projection import (
    project_nordic_modeled_land_cover,
)
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal


def _cell(
    longitude: str,
    latitude: str,
    *,
    row_number: int,
    time_slice_bp: int = 50,
    younger_bp: int = 0,
    older_bp: int = 100,
    coniferous: str = "0.2",
) -> ModeledLandCoverCell:
    broadleaved = Decimal("0.3")
    open_land = Decimal(1) - Decimal(coniferous) - broadleaved
    return ModeledLandCoverCell(
        source_member=f"Land_Cover_{time_slice_bp}.csv",
        source_member_sha256="1" * 64,
        source_row_number=row_number,
        time_slice_bp=time_slice_bp,
        younger_bp=younger_bp,
        older_bp=older_bp,
        longitude_claim=Decimal(longitude),
        latitude_claim=Decimal(latitude),
        coniferous_proportion=Decimal(coniferous),
        broadleaved_proportion=broadleaved,
        unforested_open_proportion=open_land,
        source_values=(longitude, latitude, coniferous, "0.3", str(open_land)),
    )


def _boundaries() -> dict[str, dict[str, object]]:
    return {
        country: {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [west, 0],
                                [west + 2, 0],
                                [west + 2, 2],
                                [west, 2],
                                [west, 0],
                            ]
                        ],
                    },
                }
            ],
        }
        for country, west in (
            ("Sweden", 0),
            ("Denmark", 3),
            ("Norway", 6),
            ("Finland", 9),
        )
    }


def test_projection_is_chronological_complete_and_context_only() -> None:
    cells = (
        _cell("1", "1", row_number=2, coniferous="0"),
        _cell(
            "1",
            "1",
            row_number=2,
            time_slice_bp=1500,
            younger_bp=1200,
            older_bp=1700,
        ),
        _cell("4", "1", row_number=3),
        _cell("7", "1", row_number=4),
        _cell("10", "1", row_number=5),
        _cell("2.1", "1", row_number=6),
        _cell("20", "1", row_number=7),
    )

    projection = project_nordic_modeled_land_cover(
        cells,
        country_boundaries=_boundaries(),
        boundary_artifact_digest="b" * 64,
        boundary_version="synthetic-boundaries",
    )

    features = projection.feature_collection["features"]
    assert isinstance(features, list)
    assert len(features) == 5
    assert features[0]["properties"]["time_end_bp"] == 1700
    zero_feature = next(
        feature
        for feature in features
        if feature["properties"]["coniferous_proportion"] == "0"
    )
    assert zero_feature["properties"]["coniferous_proportion_numeric"] == 0.0
    assert zero_feature["properties"]["propagation_use_allowed"] is False
    assert zero_feature["properties"]["public_release_allowed"] is False
    assert zero_feature["geometry"]["coordinates"] == [
        [[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]]
    ]
    assert projection.reconciliation["source_row_count"] == 7
    assert projection.reconciliation["unique_source_center_count"] == 6
    assert projection.reconciliation["country_decision_row_counts"] == {
        "assigned": 5,
        "review": 1,
        "unassigned": 1,
        "refused": 0,
    }
    assert projection.reconciliation["country_counts"] == {
        "SE": {"assigned_source_rows": 2, "unique_assigned_centers": 1},
        "DK": {"assigned_source_rows": 1, "unique_assigned_centers": 1},
        "NO": {"assigned_source_rows": 1, "unique_assigned_centers": 1},
        "FI": {"assigned_source_rows": 1, "unique_assigned_centers": 1},
    }
    decisions = {
        (decision["longitude"], decision["latitude"]): decision
        for decision in projection.country_decisions
    }
    assert decisions[("2.1", "1")]["decision_status"] == "review"
    assert decisions[("2.1", "1")]["decision_method"] == "boundary_proximity"
    assert decisions[("1", "1")]["source_time_slices_bp"] == [1500, 50]


def test_duplicate_slice_coordinate_is_refused() -> None:
    cell = _cell("1", "1", row_number=2)

    with pytest.raises(IntakeRefusal, match="duplicate_open_land_projection_row"):
        project_nordic_modeled_land_cover(
            (cell, cell),
            country_boundaries=_boundaries(),
            boundary_artifact_digest="b" * 64,
            boundary_version="synthetic-boundaries",
        )


def test_projection_refuses_incomplete_nordic_boundary_authority() -> None:
    boundaries = _boundaries()
    del boundaries["Finland"]

    with pytest.raises(IntakeRefusal, match="open_land_boundary_country_set_mismatch"):
        project_nordic_modeled_land_cover(
            (_cell("1", "1", row_number=2),),
            country_boundaries=boundaries,
            boundary_artifact_digest="b" * 64,
            boundary_version="synthetic-boundaries",
        )
