from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from bijux_pollenomics.adna.domain.models.vocabularies import (
    ADNA_APPROXIMATE_COORDINATE_CONFIDENCE,
)

from ...models import CountryReport


def _load_country_payloads(
    country_reports: tuple[CountryReport, ...],
    country_output_dirs: tuple[Path, ...],
) -> list[dict[str, object]]:
    by_dir = {path.name: path for path in country_output_dirs}
    payloads: list[dict[str, object]] = []
    for report in country_reports:
        country_dir = by_dir.get(report.output_dir.name)
        if country_dir is None:
            continue
        summary_path = (
            country_dir
            / f"{country_dir.name}_animal_adna_{report.version}_summary.json"
        )
        if not summary_path.is_file():
            continue
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payloads.append(payload)
    return payloads


def _build_country_species_coverage(
    country_payloads: list[dict[str, object]],
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for payload in country_payloads:
        sample_rows = payload.get("sample_rows", [])
        if not isinstance(sample_rows, list):
            sample_rows = []
        sample_counts: dict[str, int] = {}
        direct_counts: dict[str, int] = {}
        geocoded_counts: dict[str, int] = {}
        unresolved_counts: dict[str, int] = {}
        sample_lineage_counts: dict[str, int] = {}
        site_evidence_counts: dict[str, int] = {}
        chronology_provenance_counts: dict[str, int] = {}
        coordinate_provenance_counts: dict[str, int] = {}
        exact_coordinate_counts: dict[str, int] = {}
        approximate_coordinate_counts: dict[str, int] = {}
        for sample_row in sample_rows:
            if not isinstance(sample_row, dict):
                continue
            species_name = str(sample_row.get("species_latin_name", ""))
            if not species_name:
                continue
            sample_counts[species_name] = sample_counts.get(species_name, 0) + 1
            if str(sample_row.get("sample_lineage_path", "")).strip():
                sample_lineage_counts[species_name] = (
                    sample_lineage_counts.get(species_name, 0) + 1
                )
            if str(sample_row.get("site_evidence_path", "")).strip():
                site_evidence_counts[species_name] = (
                    site_evidence_counts.get(species_name, 0) + 1
                )
            if str(sample_row.get("chronology_provenance_path", "")).strip():
                chronology_provenance_counts[species_name] = (
                    chronology_provenance_counts.get(species_name, 0) + 1
                )
            if str(sample_row.get("coordinate_provenance_path", "")).strip():
                coordinate_provenance_counts[species_name] = (
                    coordinate_provenance_counts.get(species_name, 0) + 1
                )
            coordinate_basis = str(sample_row.get("coordinate_basis", ""))
            if coordinate_basis in {
                "direct_published_coordinates",
                "supplementary_proximal_site_coordinates",
                "supplementary_table_coordinates",
                "archive_coordinates",
            }:
                direct_counts[species_name] = direct_counts.get(species_name, 0) + 1
            if coordinate_basis in {"named_site_geocoding", "named_site_geocoded"}:
                geocoded_counts[species_name] = geocoded_counts.get(species_name, 0) + 1
            coordinate_confidence = str(sample_row.get("coordinate_confidence", ""))
            if coordinate_confidence == "exact":
                exact_coordinate_counts[species_name] = (
                    exact_coordinate_counts.get(species_name, 0) + 1
                )
            if coordinate_confidence in ADNA_APPROXIMATE_COORDINATE_CONFIDENCE:
                approximate_coordinate_counts[species_name] = (
                    approximate_coordinate_counts.get(species_name, 0) + 1
                )
            if str(sample_row.get("inclusion_status", "")) == "sample_context_blocked":
                unresolved_counts[species_name] = (
                    unresolved_counts.get(species_name, 0) + 1
                )
        for row in cast(list[object], payload.get("species_rows", [])):
            if not isinstance(row, dict):
                continue
            species_name = str(row.get("species_latin_name", ""))
            rows.append(
                {
                    **row,
                    "sample_row_count": sample_counts.get(species_name, 0),
                    "direct_coordinate_site_count": direct_counts.get(species_name, 0),
                    "geocoded_site_count": geocoded_counts.get(species_name, 0),
                    "unresolved_sample_count": unresolved_counts.get(species_name, 0),
                    "sample_lineage_backed_sample_count": sample_lineage_counts.get(
                        species_name, 0
                    ),
                    "site_evidence_backed_sample_count": site_evidence_counts.get(
                        species_name, 0
                    ),
                    "chronology_provenance_backed_sample_count": (
                        chronology_provenance_counts.get(species_name, 0)
                    ),
                    "coordinate_provenance_backed_sample_count": (
                        coordinate_provenance_counts.get(species_name, 0)
                    ),
                    "exact_coordinate_sample_count": exact_coordinate_counts.get(
                        species_name, 0
                    ),
                    "approximate_coordinate_sample_count": (
                        approximate_coordinate_counts.get(species_name, 0)
                    ),
                }
            )
    rows.sort(key=lambda row: (str(row["country"]), str(row["species_latin_name"])))
    return {
        "schema_version": "animal-country-species-coverage.v1",
        "rows": rows,
    }
