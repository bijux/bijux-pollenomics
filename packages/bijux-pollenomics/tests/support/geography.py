from __future__ import annotations

NORDIC_TEST_BBOX = (4.0, 54.0, 35.0, 72.0)


def rectangular_country_boundaries(
    country: str,
    *,
    west: float,
    south: float,
    east: float,
    north: float,
) -> dict[str, object]:
    """Build a simple rectangular country boundary collection for tests."""
    return {
        country: {
            "features": [
                {
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [west, south],
                                [east, south],
                                [east, north],
                                [west, north],
                                [west, south],
                            ]
                        ],
                    }
                }
            ]
        }
    }


SWEDEN_BOUNDARIES = rectangular_country_boundaries(
    "Sweden",
    west=16.0,
    south=58.0,
    east=19.0,
    north=60.5,
)
