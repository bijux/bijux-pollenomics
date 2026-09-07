"""Project- and sample-owned animal-atlas scope tests."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from bijux_pollenomics.reporting.adna.atlas_evidence_rows import service
from bijux_pollenomics.reporting.adna.atlas_evidence_rows import (
    source_records as source_records_module,
)


def _write_project_summaries(species_root: Path) -> None:
    path = species_root / "normalized" / "project_summaries.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "projects": [
                    {
                        "project_accession": "PRJEB31621",
                        "support_class": "domesticated_core_curated",
                        "domestication_scope": "domesticated_core",
                        "comparator_status": False,
                    },
                    {
                        "project_accession": "PRJEB75467",
                        "support_class": "wild_or_progenitor_context",
                        "domestication_scope": "wild_or_progenitor_context",
                        "comparator_status": False,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )


def _sample(
    project_accession: object = "PRJEB75467",
    *,
    scientific_name: str = "Bos primigenius",
    alignment: str = "",
    archive_sample_id: str = "",
) -> dict[str, object]:
    return {
        "project_accession": project_accession,
        "source_native_scientific_name": scientific_name,
        "taxon_alignment_status": alignment,
        "archive_native_sample_id": archive_sample_id,
    }


def test_atlas_builder_refuses_rows_when_project_scope_artifact_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    species_root = tmp_path / "species" / "bos_taurus"
    species_root.mkdir(parents=True)
    site_token = "bos_taurus:locality:prjeb75467:aurochs-site"
    locality = {
        "identity": {"stable_token": site_token, "locality_text": "Aurochs site"},
        "species_latin_name": "Bos taurus",
        "species_common_name": "cattle",
        "locality": "Aurochs site",
        "coordinates": {"latitude": 55.0, "longitude": 12.0},
        "chronology": {
            "original_text": "5000 BP",
            "time_start_bp": 5000,
            "time_end_bp": 5000,
            "time_mean_bp": 5000,
            "dating_basis": "radiocarbon",
            "evidence_class": "direct_radiocarbon_date",
            "precision_posture": "sample_precise_point",
        },
        "project_accessions": ["PRJEB75467"],
        "sample_count": 1,
    }
    sample = {
        "identity": {"stable_token": "bos_taurus:sample:PRJEB75467:one"},
        "locality_identity": {"stable_token": site_token},
        "project_accession": "PRJEB75467",
        "source_native_scientific_name": "Bos primigenius",
        "inclusion_status": "site_curated",
    }
    locality_key = ("PRJEB75467", "Aurochs site")
    monkeypatch.setattr(
        service,
        "build_species_support_matrix",
        lambda: (SimpleNamespace(latin_name="Bos taurus", slug="bos_taurus"),),
    )
    monkeypatch.setattr(service, "adna_species_dir", lambda _: tmp_path / "species")
    monkeypatch.setattr(service, "_load_locality_rows", lambda _: [locality])
    monkeypatch.setattr(service, "_load_sample_rows", lambda _: [sample])
    monkeypatch.setattr(
        service,
        "_load_coordinate_provenance_lookup",
        lambda _: {locality_key: {"mapping_posture": "mappable_point"}},
    )
    monkeypatch.setattr(
        service,
        "_load_site_evidence_lookup",
        lambda _: {locality_key: {"source_support_status": "paper_pinned"}},
    )
    monkeypatch.setattr(service, "_load_citation_lookup", lambda _: {})
    monkeypatch.setattr(service, "_load_review_lookup", lambda _: {})
    monkeypatch.setattr(
        source_records_module,
        "_animal_scope_for",
        lambda _: pytest.fail("species-level fallback must not run"),
    )
    assert service.build_tracked_animal_atlas_evidence_rows(tmp_path) == ()
