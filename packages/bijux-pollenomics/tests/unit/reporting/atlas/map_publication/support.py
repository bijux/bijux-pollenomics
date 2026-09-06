from __future__ import annotations

import json
import unittest
from pathlib import Path


class MapPublicationTestCase(unittest.TestCase):
    @staticmethod
    def _write_point_geojson(
        path: Path,
        *,
        layer_key: str,
        layer_label: str,
        record_id: str = "",
        time_start_bp: int | None = None,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [18.06, 59.33],
                            },
                            "properties": {
                                "layer_key": layer_key,
                                "layer_label": layer_label,
                                "name": "Example point",
                                "category": "Context",
                                "subtitle": "Example context layer",
                                "country": "Sweden",
                                "record_id": record_id,
                                "time_start_bp": time_start_bp,
                            },
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _write_polygon_geojson(path: Path, *, layer_key: str, layer_label: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [
                                    [
                                        [10.0, 55.0],
                                        [11.0, 55.0],
                                        [11.0, 56.0],
                                        [10.0, 56.0],
                                        [10.0, 55.0],
                                    ]
                                ],
                            },
                            "properties": {
                                "layer_key": layer_key,
                                "layer_label": layer_label,
                                "subtitle": "Example polygon layer",
                            },
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
