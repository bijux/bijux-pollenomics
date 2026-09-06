"""Stable facade for animal sample-foundation truth."""

# Compatibility attributes intentionally remain at this import path.
# ruff: noqa: F401

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import cast

from bijux_pollenomics.adna.workflow.paths import adna_species_root

from ....species.definitions import resolve_species_definition
from ....species.tracked_species import TRACKED_ADNA_SPECIES
from .classification import (
    build_project_truth_row,
    build_species_truth_row,
    has_any_linkage,
    sample_backed_site_count,
    sample_truth_status,
    status_counts,
)
from .dependencies import SampleTruthDependencies
from .drift import (
    build_project_locality_count_drift as _build_project_drift,
)
from .drift import (
    build_species_sample_count_drift as _build_species_drift,
)
from .foundation import build_animal_sample_foundation_truth as _build_foundation_truth
from .markdown import (
    render_animal_sample_aggregation_warnings_markdown as _render_warnings_markdown,
)
from .markdown import (
    render_animal_sample_foundation_truth_markdown as _render_truth_markdown,
)
from .markdown import (
    render_animal_sample_product_contract_markdown as _render_contract_markdown,
)
from .product_contract import build_animal_sample_product_contract as _build_contract
from .repository import (
    group_sample_rows_by_project,
    load_rows,
    readme_curated_sample_count,
)
from .warnings import build_animal_sample_aggregation_warnings as _build_warnings

__all__ = [
    "build_animal_sample_aggregation_warnings",
    "build_animal_sample_foundation_truth",
    "build_animal_sample_product_contract",
    "build_project_locality_count_drift",
    "build_species_sample_count_drift",
    "render_animal_sample_aggregation_warnings_markdown",
    "render_animal_sample_foundation_truth_markdown",
    "render_animal_sample_product_contract_markdown",
]

_SPECIES_SAMPLE_COUNT_RE = re.compile(r"- Curated sample rows: `(?P<count>\d+)`")


def build_animal_sample_product_contract() -> dict[str, object]:
    """Describe the minimum durable contract for non-human animal aDNA sample rows."""
    return _build_contract()


def build_animal_sample_foundation_truth(data_root: Path) -> dict[str, object]:
    """Count sample-foundation truth classes across species and projects."""
    return _build_foundation_truth(data_root, dependencies=_dependencies())


def build_project_locality_count_drift(
    data_root: Path,
) -> tuple[dict[str, object], ...]:
    """Compare project locality summaries against sample-backed site counts."""
    return _build_project_drift(data_root, dependencies=_dependencies())


def build_species_sample_count_drift(data_root: Path) -> tuple[dict[str, object], ...]:
    """Compare species README sample claims against current sample-master counts."""
    return _build_species_drift(data_root, dependencies=_dependencies())


def build_animal_sample_aggregation_warnings(
    data_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Count current outputs that still rely on project- or site-level aggregation."""
    return _build_warnings(data_root, report_root, dependencies=_dependencies())


def render_animal_sample_product_contract_markdown(payload: dict[str, object]) -> str:
    return _render_contract_markdown(payload)


def render_animal_sample_foundation_truth_markdown(payload: dict[str, object]) -> str:
    return _render_truth_markdown(payload)


def render_animal_sample_aggregation_warnings_markdown(
    payload: dict[str, object],
) -> str:
    return _render_warnings_markdown(payload)


def _build_project_truth_row(
    *,
    species_latin_name: str,
    species_common_name: str,
    project_accession: str,
    sample_rows: list[dict[str, object]],
    locality_rows: list[dict[str, object]],
) -> dict[str, object]:
    return build_project_truth_row(
        species_latin_name=species_latin_name,
        species_common_name=species_common_name,
        project_accession=project_accession,
        sample_rows=sample_rows,
        locality_rows=locality_rows,
        status_counter=_status_counts,
        site_counter=_sample_backed_site_count,
    )


def _build_species_truth_row(
    *,
    species_latin_name: str,
    species_common_name: str,
    species_root: Path,
    sample_rows: list[dict[str, object]],
    project_rows: list[dict[str, object]],
) -> dict[str, object]:
    return build_species_truth_row(
        species_latin_name=species_latin_name,
        species_common_name=species_common_name,
        species_root=species_root,
        sample_rows=sample_rows,
        project_rows=project_rows,
        status_counter=_status_counts,
        readme_counter=_readme_curated_sample_count,
    )


def _status_counts(sample_rows: list[dict[str, object]]) -> dict[str, int]:
    return status_counts(sample_rows, _sample_truth_status)


def _sample_truth_status(sample_row: dict[str, object]) -> str:
    return sample_truth_status(sample_row)


def _has_any_linkage(sample_row: dict[str, object]) -> bool:
    return has_any_linkage(sample_row)


def _sample_backed_site_count(sample_rows: list[dict[str, object]]) -> int:
    return sample_backed_site_count(sample_rows)


def _readme_curated_sample_count(path: Path) -> int | None:
    return readme_curated_sample_count(path, _SPECIES_SAMPLE_COUNT_RE)


def _group_sample_rows_by_project(
    sample_rows: list[dict[str, object]],
) -> dict[str, list[dict[str, object]]]:
    return group_sample_rows_by_project(sample_rows)


def _load_all_sample_rows(data_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for species_name in TRACKED_ADNA_SPECIES:
        rows.extend(_load_sample_rows(_species_root(data_root, species_name)))
    return rows


def _load_all_locality_rows(data_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for species_name in TRACKED_ADNA_SPECIES:
        rows.extend(_load_locality_rows(_species_root(data_root, species_name)))
    return rows


def _load_sample_rows(species_root: Path) -> list[dict[str, object]]:
    return load_rows(species_root, "sample_records.json", "samples")


def _load_locality_rows(species_root: Path) -> list[dict[str, object]]:
    return load_rows(species_root, "locality_summaries.json", "localities")


def _species_root(data_root: Path, species_name: str) -> Path:
    return adna_species_root(Path(data_root), species_name)


def _dependencies() -> SampleTruthDependencies:
    return cast(SampleTruthDependencies, sys.modules[__name__])
