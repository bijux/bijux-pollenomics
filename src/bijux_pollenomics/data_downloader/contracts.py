from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DataArtifactContract:
    source: str
    label: str
    relative_parts: tuple[str, ...]

    @property
    def filename(self) -> str:
        return self.relative_parts[-1]

    def path_under(self, output_root: Path) -> Path:
        """Resolve this artifact under a full data root."""
        return Path(output_root).joinpath(self.source, *self.relative_parts)

    def source_path_under(self, source_output_root: Path) -> Path:
        """Resolve this artifact under one source output directory."""
        return Path(source_output_root).joinpath(*self.relative_parts)


BOUNDARY_COLLECTION = DataArtifactContract(
    source="boundaries",
    label="Nordic country boundaries",
    relative_parts=("normalized", "nordic_country_boundaries.geojson"),
)
LANDCLIM_SITE_CSV = DataArtifactContract(
    source="landclim",
    label="LandClim pollen site CSV",
    relative_parts=("normalized", "nordic_pollen_site_sequences.csv"),
)
LANDCLIM_SITE_GEOJSON = DataArtifactContract(
    source="landclim",
    label="LandClim pollen site GeoJSON",
    relative_parts=("normalized", "nordic_pollen_site_sequences.geojson"),
)
LANDCLIM_GRID_GEOJSON = DataArtifactContract(
    source="landclim",
    label="LandClim REVEALS grid GeoJSON",
    relative_parts=("normalized", "nordic_reveals_grid_cells.geojson"),
)
NEOTOMA_POINT_CSV = DataArtifactContract(
    source="neotoma",
    label="Neotoma pollen CSV",
    relative_parts=("normalized", "nordic_pollen_sites.csv"),
)
NEOTOMA_POINT_GEOJSON = DataArtifactContract(
    source="neotoma",
    label="Neotoma pollen GeoJSON",
    relative_parts=("normalized", "nordic_pollen_sites.geojson"),
)
SEAD_POINT_CSV = DataArtifactContract(
    source="sead",
    label="SEAD site CSV",
    relative_parts=("normalized", "nordic_environmental_sites.csv"),
)
SEAD_POINT_GEOJSON = DataArtifactContract(
    source="sead",
    label="SEAD site GeoJSON",
    relative_parts=("normalized", "nordic_environmental_sites.geojson"),
)
RAA_LAYER_METADATA = DataArtifactContract(
    source="raa",
    label="RAÄ archaeology layer metadata",
    relative_parts=("normalized", "sweden_archaeology_layer.json"),
)
RAA_DENSITY_GEOJSON = DataArtifactContract(
    source="raa",
    label="RAÄ archaeology density",
    relative_parts=("normalized", "sweden_archaeology_density.geojson"),
)

ATLAS_POINT_ARTIFACTS = (
    LANDCLIM_SITE_GEOJSON,
    NEOTOMA_POINT_GEOJSON,
    SEAD_POINT_GEOJSON,
)
