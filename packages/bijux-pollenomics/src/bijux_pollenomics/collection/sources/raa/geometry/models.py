"""Immutable private-audit identity and source-specific refusal boundaries."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import cast

SCHEMA_VERSION = "raa-native-geometry-audit.v1"
BOUNDARY: dict[str, object] = {
    "geometry_validation": "standard_2d_binary_structure_and_declared_crs_only",
    "topology_validation": "not_evaluated",
    "coordinate_accuracy": "not_evaluated",
    "country_assignment": "not_performed",
    "density_admission": "not_evaluated",
    "representative_coordinates_derived": False,
    "chronology_admission": False,
    "scientific_admission": False,
    "canonical_source_adoption": False,
}


class GeometryRefusal(ValueError):
    """An accounted native payload failure, never a repaired geometry."""

    def __init__(self, reason: str, *, unsupported: bool = False) -> None:
        super().__init__(reason)
        self.reason = reason
        self.status = "unsupported" if unsupported else "invalid"


@dataclass(frozen=True, slots=True)
class RaaGeometryAudit:
    """Published private audit identity with a fresh manifest projection per call."""

    directory: Path
    manifest_sha256: str
    manifest_json: str

    def manifest(self) -> dict[str, object]:
        return cast(dict[str, object], json.loads(self.manifest_json))
