"""Private, pre-normalized comparison types; no claim of native HYDE admission."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Literal

from ..quarantine import IntakeRefusal
from .grid import GridSpec, finite_number
from .time import TimeSupport


@dataclass(frozen=True)
class VariableSpec:
    """A single source-labelled quantity; area, fractions and people stay distinct."""

    source_label: str
    category_key: str
    scenario: str
    quantity: Literal["land_fraction", "area_km2", "population"]
    units: str

    def __post_init__(self) -> None:
        expected_units = {
            "land_fraction": "1",
            "area_km2": "km2",
            "population": "persons",
        }
        if (
            not isinstance(self.quantity, str)
            or self.quantity not in expected_units
            or self.units != expected_units[self.quantity]
        ):
            raise IntakeRefusal(
                "hyde_quantity_units_unsupported", repr((self.quantity, self.units))
            )
        if not all(
            isinstance(value, str) and value.strip()
            for value in (self.source_label, self.category_key, self.scenario)
        ):
            raise IntakeRefusal("hyde_variable_identity_missing", repr(self))


@dataclass(frozen=True)
class DeclaredGridLayer:
    """Hash-bound internal interchange whose source admission remains unverified."""

    interchange_sha256: str
    source_kind: Literal["synthetic_fixture", "pre_normalized_candidate"]
    release_claim: str
    source_url: str | None
    citation: str | None
    license_claim: str | None
    grid: GridSpec
    time: TimeSupport
    variable: VariableSpec
    values: tuple[float | None, ...]
    land_fractions: tuple[float, ...]
    source_values: tuple[int | float | None, ...]
    nodata_value: float | None
    native_hyde_admission_verified: bool = field(default=False, init=False)
    public_release_allowed: bool = field(default=False, init=False)
    evidence_role: str = field(default="modeled_comparison_only", init=False)

    def __post_init__(self) -> None:
        if self.source_kind not in ("synthetic_fixture", "pre_normalized_candidate"):
            raise IntakeRefusal("hyde_native_format_unverified", self.source_kind)
        if (
            not isinstance(self.interchange_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", self.interchange_sha256) is None
        ):
            raise IntakeRefusal(
                "hyde_interchange_digest_invalid", repr(self.interchange_sha256)
            )
        if (
            self.source_kind == "synthetic_fixture"
            and self.release_claim != "synthetic-fixture"
        ) or (
            self.source_kind == "pre_normalized_candidate"
            and self.release_claim != "3.5"
        ):
            raise IntakeRefusal("hyde_release_claim_unsupported", self.release_claim)
        count = self.grid.rows * self.grid.columns
        if not (
            len(self.values)
            == len(self.land_fractions)
            == len(self.source_values)
            == count
        ):
            raise IntakeRefusal("hyde_cell_count_mismatch", str(count))
        for index, (value, land) in enumerate(
            zip(self.values, self.land_fractions, strict=True)
        ):
            land = finite_number(land, f"land_fraction[{index}]")
            if not 0 <= land <= 1:
                raise IntakeRefusal("hyde_land_fraction_invalid", str(index))
            if value is None:
                continue
            value = finite_number(value, f"value[{index}]")
            if value < 0 or (self.variable.quantity == "land_fraction" and value > 1):
                raise IntakeRefusal("hyde_value_out_of_range", str(index))
            if land == 0 and value != 0:
                raise IntakeRefusal("hyde_nonzero_value_on_water_cell", str(index))
            if self.variable.quantity == "area_km2":
                row, column = divmod(index, self.grid.columns)
                if value > self.grid.cell_bounds(row, column).area_km2 * land:
                    raise IntakeRefusal("hyde_area_exceeds_land_support", str(index))
