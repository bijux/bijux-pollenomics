"""Contracts for compact HYDE NetCDF declarations, never native cell values."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from ...quarantine import IntakeRefusal
from ..local.contracts import encode, sha256

SCHEMA = "hyde-netcdf-declaration-inventory.v1"
SCENARIOS = ("base", "lower", "upper")
VARIABLES = (
    "cropland",
    "grazing_land",
    "irrigated_not_rice",
    "irrigated_rice",
    "pasture",
    "population",
    "population_density",
    "rainfed_not_rice",
    "rainfed_rice",
    "rangeland",
    "rural_population",
    "total_irrigated",
    "total_rainfed",
    "total_rice",
    "urban_area",
    "urban_population",
)


@dataclass(frozen=True)
class NetcdfAxisDeclaration:
    """One raw coordinate declaration shared by every retained header."""

    name: Literal["time", "lat", "lon"]
    dtype: str
    dimension: str
    size: int
    unlimited: bool
    standard_name: str
    long_name: str | None
    units: str
    calendar: str | None
    coordinate_values: tuple[float, ...]
    spacing: tuple[float, ...]
    orientation: Literal["ascending", "descending"]


@dataclass(frozen=True)
class NetcdfFileDeclaration:
    """Raw identity and variable declaration for one retained NetCDF file."""

    scenario: Literal["base", "lower", "upper"]
    variable: str
    path: str
    bytes: int
    mtime_ns: int
    source_sha256: str
    file_format: str
    global_attributes: tuple[tuple[str, str], ...]
    dtype: str
    dimensions: tuple[str, ...]
    shape: tuple[int, ...]
    standard_name: str
    long_name: str
    units: str
    fill_value: float


_FACTORY_TOKEN = object()


@dataclass(frozen=True, init=False)
class HydeNetcdfDeclarationInventory:
    """Authenticated declarations that cannot grant scientific admission."""

    input_sha256: tuple[tuple[str, str], ...]
    custody_manifest_sha256: str
    dataset_inventory_sha256: str
    dataset_file_count: int
    dataset_byte_count: int
    axes: tuple[NetcdfAxisDeclaration, ...]
    files: tuple[NetcdfFileDeclaration, ...]
    conflicts: tuple[str, ...]
    schema_version: str = field(default=SCHEMA, init=False)
    scenario_role: str = field(default="provider_estimate_scenarios", init=False)
    pointwise_ordering_contract: str = field(default="none", init=False)
    native_release_admitted: bool = field(default=False, init=False)
    rights_cleared: bool = field(default=False, init=False)
    crs_assigned: bool = field(default=False, init=False)
    canonical_bp_conversion_allowed: bool = field(default=False, init=False)
    scenario_confidence_bounds: bool = field(default=False, init=False)
    publication_allowed: bool = field(default=False, init=False)
    independent_measured_vegetation_truth: bool = field(default=False, init=False)
    scientific_acceptance: str = field(default="not_evaluated", init=False)

    def __init__(
        self,
        *,
        input_sha256: tuple[tuple[str, str], ...],
        custody_manifest_sha256: str,
        dataset_inventory_sha256: str,
        dataset_file_count: int,
        dataset_byte_count: int,
        axes: tuple[NetcdfAxisDeclaration, ...],
        files: tuple[NetcdfFileDeclaration, ...],
        conflicts: tuple[str, ...],
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _FACTORY_TOKEN:
            raise IntakeRefusal("hyde_netcdf_product_factory_required", "inventory")
        object.__setattr__(self, "input_sha256", input_sha256)
        object.__setattr__(self, "custody_manifest_sha256", custody_manifest_sha256)
        object.__setattr__(self, "dataset_inventory_sha256", dataset_inventory_sha256)
        object.__setattr__(self, "dataset_file_count", dataset_file_count)
        object.__setattr__(self, "dataset_byte_count", dataset_byte_count)
        object.__setattr__(self, "axes", axes)
        object.__setattr__(self, "files", files)
        object.__setattr__(self, "conflicts", conflicts)

    @property
    def scenario_counts(self) -> tuple[tuple[str, int], ...]:
        """Return the exact retained scenario denominator."""
        return tuple(
            (scenario, sum(row.scenario == scenario for row in self.files))
            for scenario in SCENARIOS
        )

    def payload(self) -> dict[str, object]:
        """Return a canonical, fully explicit declaration product."""
        return {
            "schema_version": self.schema_version,
            "inputs": dict(self.input_sha256),
            "custody": {
                "manifest_sha256": self.custody_manifest_sha256,
                "dataset_inventory_sha256": self.dataset_inventory_sha256,
                "dataset_file_count": self.dataset_file_count,
                "dataset_byte_count": self.dataset_byte_count,
            },
            "axes": [
                {
                    "name": axis.name,
                    "dtype": axis.dtype,
                    "dimension": axis.dimension,
                    "size": axis.size,
                    "unlimited": axis.unlimited,
                    "standard_name": axis.standard_name,
                    "long_name": axis.long_name,
                    "units": axis.units,
                    "calendar": axis.calendar,
                    "coordinate_values": list(axis.coordinate_values),
                    "spacing": list(axis.spacing),
                    "orientation": axis.orientation,
                }
                for axis in self.axes
            ],
            "files": [
                {
                    "scenario": row.scenario,
                    "variable": row.variable,
                    "path": row.path,
                    "bytes": row.bytes,
                    "mtime_ns": row.mtime_ns,
                    "source_sha256": row.source_sha256,
                    "file_format": row.file_format,
                    "global_attributes": dict(row.global_attributes),
                    "dtype": row.dtype,
                    "dimensions": list(row.dimensions),
                    "shape": list(row.shape),
                    "standard_name": row.standard_name,
                    "long_name": row.long_name,
                    "units": row.units,
                    "fill_value": row.fill_value,
                }
                for row in self.files
            ],
            "scenario_semantics": {
                "counts": dict(self.scenario_counts),
                "role": self.scenario_role,
                "confidence_bounds": self.scenario_confidence_bounds,
                "pointwise_ordering_contract": self.pointwise_ordering_contract,
            },
            "conflicts": list(self.conflicts),
            "admission": {
                "native_release_admitted": self.native_release_admitted,
                "rights_cleared": self.rights_cleared,
                "crs_assigned": self.crs_assigned,
                "canonical_bp_conversion_allowed": self.canonical_bp_conversion_allowed,
                "publication_allowed": self.publication_allowed,
                "independent_measured_vegetation_truth": (
                    self.independent_measured_vegetation_truth
                ),
                "scientific_acceptance": self.scientific_acceptance,
            },
        }

    @property
    def canonical_bytes(self) -> bytes:
        """Return deterministic product bytes without opening source payloads."""
        return encode(self.payload())

    @property
    def sha256(self) -> str:
        """Return the canonical declaration-product identity."""
        return sha256(self.canonical_bytes)


def _mint_inventory(
    *,
    input_sha256: tuple[tuple[str, str], ...],
    custody_manifest_sha256: str,
    dataset_inventory_sha256: str,
    dataset_file_count: int,
    dataset_byte_count: int,
    axes: tuple[NetcdfAxisDeclaration, ...],
    files: tuple[NetcdfFileDeclaration, ...],
    conflicts: tuple[str, ...],
) -> HydeNetcdfDeclarationInventory:
    return HydeNetcdfDeclarationInventory(
        input_sha256=input_sha256,
        custody_manifest_sha256=custody_manifest_sha256,
        dataset_inventory_sha256=dataset_inventory_sha256,
        dataset_file_count=dataset_file_count,
        dataset_byte_count=dataset_byte_count,
        axes=axes,
        files=files,
        conflicts=conflicts,
        _factory_token=_FACTORY_TOKEN,
    )
