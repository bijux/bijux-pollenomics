"""Finite private products for conditional source-native registry UUID counts."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import cast

SCHEMA_VERSION = "raa-native-point-grid-v1"
DISPOSITIONS = (
    "unselected_native_class",
    "no_primary_point_occurrence",
    "multiple_primary_point_occurrences",
    "unsupported_sole_point",
    "unsupported_projection_or_location",
    "included",
)
BOUNDARY: dict[str, object] = {
    "counted_unit": "conditional_source_native_lamning_uuid_per_declared_cell",
    "scientific_admission": False,
    "historical_WFS_density_equivalence": False,
    "country_assignment": "not_performed",
    "chronology_admission": False,
    "archaeological_event_interpretation": False,
    "area_density_or_population_estimate": False,
    "coordinate_accuracy": "not_evaluated",
    "private_uuid_ledger": True,
    "non_point_geometry_validation": "not_performed",
    "uncertainty_geometry_used_for_location": False,
    "canonical_source_adoption": False,
}


@dataclass(frozen=True, slots=True)
class NativePointGridLimits:
    """Explicit source-row, point-blob and complete private-output budgets."""

    max_uuid_records: int
    max_geometry_rows: int
    max_point_bytes: int
    max_output_bytes: int

    def __post_init__(self) -> None:
        """Refuse ambiguous or unbounded input and publication budgets."""
        if any(
            type(value) is not int or value <= 0
            for value in (
                self.max_uuid_records,
                self.max_geometry_rows,
                self.max_point_bytes,
                self.max_output_bytes,
            )
        ):
            raise ValueError("Native POINT budgets require positive native integers")


@dataclass(frozen=True, slots=True)
class RaaNativePointGrid:
    """Published report identity without exposing a mutable shared report."""

    directory: Path
    report_sha256: str
    report_json: str

    def report(self) -> dict[str, object]:
        """Return a detached aggregate/provenance projection, never the UUID ledger."""
        return cast(dict[str, object], json.loads(self.report_json))
