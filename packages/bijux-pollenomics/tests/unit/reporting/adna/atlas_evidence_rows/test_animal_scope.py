"""Project- and sample-owned animal-atlas scope tests."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from bijux_pollenomics.reporting.adna.atlas_evidence_rows import service
from bijux_pollenomics.reporting.adna.atlas_evidence_rows.source_records import (
    _load_project_animal_scope_lookup,
    _project_sample_animal_scope_for,
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


def _sample(project_accession: object = "PRJEB75467") -> dict[str, object]:
    return {
        "project_accession": project_accession,
        "source_native_scientific_name": "Bos primigenius",
    }


def test_wild_aurochs_project_does_not_inherit_species_domesticated_scope(
    tmp_path: Path,
) -> None:
    species_root = tmp_path / "bos_taurus"
    _write_project_summaries(species_root)
    lookup = _load_project_animal_scope_lookup(species_root)

    assert lookup is not None
    assert (
        _project_sample_animal_scope_for(
            species_root,
            lookup,
            project_accessions=("PRJEB75467",),
            sample_rows=(_sample(),),
        )
        == "wild_or_progenitor_context"
    )
    assert (
        _project_sample_animal_scope_for(
            species_root,
            lookup,
            project_accessions=("PRJEB31621",),
            sample_rows=(_sample("PRJEB31621"),),
        )
        == "domesticated_core"
    )


@pytest.mark.parametrize(
    ("project_accessions", "sample_rows"),
    [
        (("PRJEB75467", "PRJEB31621"), (_sample(),)),
        (("PRJEB75467",), (_sample("PRJEB31621"),)),
        (("PRJEB75467",), (_sample(None),)),
        (("UNKNOWN",), (_sample("UNKNOWN"),)),
        (("PRJEB75467",), ()),
    ],
)
def test_ambiguous_or_unowned_project_sample_scope_fails_closed(
    tmp_path: Path,
    project_accessions: tuple[str, ...],
    sample_rows: tuple[dict[str, object], ...],
) -> None:
    species_root = tmp_path / "bos_taurus"
    _write_project_summaries(species_root)
    lookup = _load_project_animal_scope_lookup(species_root)

    assert lookup is not None
    assert (
        _project_sample_animal_scope_for(
            species_root,
            lookup,
            project_accessions=project_accessions,
            sample_rows=sample_rows,
        )
        is None
    )


def test_duplicate_project_scope_records_fail_closed(tmp_path: Path) -> None:
    species_root = tmp_path / "bos_taurus"
    _write_project_summaries(species_root)
    path = species_root / "normalized" / "project_summaries.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["projects"].append(dict(payload["projects"][1]))
    path.write_text(json.dumps(payload), encoding="utf-8")

    lookup = _load_project_animal_scope_lookup(species_root)

    assert lookup is not None
    assert "PRJEB75467" not in lookup


def test_atlas_builder_propagates_the_matched_samples_project_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    species_root = tmp_path / "species" / "bos_taurus"
    _write_project_summaries(species_root)
    site_token = "bos_taurus:locality:prjeb75467:aurochs-site"
    locality = {
        "identity": {
            "stable_token": site_token,
            "locality_text": "Aurochs site",
        },
        "species_latin_name": "Bos taurus",
        "species_common_name": "cattle",
        "locality": "Aurochs site",
        "coordinates": {"latitude": 55.0, "longitude": 12.0},
        "chronology": {
            "original_text": "5000 BP",
            "time_start_bp": 5000,
            "time_end_bp": 5000,
            "time_mean_bp": 5000,
            "dating_basis": "archaeological_context",
            "evidence_class": "archaeological_context_date",
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

    rows = service.build_tracked_animal_atlas_evidence_rows(tmp_path)

    assert len(rows) == 1
    assert rows[0].primary_project_accession == "PRJEB75467"
    assert rows[0].source_native_scientific_names == ("Bos primigenius",)
    assert rows[0].animal_scope == "wild_or_progenitor_context"
