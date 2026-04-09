from __future__ import annotations

import unittest

from bijux_pollenomics.data_downloader.spatial import (
    classify_country,
    geometry_to_representative_point,
    point_in_geometry,
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

        self.assertEqual(geometry_type, "Polygon")
        self.assertNotEqual((longitude, latitude), (2.0, 2.0))
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

        self.assertEqual(geometry_type, "MultiPolygon")
        self.assertGreater(longitude, 10.0)
        self.assertGreater(latitude, 10.0)
        self.assertTrue(point_in_geometry(longitude, latitude, geometry))

    def test_classify_country_recovers_points_in_boundary_holes(self) -> None:
        country_boundaries = {
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

        self.assertEqual(classify_country(2.0, 2.0, country_boundaries), "Sweden")

    def test_classify_country_recovers_points_just_outside_boundary(self) -> None:
        country_boundaries = {
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

        self.assertEqual(classify_country(13.05, 61.5, country_boundaries), "Norway")
        self.assertEqual(classify_country(13.5, 61.5, country_boundaries), "")


if __name__ == "__main__":
    unittest.main()
