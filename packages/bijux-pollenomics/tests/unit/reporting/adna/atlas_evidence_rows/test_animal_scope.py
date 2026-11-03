"""Project- and sample-owned animal-atlas scope tests."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics.adna import AdnaChronology
from bijux_pollenomics.adna.domain.locality import locality_sample_intervals
from bijux_pollenomics.adna.domain.models.localities import AdnaSampleChronologySupport
from bijux_pollenomics.reporting.adna.atlas_evidence_rows import service
from bijux_pollenomics.reporting.adna.atlas_evidence_rows.localities import (
    _parse_locality_summary,
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
        "sample_ids": ["bos_taurus:sample:PRJEB75467:one"],
    }
    sample = {
        "identity": {"stable_token": "bos_taurus:sample:PRJEB75467:one"},
        "master_id": "bos_taurus:sample:PRJEB75467:one",
        "chronology": AdnaChronology(
            original_text="5000 BP",
            time_start_bp=5000,
            time_end_bp=5000,
            time_mean_bp=5000,
            dating_basis="archaeological_context",
            evidence_class="archaeological_context_date",
            precision_posture="sample_precise_point",
        ).as_dict(),
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
    assert len(rows[0].sample_chronologies) == 1
    support = rows[0].sample_chronologies[0]
    assert support.sample_id == sample["master_id"]
    assert support.chronology.time_start_bp == 5000
    assert support.chronology.time_end_bp == 5000


def _owned_locality(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, explicit: bool = True
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Use distinct dated children and an undated member with exact source metadata."""
    species_root = tmp_path / "species" / "bos_taurus"
    _write_project_summaries(species_root)
    site_token = "bos_taurus:locality:prjeb75467:aurochs-site"
    dated = AdnaChronology(
        "source interval",
        100,
        110,
        105,
        dating_basis="radiocarbon",
        evidence_class="direct_radiocarbon_date",
        precision_posture="sample_precise_interval",
    )
    chronologies = (
        dated,
        replace(dated, time_start_bp=300, time_end_bp=310, time_mean_bp=305),
        AdnaChronology("undated", None, None, None),
    )
    samples = [
        {
            "identity": {"stable_token": f"normalized:{index}"},
            "master_id": f"source:{index}",
            "chronology": chronology.as_dict(),
            "locality_identity": {"stable_token": site_token},
            "project_accession": "PRJEB75467",
            "source_native_scientific_name": "Bos primigenius",
            "inclusion_status": "site_curated",
            "source_release": "PRJEB75467",
            "chronology_provenance_path": "source-supplement.xlsx",
            "chronology_provenance_locator": f"Table S1!row{index + 2}",
            "chronology_provenance_text": f"literal source row {index}",
            "chronology_provenance_kind": "supplementary_spreadsheet_row",
            "chronology_strength": "source_owned",
            "chronology_normalization_status": "normalized_interval"
            if index < 2
            else "unresolved",
            "chronology_conflict_note": "retained source caution" if index == 1 else "",
            "reference_epoch": "source-explicit epoch",
            "age_type": "source age type",
            "calibration_status": "source calibration",
            "model": "source model",
        }
        for index, chronology in enumerate(chronologies)
    ]
    locality = {
        "identity": {"stable_token": site_token, "locality_text": "Aurochs site"},
        "species_latin_name": "Bos taurus",
        "species_common_name": "cattle",
        "locality": "Aurochs site",
        "coordinates": {"latitude": 55.0, "longitude": 12.0},
        "chronology": replace(dated, time_end_bp=310, time_mean_bp=205).as_dict(),
        "project_accessions": ["PRJEB75467"],
        "sample_count": 3,
        "sample_ids": [sample["master_id"] for sample in samples],
    }
    if explicit:
        locality["sample_chronologies"] = [
            AdnaSampleChronologySupport.from_sample_payload(sample).as_dict()
            for sample in samples
        ]
    key = ("PRJEB75467", "Aurochs site")
    monkeypatch.setattr(
        service,
        "build_species_support_matrix",
        lambda: (SimpleNamespace(latin_name="Bos taurus", slug="bos_taurus"),),
    )
    monkeypatch.setattr(service, "adna_species_dir", lambda _: tmp_path / "species")
    monkeypatch.setattr(service, "_load_locality_rows", lambda _: [locality])
    monkeypatch.setattr(service, "_load_sample_rows", lambda _: samples)
    monkeypatch.setattr(
        service,
        "_load_coordinate_provenance_lookup",
        lambda _: {
            key: {"mapping_posture": "mappable_point"},
        },
    )
    monkeypatch.setattr(
        service,
        "_load_site_evidence_lookup",
        lambda _: {
            key: {"source_support_status": "paper_pinned"},
        },
    )
    monkeypatch.setattr(service, "_load_citation_lookup", lambda _: {})
    monkeypatch.setattr(service, "_load_review_lookup", lambda _: {})
    return locality, samples


@pytest.mark.parametrize("explicit", [False, True])
def test_locality_admission_uses_complete_source_owned_children(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    explicit: bool,
) -> None:
    locality, samples = _owned_locality(tmp_path, monkeypatch, explicit=explicit)
    original = deepcopy((locality, samples))
    (row,) = service.build_tracked_animal_atlas_evidence_rows(tmp_path)
    assert row.animal_scope == "wild_or_progenitor_context"
    assert row.sample_ids == tuple(sample["master_id"] for sample in samples)
    assert row.sample_count == 3
    assert (row.latitude, row.longitude) == (55.0, 12.0)
    assert row.chronology == replace(
        AdnaChronology(**locality["chronology"]),
        dating_basis="locality_sample_coverage",
        evidence_class="locality_sample_coverage_hull",
        precision_posture="display_coverage_only",
    )
    assert row.sample_chronologies == tuple(
        AdnaSampleChronologySupport.from_sample_payload(sample) for sample in samples
    )
    assert row.sample_chronologies[-1].chronology.time_start_bp is None
    assert (locality, samples) == original


def test_display_hull_mutations_never_supply_occurrence_or_a_child_date(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    locality, samples = _owned_locality(tmp_path, monkeypatch)
    (first,) = service.build_tracked_animal_atlas_evidence_rows(tmp_path)
    for start, end in [(100, 310), (0, 100000)]:
        locality["chronology"].update(
            time_start_bp=start,
            time_end_bp=end,
            time_mean_bp=(start + end) // 2,
            dating_basis="locality_sample_coverage",
            evidence_class="locality_sample_coverage_hull",
            precision_posture="display_coverage_only",
        )
        (row,) = service.build_tracked_animal_atlas_evidence_rows(tmp_path)
        assert (row.feature_id, row.evidence_row_id, row.site_record_id) == (
            first.feature_id,
            first.evidence_row_id,
            first.site_record_id,
        )
        assert row.sample_chronologies == first.sample_chronologies
        parsed = _parse_locality_summary(locality)
        assert parsed.chronology.time_start_bp == start
        assert parsed.chronology.time_end_bp == end
        intervals = locality_sample_intervals(parsed)
        assert [
            (owner, (interval.younger_bp, interval.older_bp))
            for owner, interval in intervals
        ] == [
            (samples[0]["master_id"], (100, 110)),
            (samples[1]["master_id"], (300, 310)),
        ]
        assert not any(
            interval.younger_bp <= 200 <= interval.older_bp for _, interval in intervals
        )
        assert (
            row.chronology.as_temporal_semantics(source_family="animal_adna")[
                "comparability_posture"
            ]
            == "contextual_label_only"
        )


@pytest.mark.parametrize("state", ["undated", "refused", "contextual"])
def test_child_publication_policy_remains_authoritative(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    state: str,
) -> None:
    locality, samples = _owned_locality(tmp_path, monkeypatch, explicit=False)
    for sample in samples:
        chronology = AdnaChronology(**sample["chronology"])
        if state == "undated":
            chronology = AdnaChronology("undated", None, None, None)
        elif state == "refused":
            chronology = replace(
                chronology, refusal_reason_code="source_age_system_not_comparable"
            )
        else:
            chronology = replace(
                chronology,
                original_text="source archaeological period",
                dating_basis="archaeological_period",
                evidence_class="broad_period_label",
                precision_posture="broad_period_only",
            )
        sample["chronology"] = chronology.as_dict()
    rows = service.build_tracked_animal_atlas_evidence_rows(tmp_path)
    if state != "contextual":
        assert rows == ()
    else:
        assert len(rows) == 1
        locality["sample_chronologies"] = [
            support.as_dict() for support in rows[0].sample_chronologies
        ]
        assert locality_sample_intervals(_parse_locality_summary(locality)) == ()


def test_refused_child_and_aggregate_refusal_remain_literal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    locality, samples = _owned_locality(tmp_path, monkeypatch, explicit=False)
    samples[0]["chronology"]["refusal_reason_code"] = "source_age_system_not_comparable"
    locality["chronology"]["refusal_reason_code"] = "global_source_refusal"
    (row,) = service.build_tracked_animal_atlas_evidence_rows(tmp_path)
    assert row.chronology.refusal_reason_code == "global_source_refusal"
    assert (
        row.chronology.as_temporal_semantics(source_family="animal_adna")[
            "comparability_posture"
        ]
        == "refused"
    )
    assert (
        row.sample_chronologies[0].chronology.refusal_reason_code
        == "source_age_system_not_comparable"
    )
    assert (
        row.sample_chronologies[0].conflict_note
        == samples[0]["chronology_conflict_note"]
    )


@pytest.mark.parametrize(
    "tamper",
    [
        "missing_support",
        "duplicate_support",
        "swapped_dates",
        "foreign_support",
        "missing_declared_owner",
        "extra_declared_owner",
        "duplicate_declared_owner",
        "missing_source_owner",
        "duplicate_source_owner",
        "empty_supports",
        "null_supports",
        "boolean_endpoint",
        "altered_provenance",
        "altered_model",
    ],
)
def test_incomplete_or_malformed_ownership_never_becomes_hull_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tamper: str,
) -> None:
    locality, samples = _owned_locality(tmp_path, monkeypatch)
    supports = locality["sample_chronologies"]
    if tamper == "missing_support":
        supports.pop()
    elif tamper == "duplicate_support":
        supports[1] = deepcopy(supports[0])
    elif tamper == "swapped_dates":
        supports[0]["chronology"], supports[1]["chronology"] = (
            supports[1]["chronology"],
            supports[0]["chronology"],
        )
    elif tamper == "foreign_support":
        supports[0]["sample_id"] = "foreign"
    elif tamper == "missing_declared_owner":
        locality["sample_ids"].pop()
    elif tamper == "extra_declared_owner":
        locality["sample_ids"].append("foreign")
    elif tamper == "duplicate_declared_owner":
        locality["sample_ids"][1] = locality["sample_ids"][0]
    elif tamper == "missing_source_owner":
        samples.pop()
    elif tamper == "duplicate_source_owner":
        samples.append(deepcopy(samples[0]))
    elif tamper == "empty_supports":
        locality["sample_chronologies"] = []
    elif tamper == "null_supports":
        locality["sample_chronologies"] = None
    elif tamper == "boolean_endpoint":
        supports[0]["chronology"]["time_start_bp"] = True
    elif tamper == "altered_provenance":
        supports[0]["provenance_path"] = "unrelated.xlsx"
    else:
        supports[0]["model"] = "invented chronology model"
    with pytest.raises((ValueError, TypeError)):
        service.build_tracked_animal_atlas_evidence_rows(tmp_path)


def test_source_inclusion_and_coordinate_gates_are_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    locality, samples = _owned_locality(tmp_path, monkeypatch)
    locality["coordinates"]["latitude"] = None
    assert service.build_tracked_animal_atlas_evidence_rows(tmp_path) == ()
    locality["coordinates"]["latitude"] = 55.0
    for sample in samples:
        sample["inclusion_status"] = "not_admitted"
    assert service.build_tracked_animal_atlas_evidence_rows(tmp_path) == ()


@pytest.mark.parametrize("count", ["missing", True, "3", 2])
def test_locality_sample_count_requires_exact_integer_ownership(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    count: object,
) -> None:
    locality, samples = _owned_locality(tmp_path, monkeypatch)
    if type(count) is bool:
        del samples[1:]
        del locality["sample_ids"][1:]
        del locality["sample_chronologies"][1:]
    if count == "missing":
        locality.pop("sample_count")
    else:
        locality["sample_count"] = count
    with pytest.raises(ValueError, match="sample count"):
        service.build_tracked_animal_atlas_evidence_rows(tmp_path)
