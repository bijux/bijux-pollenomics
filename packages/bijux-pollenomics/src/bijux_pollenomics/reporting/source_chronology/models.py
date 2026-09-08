"""Result contracts for source-chronology atlas projection."""

from __future__ import annotations

from dataclasses import dataclass

from bijux_pollenomics.core.geospatial.geojson import JsonObject


@dataclass(frozen=True)
class SourceChronologyAtlasProjection:
    """Three point layers and their denominator-complete accounting."""

    point_layers: tuple[JsonObject, ...]
    reconciliation: JsonObject


__all__ = ["SourceChronologyAtlasProjection"]
