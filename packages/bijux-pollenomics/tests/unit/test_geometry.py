from __future__ import annotations

import unittest

from bijux_pollenomics.core.geojson import CountryBoundaryCollection
from bijux_pollenomics.collection.spatial import (
    CountryAttributionDecision,
    classify_country,
    decide_country_attribution,
    geometry_to_representative_point,
    point_in_geometry,
)

BOUNDARY_DIGEST = "sha256:boundary-fixture"
BOUNDARY_VERSION = "natural-earth-5.1.1-test"


def _square_feature(
    *, min_longitude: float, min_latitude: float, size: float = 2.0
) -> dict[str, object]:
    max_longitude = min_longitude + size
    max_latitude = min_latitude + size
    return {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [min_longitude, min_latitude],
                    [max_longitude, min_latitude],
                    [max_longitude, max_latitude],
                    [min_longitude, max_latitude],
                    [min_longitude, min_latitude],
                ]
            ],
        }
    }


def _decision(
    longitude: float,
    latitude: float,
    country_boundaries: CountryBoundaryCollection,
    *,
    raw_country: str | None = None,
    raw_country_aliases: dict[str, str] | None = None,
    proximity_tolerance: float = 0.15,
) -> CountryAttributionDecision:
    return decide_country_attribution(
        longitude,
        latitude,
        country_boundaries,
        boundary_artifact_digest=BOUNDARY_DIGEST,
        boundary_version=BOUNDARY_VERSION,
        raw_country=raw_country,
        raw_country_aliases=raw_country_aliases,
        proximity_tolerance=proximity_tolerance,
    )


class GeometryTests(unittest.TestCase):
    def test_geometry_to_representative_point_prefers_polygon_centroid_over_bbox_center(
        self,
    ) -> None:
        geometry = {
            "type": "Polygon",
            "coordinates": [
                [
                    [0.0, 0.0],
                    [4.0, 0.0],
                    [4.0, 1.0],
                    [1.0, 1.0],
                    [1.0, 4.0],
                    [0.0, 4.0],
                    [0.0, 0.0],
                ]
            ],
        }

        longitude, latitude, geometry_type = geometry_to_representative_point(
            geometry
        ) or (None, None, None)

        self.assertIsNotNone(longitude)
        self.assertIsNotNone(latitude)
        self.assertEqual(geometry_type, "Polygon")
        self.assertNotEqual((longitude, latitude), (2.0, 2.0))
        if longitude is None or latitude is None:
            raise AssertionError("Expected representative point coordinates")
        self.assertTrue(point_in_geometry(longitude, latitude, geometry))

    def test_geometry_to_representative_point_uses_largest_polygon_in_multipolygon(
        self,
    ) -> None:
        geometry = {
            "type": "MultiPolygon",
            "coordinates": [
                [[[0.0, 0.0], [0.5, 0.0], [0.5, 0.5], [0.0, 0.5], [0.0, 0.0]]],
                [
                    [
                        [10.0, 10.0],
                        [14.0, 10.0],
                        [14.0, 14.0],
                        [10.0, 14.0],
                        [10.0, 10.0],
                    ]
                ],
            ],
        }

        longitude, latitude, geometry_type = geometry_to_representative_point(
            geometry
        ) or (None, None, None)

        self.assertIsNotNone(longitude)
        self.assertIsNotNone(latitude)
        self.assertEqual(geometry_type, "MultiPolygon")
        if longitude is None or latitude is None:
            raise AssertionError("Expected representative point coordinates")
        self.assertGreater(longitude, 10.0)
        self.assertGreater(latitude, 10.0)
        self.assertTrue(point_in_geometry(longitude, latitude, geometry))

    def test_country_attribution_keeps_boundary_holes_unassigned(self) -> None:
        country_boundaries: CountryBoundaryCollection = {
            "Sweden": {
                "features": [
                    {
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [0.0, 0.0],
                                    [4.0, 0.0],
                                    [4.0, 4.0],
                                    [0.0, 4.0],
                                    [0.0, 0.0],
                                ],
                                [
                                    [1.0, 1.0],
                                    [3.0, 1.0],
                                    [3.0, 3.0],
                                    [1.0, 3.0],
                                    [1.0, 1.0],
                                ],
                            ],
                        }
                    }
                ]
            }
        }

        decision = _decision(
            2.0,
            2.0,
            country_boundaries,
            proximity_tolerance=0.1,
        )

        self.assertEqual(classify_country(2.0, 2.0, country_boundaries), "")
        self.assertEqual(decision.decision_status, "unassigned")
        self.assertEqual(decision.derived_country, None)
        self.assertEqual(decision.refusal_reason, "inside_boundary_hole")
        self.assertEqual(decision.candidate_countries, ("Sweden",))

    def test_country_attribution_marks_proximity_for_review_without_snapping(
        self,
    ) -> None:
        country_boundaries: CountryBoundaryCollection = {
            "Norway": {
                "features": [
                    {
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [10.0, 60.0],
                                    [13.0, 60.0],
                                    [13.0, 63.0],
                                    [10.0, 63.0],
                                    [10.0, 60.0],
                                ]
                            ],
                        }
                    }
                ]
            }
        }

        decision = _decision(13.05, 61.5, country_boundaries)

        self.assertEqual(classify_country(13.05, 61.5, country_boundaries), "")
        self.assertEqual(decision.decision_status, "review")
        self.assertEqual(decision.decision_method, "boundary_proximity")
        self.assertEqual(decision.derived_country, None)
        self.assertEqual(decision.candidate_countries, ("Norway",))
        self.assertEqual(classify_country(13.5, 61.5, country_boundaries), "")

    def test_country_attribution_assigns_multipart_island_by_strict_containment(
        self,
    ) -> None:
        country_boundaries: CountryBoundaryCollection = {
            "Denmark": {
                "features": [
                    {
                        "geometry": {
                            "type": "MultiPolygon",
                            "coordinates": [
                                [
                                    [
                                        [8.0, 54.0],
                                        [10.0, 54.0],
                                        [10.0, 56.0],
                                        [8.0, 56.0],
                                        [8.0, 54.0],
                                    ]
                                ],
                                [
                                    [
                                        [14.0, 54.5],
                                        [16.0, 54.5],
                                        [16.0, 56.5],
                                        [14.0, 56.5],
                                        [14.0, 54.5],
                                    ]
                                ],
                            ],
                        }
                    }
                ]
            }
        }

        decision = _decision(
            15.0,
            55.0,
            country_boundaries,
            raw_country="DK",
            raw_country_aliases={"DK": "Denmark"},
        )

        self.assertEqual(decision.derived_country, "Denmark")
        self.assertEqual(decision.decision_status, "assigned")
        self.assertEqual(decision.decision_method, "strict_boundary_containment")
        self.assertEqual(decision.raw_country, "DK")
        self.assertEqual(decision.raw_country_comparison, "agrees")
        self.assertEqual(decision.boundary_artifact_digest, BOUNDARY_DIGEST)
        self.assertEqual(decision.boundary_version, BOUNDARY_VERSION)
        self.assertEqual(classify_country(15.0, 55.0, country_boundaries), "Denmark")

    def test_country_attribution_marks_exact_boundary_contact_for_review(self) -> None:
        country_boundaries: CountryBoundaryCollection = {
            "Sweden": {"features": [_square_feature(min_longitude=0, min_latitude=0)]}
        }

        decision = _decision(0.0, 1.0, country_boundaries)

        self.assertEqual(decision.decision_status, "review")
        self.assertEqual(decision.decision_method, "point_on_boundary")
        self.assertEqual(decision.ambiguity_reason, "point_on_boundary")
        self.assertEqual(decision.candidate_countries, ("Sweden",))
        self.assertEqual(classify_country(0.0, 1.0, country_boundaries), "")

    def test_country_attribution_is_order_invariant_for_overlapping_boundaries(
        self,
    ) -> None:
        sweden: dict[str, object] = {
            "features": [_square_feature(min_longitude=0, min_latitude=0)]
        }
        norway: dict[str, object] = {
            "features": [_square_feature(min_longitude=1, min_latitude=0)]
        }

        first = _decision(1.5, 1.0, {"Sweden": sweden, "Norway": norway})
        second = _decision(1.5, 1.0, {"Norway": norway, "Sweden": sweden})

        self.assertEqual(first, second)
        self.assertEqual(first.decision_status, "review")
        self.assertEqual(first.decision_method, "multiple_boundary_containment")
        self.assertEqual(first.candidate_countries, ("Norway", "Sweden"))
        self.assertEqual(
            classify_country(1.5, 1.0, {"Sweden": sweden, "Norway": norway}), ""
        )

    def test_country_attribution_keeps_strict_membership_during_raw_conflict(
        self,
    ) -> None:
        country_boundaries: CountryBoundaryCollection = {
            "Sweden": {"features": [_square_feature(min_longitude=0, min_latitude=0)]}
        }

        decision = _decision(1.0, 1.0, country_boundaries, raw_country="Norway")

        self.assertEqual(decision.derived_country, "Sweden")
        self.assertEqual(decision.decision_status, "review")
        self.assertEqual(decision.decision_method, "strict_boundary_containment")
        self.assertEqual(decision.ambiguity_reason, "raw_country_conflict")
        self.assertEqual(decision.raw_country, "Norway")
        self.assertEqual(decision.raw_country_comparison, "conflicts")

    def test_country_attribution_leaves_equal_proximity_tie_for_review(self) -> None:
        country_boundaries: CountryBoundaryCollection = {
            "Sweden": {"features": [_square_feature(min_longitude=0, min_latitude=0)]},
            "Finland": {
                "features": [_square_feature(min_longitude=2.2, min_latitude=0)]
            },
        }

        decision = _decision(2.1, 1.0, country_boundaries)

        self.assertEqual(decision.decision_status, "review")
        self.assertEqual(decision.decision_method, "boundary_proximity")
        self.assertEqual(decision.ambiguity_reason, "near_multiple_boundaries")
        self.assertEqual(decision.candidate_countries, ("Finland", "Sweden"))
        self.assertEqual(decision.derived_country, None)

    def test_country_attribution_refuses_invalid_coordinates_with_provenance(
        self,
    ) -> None:
        country_boundaries: CountryBoundaryCollection = {
            "Sweden": {"features": [_square_feature(min_longitude=0, min_latitude=0)]}
        }

        decision = _decision(181.0, 1.0, country_boundaries, raw_country="Sweden")

        self.assertEqual(decision.decision_status, "refused")
        self.assertEqual(decision.decision_method, "coordinate_validation")
        self.assertEqual(decision.refusal_reason, "longitude_out_of_range")
        self.assertEqual(decision.raw_country_comparison, "unresolved")
        self.assertEqual(decision.boundary_artifact_digest, BOUNDARY_DIGEST)
        self.assertEqual(decision.boundary_version, BOUNDARY_VERSION)

        boolean_decision = _decision(True, 1.0, country_boundaries)
        self.assertEqual(boolean_decision.decision_status, "refused")
        self.assertEqual(boolean_decision.refusal_reason, "non_numeric_coordinate")

    def test_country_attribution_records_no_containment_without_zero_like_value(
        self,
    ) -> None:
        country_boundaries: CountryBoundaryCollection = {
            "Sweden": {"features": [_square_feature(min_longitude=0, min_latitude=0)]}
        }

        decision = _decision(
            5.0,
            5.0,
            country_boundaries,
            raw_country="Sweden",
            proximity_tolerance=0.1,
        )

        self.assertEqual(decision.decision_status, "unassigned")
        self.assertEqual(decision.decision_method, "no_boundary_containment")
        self.assertEqual(decision.derived_country, None)
        self.assertEqual(decision.refusal_reason, "outside_governed_boundaries")
        self.assertEqual(decision.raw_country_comparison, "unresolved")

    def test_country_attribution_requires_boundary_digest_and_version(self) -> None:
        country_boundaries: CountryBoundaryCollection = {
            "Sweden": {"features": [_square_feature(min_longitude=0, min_latitude=0)]}
        }

        with self.assertRaisesRegex(
            ValueError, "boundary_artifact_digest must be supplied"
        ):
            decide_country_attribution(
                1.0,
                1.0,
                country_boundaries,
                boundary_artifact_digest=" ",
                boundary_version=BOUNDARY_VERSION,
            )
        with self.assertRaisesRegex(ValueError, "boundary_version must be supplied"):
            decide_country_attribution(
                1.0,
                1.0,
                country_boundaries,
                boundary_artifact_digest=BOUNDARY_DIGEST,
                boundary_version=" ",
            )


if __name__ == "__main__":
    unittest.main()
