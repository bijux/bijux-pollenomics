from __future__ import annotations

from bijux_pollenomics.core.geospatial.geojson import JsonObject


def build_point_layers(*, large: bool = False) -> list[JsonObject]:
    description = "x" * 30_000 if large else "source-owned point"
    count = 100 if large else 2
    return [
        {
            "key": "pollen-sites",
            "label": "Pollen sites",
            "group": "environmental-context",
            "source_name": "Example source",
            "default_enabled": True,
            "features": [
                {
                    "title": f"evidence-{index}",
                    "country": "Sweden" if index % 2 == 0 else "Norway",
                    "latitude": 59.0 + index / 1000,
                    "longitude": 18.0 + index / 1000,
                    "time_start_bp": index,
                    "time_end_bp": index + 100,
                    "description": description,
                }
                for index in range(count)
            ],
        }
    ]


def build_polygon_layers() -> list[JsonObject]:
    return [
        {
            "key": "country-boundaries",
            "label": "Country boundaries",
            "group": "orientation",
            "source_name": "Boundary source",
            "default_enabled": True,
            "geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [17.0, 58.0],
                                    [19.0, 58.0],
                                    [19.0, 60.0],
                                    [17.0, 60.0],
                                    [17.0, 58.0],
                                ]
                            ],
                        },
                        "properties": {"country": "Sweden"},
                    }
                ],
            },
        }
    ]


__all__ = ["build_point_layers", "build_polygon_layers"]
