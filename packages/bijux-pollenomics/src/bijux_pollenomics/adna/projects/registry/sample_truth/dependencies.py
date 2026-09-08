"""Typed facade seam for sample-truth orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class SpeciesDefinition(Protocol):
    latin_name: str
    common_name: str


class SampleTruthDependencies(Protocol):
    TRACKED_ADNA_SPECIES: tuple[str, ...]

    def resolve_species_definition(self, name: str) -> SpeciesDefinition: ...

    def _species_root(self, data_root: Path, species_name: str) -> Path: ...

    def _load_sample_rows(self, species_root: Path) -> list[dict[str, object]]: ...

    def _load_locality_rows(self, species_root: Path) -> list[dict[str, object]]: ...

    def _load_all_sample_rows(self, data_root: Path) -> list[dict[str, object]]: ...

    def _load_all_locality_rows(self, data_root: Path) -> list[dict[str, object]]: ...

    def _group_sample_rows_by_project(
        self, sample_rows: list[dict[str, object]]
    ) -> dict[str, list[dict[str, object]]]: ...

    def _build_project_truth_row(
        self,
        *,
        species_latin_name: str,
        species_common_name: str,
        project_accession: str,
        sample_rows: list[dict[str, object]],
        locality_rows: list[dict[str, object]],
    ) -> dict[str, object]: ...

    def _build_species_truth_row(
        self,
        *,
        species_latin_name: str,
        species_common_name: str,
        species_root: Path,
        sample_rows: list[dict[str, object]],
        project_rows: list[dict[str, object]],
    ) -> dict[str, object]: ...

    def _sample_backed_site_count(
        self, sample_rows: list[dict[str, object]]
    ) -> int: ...

    def _readme_curated_sample_count(self, path: Path) -> int | None: ...

    def build_animal_sample_foundation_truth(
        self, data_root: Path
    ) -> dict[str, object]: ...

    def build_project_locality_count_drift(
        self, data_root: Path
    ) -> tuple[dict[str, object], ...]: ...

    def build_species_sample_count_drift(
        self, data_root: Path
    ) -> tuple[dict[str, object], ...]: ...
