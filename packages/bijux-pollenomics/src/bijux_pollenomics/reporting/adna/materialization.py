"""Materialize publication-owned animal aDNA artifacts."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.adna.governance.audit_catalogs import (
    build_animal_atlas_candidate_accountability,
    render_animal_atlas_candidate_accountability_markdown,
)
from bijux_pollenomics.adna.workflow.paths import adna_final_root
from bijux_pollenomics.core.files import write_json, write_text
from bijux_pollenomics.core.records import require_record_rows
from bijux_pollenomics.core.tabular import render_csv_rows

from .atlas_evidence_rows import build_tracked_animal_atlas_evidence_rows
from .country_outputs import build_country_animal_output_bundle


def materialize_animal_publication_artifacts(data_root: Path) -> None:
    """Write final atlas and country indexes from normalized animal evidence."""
    final_root = adna_final_root(data_root)
    atlas_root = final_root / "atlas"
    countries_root = final_root / "countries"
    atlas_root.mkdir(parents=True, exist_ok=True)
    countries_root.mkdir(parents=True, exist_ok=True)

    atlas_rows = tuple(
        row.as_dict() for row in build_tracked_animal_atlas_evidence_rows(data_root)
    )
    write_json(
        atlas_root / "animal_atlas_point_candidates.json",
        {
            "schema_version": "animal-atlas-point-candidates.v1",
            "row_count": len(atlas_rows),
            "rows": list(atlas_rows),
        },
    )
    write_text(
        atlas_root / "animal_atlas_point_candidates.csv",
        render_csv_rows(atlas_rows),
    )

    accountability = build_animal_atlas_candidate_accountability(data_root)
    write_json(
        atlas_root / "animal_atlas_candidate_accountability.json",
        accountability,
    )
    write_text(
        atlas_root / "animal_atlas_candidate_accountability.md",
        render_animal_atlas_candidate_accountability_markdown(accountability),
    )
    accountability_rows = require_record_rows(accountability, "rows")
    if accountability_rows:
        write_text(
            atlas_root / "animal_atlas_candidate_accountability.csv",
            render_csv_rows(accountability_rows),
        )

    country_rows: list[dict[str, object]] = []
    for country in ("Sweden", "Norway", "Finland", "Denmark"):
        bundle = build_country_animal_output_bundle(
            data_root=data_root,
            country=country,
            version="v66",
            generated_on="checked_data_root",
        )
        country_rows.append(
            {
                "country": country,
                "sample_row_count": len(bundle.sample_rows),
                "species_count": len(bundle.species_rows),
                "locality_count": len(bundle.localities),
                "citation_count": len(bundle.citations),
                "warning_count": len(bundle.warnings),
            }
        )
    write_json(
        countries_root / "country_publication_index.json",
        {
            "schema_version": "animal-country-publication-index.v1",
            "rows": country_rows,
        },
    )
    write_text(
        countries_root / "country_publication_index.csv",
        render_csv_rows(tuple(country_rows)),
    )
