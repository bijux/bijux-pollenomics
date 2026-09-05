from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from unittest.mock import patch

import pytest

from bijux_pollenomics.collection.spatial import country_classification
from bijux_pollenomics.collection.spatial.country_classification import (
    CountryAttributionDecision,
)
from bijux_pollenomics.core.geospatial.geojson import JsonObject


def _square(west: float, east: float) -> JsonObject:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [west, 0.0],
                            [east, 0.0],
                            [east, 2.0],
                            [west, 2.0],
                            [west, 0.0],
                        ]
                    ],
                },
            }
        ],
    }


def _decision(longitude: float, latitude: float) -> CountryAttributionDecision:
    return country_classification.decide_country_attribution(
        longitude,
        latitude,
        {"A": _square(0.0, 2.0), "B": _square(2.0, 4.0)},
        boundary_artifact_digest=" digest ",
        boundary_version=" version ",
    )


def test_strict_boundary_and_coordinate_refusals_are_distinct() -> None:
    boundary = _decision(2.0, 1.0)
    invalid = _decision(math.nan, 1.0)

    assert dataclasses.asdict(boundary) == {
        "derived_country": None,
        "decision_status": "review",
        "decision_method": "point_on_boundary",
        "ambiguity_reason": "point_on_boundary",
        "refusal_reason": None,
        "raw_country": None,
        "raw_country_comparison": "not_supplied",
        "candidate_countries": ("A", "B"),
        "boundary_artifact_digest": "digest",
        "boundary_version": "version",
    }
    assert invalid.decision_status == "refused"
    assert invalid.refusal_reason == "non_finite_coordinate"


@pytest.mark.parametrize(
    ("digest", "version", "tolerance", "message"),
    (
        ("", "v", 0.15, "boundary_artifact_digest must be supplied"),
        ("d", "", 0.15, "boundary_version must be supplied"),
        ("d", "v", -1.0, "proximity_tolerance must be a finite non-negative value"),
    ),
)
def test_invalid_authority_inputs_keep_exact_exception_text(
    digest: str, version: str, tolerance: float, message: str
) -> None:
    with pytest.raises(ValueError, match=f"^{message}$"):
        country_classification.decide_country_attribution(
            1.0,
            1.0,
            {"A": _square(0.0, 2.0)},
            boundary_artifact_digest=digest,
            boundary_version=version,
            proximity_tolerance=tolerance,
        )


def test_decision_keeps_facade_geometry_patch_seams() -> None:
    with (
        patch.object(
            country_classification, "point_on_geometry_boundary", return_value=False
        ),
        patch.object(
            country_classification, "point_in_geometry", return_value=True
        ) as inside,
    ):
        decision = _decision(100.0, 50.0)

    assert decision.derived_country is None
    assert decision.decision_method == "multiple_boundary_containment"
    assert decision.candidate_countries == ("A", "B")
    assert inside.call_count == 2


def test_decision_matrix_keeps_canonical_serialization_hash() -> None:
    decisions = {
        "inside": dataclasses.asdict(_decision(1.0, 1.0)),
        "boundary": dataclasses.asdict(_decision(2.0, 1.0)),
        "outside": dataclasses.asdict(_decision(10.0, 10.0)),
        "invalid": dataclasses.asdict(_decision(181.0, 1.0)),
    }
    digest = hashlib.sha256(
        json.dumps(decisions, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    assert digest == "d581e6e555f8c7d5af4880fd4d49b5b27fa68f7b2de834d32fa7ded1816c589f"
