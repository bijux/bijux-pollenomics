"""Country-boundary fixture shared by source normalization tests."""

import unittest


class NordicBoundaryTestCase(unittest.TestCase):
    """Provide a minimal Sweden polygon for deterministic country resolution."""

    country_boundaries: dict[str, dict[str, object]]

    def setUp(self) -> None:
        self.country_boundaries = {
            "Sweden": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [10.0, 55.0],
                                    [25.0, 55.0],
                                    [25.0, 70.0],
                                    [10.0, 70.0],
                                    [10.0, 55.0],
                                ]
                            ],
                        },
                        "properties": {"name": "Sweden"},
                    }
                ],
            }
        }


__all__ = ["NordicBoundaryTestCase"]
