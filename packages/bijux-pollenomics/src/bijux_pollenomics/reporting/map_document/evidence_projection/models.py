"""Atlas evidence projection result records."""

from __future__ import annotations

from dataclasses import dataclass

from bijux_pollenomics.core.geospatial.geojson import JsonObject


@dataclass(frozen=True)
class MapEvidenceProjection:
    """Deterministic detail records and their feature/detail accounting."""

    detail_records: tuple[JsonObject, ...]
    reconciliation: JsonObject
    point_layers: tuple[JsonObject, ...] = ()
