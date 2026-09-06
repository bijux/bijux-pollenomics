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
from bijux_pollenomics.reporting.adna.atlas_evidence_rows.source_records import (
    _load_project_animal_scope_lookup,
)
from bijux_pollenomics.reporting.adna.atlas_evidence_rows.validation import (
    _project_sample_animal_scope_for,
    _project_sample_animal_scope_resolution_for,
)

from tests.support.repository import REPOSITORY_ROOT


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


def test_missing_project_scope_artifact_fails_closed(tmp_path: Path) -> None:
    species_root = tmp_path / "bos_taurus"

    assert (
        _project_sample_animal_scope_for(
            species_root,
            None,
            project_accessions=("PRJEB75467",),
            sample_rows=(_sample(),),
        )
        is None
    )


def test_domesticated_project_classifies_source_native_wildcats_separately(
    tmp_path: Path,
) -> None:
    species_root = tmp_path / "felis_catus"
    _write_project_summaries(species_root)
    lookup = _load_project_animal_scope_lookup(species_root)

    assert lookup is not None
    assert (
        _project_sample_animal_scope_for(
            species_root,
            lookup,
            project_accessions=("PRJEB31621",),
            sample_rows=(
                _sample(
                    "PRJEB31621",
                    scientific_name="Felis silvestris silvestris",
                    alignment="project_species_mismatch",
                ),
            ),
        )
        == "wild_or_progenitor_context"
    )


def test_mixed_domestic_and_wild_samples_at_one_locality_fail_closed(
    tmp_path: Path,
) -> None:
    species_root = tmp_path / "felis_catus"
    _write_project_summaries(species_root)
    lookup = _load_project_animal_scope_lookup(species_root)

    assert lookup is not None
    assert (
        _project_sample_animal_scope_for(
            species_root,
            lookup,
            project_accessions=("PRJEB31621",),
            sample_rows=(
                _sample(
                    "PRJEB31621",
                    scientific_name="Felis catus",
                    alignment="project_species_match",
                ),
                _sample(
                    "PRJEB31621",
                    scientific_name="Felis silvestris silvestris",
                    alignment="project_species_mismatch",
                ),
            ),
        )
        is None
    )
    assert _project_sample_animal_scope_resolution_for(
        species_root,
        lookup,
        project_accessions=("PRJEB31621",),
        sample_rows=(
            _sample(
                "PRJEB31621",
                scientific_name="Felis catus",
                alignment="project_species_match",
            ),
            _sample(
                "PRJEB31621",
                scientific_name="Felis silvestris silvestris",
                alignment="project_species_mismatch",
            ),
        ),
    ) == (None, "mixed_sample_scope")


def test_source_native_pig_taxon_requires_accession_level_domestic_evidence(
    tmp_path: Path,
) -> None:
    species_root = tmp_path / "sus_scrofa_domesticus"
    _write_project_summaries(species_root)
    lookup = _load_project_animal_scope_lookup(species_root)

    assert lookup is not None
    asserted_domestic = _sample(
        "PRJEB30282",
        scientific_name="Sus scrofa",
        alignment="project_species_mismatch",
        archive_sample_id="SAMEA5160867",
    )
    lookup["PRJEB30282"] = lookup["PRJEB31621"]

    assert (
        _project_sample_animal_scope_for(
            species_root,
            lookup,
            project_accessions=("PRJEB30282",),
            sample_rows=(asserted_domestic,),
        )
        == "domesticated_core"
    )
    asserted_domestic["archive_native_sample_id"] = "SAMEA5160869"
    assert (
        _project_sample_animal_scope_for(
            species_root,
            lookup,
            project_accessions=("PRJEB30282",),
            sample_rows=(asserted_domestic,),
        )
        is None
    )


@pytest.mark.parametrize(
    ("species_slug", "project_accession", "evidence_text", "expected_scope"),
    [
        (
            "equus_caballus",
            "PRJEB31613",
            "Batagai_5155 | N/A | wild Archaic | 5155 BP",
            "wild_or_progenitor_context",
        ),
        (
            "equus_caballus",
            "PRJEB44430",
            "cave, Late Pleistocene, Infinite radiocarbon dating",
            "wild_or_progenitor_context",
        ),
        (
            "equus_caballus",
            "PRJEB44430",
            "sample | coordinates | Acemhoyuk | Turkey | DOM2 | Bronze Age",
            "domesticated_core",
        ),
        (
            "capra_hircus",
            "PRJEB90141",
            "Turkish Bezoar, Taurus Mountains",
            "wild_or_progenitor_context",
        ),
        (
            "capra_hircus",
            "PRJEB90141",
            "Bronze Age Central Turkish Domestic",
            "domesticated_core",
        ),
    ],
)
def test_heterogeneous_projects_require_source_sample_scope_evidence(
    tmp_path: Path,
    species_slug: str,
    project_accession: str,
    evidence_text: str,
    expected_scope: str,
) -> None:
    species_root = tmp_path / species_slug
    _write_project_summaries(species_root)
    lookup = _load_project_animal_scope_lookup(species_root)

    assert lookup is not None
    lookup[project_accession] = "domesticated_core"
    sample = _sample(project_accession)
    sample["sample_lineage_excerpt"] = evidence_text
    sample["taxon_alignment_status"] = "not_reported"
    assert (
        _project_sample_animal_scope_for(
            species_root,
            lookup,
            project_accessions=(project_accession,),
            sample_rows=(sample,),
        )
        == expected_scope
    )


def test_heterogeneous_project_without_sample_scope_evidence_fails_closed(
    tmp_path: Path,
) -> None:
    species_root = tmp_path / "equus_caballus"
    _write_project_summaries(species_root)
    lookup = _load_project_animal_scope_lookup(species_root)

    assert lookup is not None
    lookup["PRJEB31613"] = "domesticated_core"
    sample = _sample("PRJEB31613")
    sample["sample_lineage_excerpt"] = "Bronze Age"
    sample["taxon_alignment_status"] = "not_reported"
    assert (
        _project_sample_animal_scope_for(
            species_root,
            lookup,
            project_accessions=("PRJEB31613",),
            sample_rows=(sample,),
        )
        is None
    )
    assert _project_sample_animal_scope_resolution_for(
        species_root,
        lookup,
        project_accessions=("PRJEB31613",),
        sample_rows=(sample,),
    ) == (None, "sample_scope_not_evidenced")


def test_tracked_atlas_never_labels_source_native_mismatches_as_domesticated() -> None:
    rows = service.build_tracked_animal_atlas_evidence_rows(REPOSITORY_ROOT / "data")
    domestic_rows = tuple(
        row for row in rows if row.animal_scope == "domesticated_core"
    )
    wildcat_rows = tuple(
        row
        for row in rows
        if any(
            name.startswith("Felis silvestris")
            for name in row.source_native_scientific_names
        )
    )

    assert domestic_rows
    assert not any(
        any(
            name
            in {
                "Bos primigenius",
                "Felis silvestris lybica",
                "Felis silvestris silvestris",
            }
            for name in row.source_native_scientific_names
        )
        for row in domestic_rows
    )
    assert len(wildcat_rows) == 15
    assert all(row.animal_scope == "wild_or_progenitor_context" for row in wildcat_rows)
    assert not any("bernhardsthal" in row.site_record_id for row in rows)
    pig_rows = tuple(
        row for row in rows if row.species_latin_name == "Sus scrofa domesticus"
    )
    assert len(pig_rows) == 2
    assert all(row.animal_scope == "domesticated_core" for row in pig_rows)
    wild_markers = (
        "bezoar",
        "palaeolithic",
        "paleolithic",
        "pleistocene",
        "wild archaic",
    )
    assert not any(
        any(marker in row.exact_source_text.casefold() for marker in wild_markers)
        for row in domestic_rows
    )


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
