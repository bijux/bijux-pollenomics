"""Independent winding/distance checks of source-coordinate country support."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
import math
from typing import Any

import pytest

from bijux_pollenomics.adna.species.homo_sapiens.materialization.models import (
    AadrCoordinateEvidence,
)
from bijux_pollenomics.core.geospatial.geojson import CountryBoundaryCollection
from bijux_pollenomics_dev.source_completion.adna.aadr_country_support import (
    coordinate_country_support,
)

DIGEST = "sha256:" + "a" * 64
VERSION = "natural-earth:5.1.1"
Point = tuple[float, float]
Ring = tuple[Point, ...]
Polygon = tuple[Ring, ...]
CountryPolygons = dict[str, tuple[Polygon, ...]]


def coordinate(longitude: float = 1.0, latitude: float = 1.0) -> AadrCoordinateEvidence:
    return AadrCoordinateEvidence(
        str(latitude), str(longitude), latitude, longitude, "admitted"
    )


def square(left: float, bottom: float, right: float, top: float) -> list[list[float]]:
    return [[left, bottom], [right, bottom], [right, top], [left, top], [left, bottom]]


def boundaries(
    *, hole: bool = False, second: bool = False
) -> CountryBoundaryCollection:
    rings = [square(0, 0, 4, 4)]
    if hole:
        rings.append(square(1, 1, 3, 3))
    result = {
        "Sweden": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": rings},
                }
            ],
        }
    }
    if second:
        result["Norway"] = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "MultiPolygon",
                        "coordinates": [[square(2, 0, 6, 4)], [square(8, 0, 9, 1)]],
                    },
                }
            ],
        }
    return result


def independent_polygons(collections: CountryBoundaryCollection) -> CountryPolygons:
    """Parse raw coordinates without maintained polygon/topology helpers."""
    result = {}
    for country, collection in collections.items():
        polygons: list[Polygon] = []
        features: Any = collection["features"]
        for feature in features:
            geometry = feature["geometry"]
            raw = geometry["coordinates"]
            if geometry["type"] == "Polygon":
                raw = [raw]
            else:
                assert geometry["type"] == "MultiPolygon"
            for polygon in raw:
                rings = tuple(
                    tuple((float(vertex[0]), float(vertex[1])) for vertex in ring)
                    for ring in polygon
                )
                assert rings and all(
                    len(ring) >= 4 and ring[0] == ring[-1] for ring in rings
                )
                polygons.append(rings)
        result[country] = tuple(polygons)
    return result


def _winding(point: Point, ring: Ring) -> bool:
    x, y = point
    winding = 0
    for (ax, ay), (bx, by) in zip(ring[:-1], ring[1:], strict=True):
        cross = (bx - ax) * (y - ay) - (x - ax) * (by - ay)
        if ay <= y < by and cross > 0:
            winding += 1
        elif by <= y < ay and cross < 0:
            winding -= 1
    return winding != 0


def _edge_distance(point: Point, ring: Ring) -> float:
    distances = []
    x, y = point
    for (ax, ay), (bx, by) in zip(ring[:-1], ring[1:], strict=True):
        dx, dy = bx - ax, by - ay
        dot = (x - ax) * dx + (y - ay) * dy
        norm = dx * dx + dy * dy
        if dot <= 0 or norm == 0:
            distance = math.hypot(x - ax, y - ay)
        elif dot >= norm:
            distance = math.hypot(x - bx, y - by)
        else:
            distance = abs(dx * (y - ay) - dy * (x - ax)) / math.sqrt(norm)
        distances.append(distance)
    return min(distances)


def independent_decision(
    point: Point, source_country: str, polygons: CountryPolygons
) -> dict[str, str | None]:
    """Observe the declared planar policy independently of its production code.

    A winding number replaces ray casting, and perpendicular line distance
    replaces closest-point reconstruction. The angular review band is a
    policy parameter, not a coordinate-uncertainty estimate.
    """
    containing, contact, shells, nearby = [], [], [], []
    x, y = point
    for country, parts in polygons.items():
        touches = inside = shell = near = False
        for rings in parts:
            exterior = rings[0]
            xs, ys = [v[0] for v in exterior], [v[1] for v in exterior]
            if (
                x < min(xs) - 0.15
                or x > max(xs) + 0.15
                or y < min(ys) - 0.15
                or y > max(ys) + 0.15
            ):
                continue
            distance = min(_edge_distance(point, ring) for ring in rings)
            touches |= distance <= 1e-12
            near |= distance <= 0.15
            outer = _winding(point, exterior)
            shell |= outer
            inside |= outer and not any(_winding(point, ring) for ring in rings[1:])
        if touches:
            contact.append(country)
        if inside:
            containing.append(country)
        if shell:
            shells.append(country)
        if near:
            nearby.append(country)
    country_value: str | None = None
    reason: str | None
    if contact:
        status, method, reason, candidates = (
            "review",
            "point_on_boundary",
            "point_on_boundary",
            contact,
        )
    elif len(containing) > 1:
        status, method, reason, candidates = (
            "review",
            "multiple_boundary_containment",
            "multiple_boundary_containment",
            containing,
        )
    elif containing:
        country_value = containing[0]
        conflict = source_country.strip().casefold() != country_value.casefold()
        status, method, reason, candidates = (
            "review" if conflict else "assigned",
            "strict_boundary_containment",
            "raw_country_conflict" if conflict else None,
            containing,
        )
    elif shells:
        status, method, reason, candidates = (
            "unassigned",
            "no_boundary_containment",
            "inside_boundary_hole",
            shells,
        )
    elif nearby:
        status, method, reason, candidates = (
            "review",
            "boundary_proximity",
            "near_multiple_boundaries"
            if len(nearby) > 1
            else "near_boundary_without_containment",
            nearby,
        )
    else:
        status, method, reason, candidates = (
            "unassigned",
            "no_boundary_containment",
            "outside_governed_boundaries",
            [],
        )
    return {
        "spatial_status": status,
        "spatial_method": method,
        "spatial_country": country_value,
        "spatial_candidates": ";".join(sorted(candidates)),
        "spatial_reason": reason,
    }


def evaluate(
    coordinates: Sequence[AadrCoordinateEvidence],
    *,
    source_country: str = "Sweden",
    collection: CountryBoundaryCollection | None = None,
) -> dict[str, str | None]:
    return coordinate_country_support(
        coordinates,
        source_country=source_country,
        boundaries=boundaries() if collection is None else collection,
        boundary_digest=DIGEST,
        boundary_version=VERSION,
    )


@pytest.mark.parametrize(
    ("point", "hole", "second", "source", "status", "method", "country", "reason"),
    [
        (
            (0.01, 2.0),
            False,
            False,
            "Sweden",
            "assigned",
            "strict_boundary_containment",
            "Sweden",
            None,
        ),
        (
            (0.0, 2.0),
            False,
            False,
            "Sweden",
            "review",
            "point_on_boundary",
            None,
            "point_on_boundary",
        ),
        (
            (-0.15, 2.0),
            False,
            False,
            "Sweden",
            "review",
            "boundary_proximity",
            None,
            "near_boundary_without_containment",
        ),
        (
            (math.nextafter(-0.15, -math.inf), 2.0),
            False,
            False,
            "Sweden",
            "unassigned",
            "no_boundary_containment",
            None,
            "outside_governed_boundaries",
        ),
        (
            (math.nextafter(-0.15, 0.0), 2.0),
            False,
            False,
            "Sweden",
            "review",
            "boundary_proximity",
            None,
            "near_boundary_without_containment",
        ),
        (
            (2.0, 2.0),
            True,
            False,
            "Sweden",
            "unassigned",
            "no_boundary_containment",
            None,
            "inside_boundary_hole",
        ),
        (
            (1.01, 2.0),
            True,
            False,
            "Sweden",
            "unassigned",
            "no_boundary_containment",
            None,
            "inside_boundary_hole",
        ),
        (
            (1.0, 2.0),
            True,
            False,
            "Sweden",
            "review",
            "point_on_boundary",
            None,
            "point_on_boundary",
        ),
        (
            (3.0, 2.0),
            False,
            True,
            "Sweden",
            "review",
            "multiple_boundary_containment",
            None,
            "multiple_boundary_containment",
        ),
        (
            (3.0, -0.1),
            False,
            True,
            "Sweden",
            "review",
            "boundary_proximity",
            None,
            "near_multiple_boundaries",
        ),
        (
            (8.5, 0.5),
            False,
            True,
            "Norway",
            "assigned",
            "strict_boundary_containment",
            "Norway",
            None,
        ),
        (
            (1.0, 2.0),
            False,
            False,
            "Norway",
            "review",
            "strict_boundary_containment",
            "Sweden",
            "raw_country_conflict",
        ),
    ],
)
def test_complete_country_decisions_match_independent_winding_observer(
    point: Point,
    hole: bool,
    second: bool,
    source: str,
    status: str,
    method: str,
    country: str | None,
    reason: str | None,
) -> None:
    collection = boundaries(hole=hole, second=second)
    expected = independent_decision(point, source, independent_polygons(collection))
    assert (
        expected["spatial_status"],
        expected["spatial_method"],
        expected["spatial_country"],
        expected["spatial_reason"],
    ) == (status, method, country, reason)
    assert (
        evaluate((coordinate(*point),), source_country=source, collection=collection)
        == expected
    )


@pytest.mark.parametrize("complement", ["missing", "equivalent_raw", "duplicate"])
def test_one_unique_usable_pair_is_not_overruled_by_group_count(
    complement: str,
) -> None:
    first = coordinate()
    other = (
        AadrCoordinateEvidence("", "", None, None, "missing")
        if complement == "missing"
        else replace(first, latitude_raw="1.000", longitude_raw="1.000")
        if complement == "equivalent_raw"
        else first
    )
    assert evaluate((first, other)) == evaluate((first,))
    assert evaluate((other, first)) == evaluate((first,))


@pytest.mark.parametrize(
    ("coordinates", "reason"),
    [
        ((), "coordinate_missing"),
        (
            (AadrCoordinateEvidence("", "", None, None, "missing"),),
            "coordinate_missing",
        ),
        ((coordinate(), coordinate(2.0, 2.0)), "coordinate_conflict"),
        (
            (AadrCoordinateEvidence("1", "", 1.0, None, "partial"),),
            "coordinate_unresolved",
        ),
        (
            (
                coordinate(),
                AadrCoordinateEvidence("1", "bad", 1.0, None, "invalid_numeric"),
            ),
            "coordinate_unresolved",
        ),
    ],
)
def test_unresolved_source_coordinate_claims_remain_refused(
    coordinates: Sequence[AadrCoordinateEvidence], reason: str
) -> None:
    assert evaluate(coordinates) == {
        "spatial_status": "refused",
        "spatial_method": "coordinate_evidence",
        "spatial_country": None,
        "spatial_candidates": "",
        "spatial_reason": reason,
    }
