"""Typed facade seam for country-attribution policy."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from ....core.geospatial.geojson import CountryBoundaryCollection, JsonObject
from .model import RawCountryComparison


class CountryClassificationDependencies(Protocol):
    def _geometries_by_country(
        self, country_boundaries: CountryBoundaryCollection
    ) -> dict[str, tuple[JsonObject, ...]]: ...

    def _coordinate_refusal_reason(
        self, longitude: float, latitude: float
    ) -> str | None: ...

    def _optional_country(self, raw_country: str | None) -> str | None: ...

    def _compare_raw_country(
        self,
        *,
        raw_country: str | None,
        derived_country: str,
        raw_country_aliases: Mapping[str, str] | None,
    ) -> RawCountryComparison: ...

    def point_on_geometry_boundary(
        self,
        longitude: float,
        latitude: float,
        geometry: JsonObject,
        *,
        epsilon: float = ...,
    ) -> bool: ...

    def point_in_geometry(
        self, longitude: float, latitude: float, geometry: JsonObject
    ) -> bool: ...

    def point_in_geometry_ignoring_holes(
        self, longitude: float, latitude: float, geometry: JsonObject
    ) -> bool: ...

    def geometry_boundary_distance(
        self, longitude: float, latitude: float, geometry: JsonObject
    ) -> float: ...
