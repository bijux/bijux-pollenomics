from __future__ import annotations

from bijux_pollenomics.collection.sources.neotoma.normalization import (
    build_neotoma_site_country_decisions,
)
from bijux_pollenomics.collection.spatial import CountryAttributionDecision


def country_boundaries() -> dict[str, dict[str, object]]:
    return {
        "Sweden": {
            "features": [
                {
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [0.0, 0.0],
                                [2.0, 0.0],
                                [2.0, 2.0],
                                [0.0, 2.0],
                                [0.0, 0.0],
                            ]
                        ],
                    }
                }
            ]
        },
        "Norway": {
            "features": [
                {
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [3.0, 0.0],
                                [5.0, 0.0],
                                [5.0, 2.0],
                                [3.0, 2.0],
                                [3.0, 0.0],
                            ]
                        ],
                    }
                }
            ]
        },
    }


def country_decisions(
    rows: list[dict[str, object]],
    boundaries: dict[str, dict[str, object]] | None = None,
) -> dict[str, CountryAttributionDecision]:
    return build_neotoma_site_country_decisions(
        rows,
        boundaries or country_boundaries(),
        boundary_artifact_digest="sha256:boundary-fixture",
        boundary_version="boundary-fixture-v1",
    )
