"""Fail-closed governed repository and exact-join tests."""

from __future__ import annotations

from copy import deepcopy
from collections import Counter
import json
from pathlib import Path

import pytest

from bijux_pollenomics.reporting.adna.sample_chronology_context.repository import (
    load_animal_sample_chronology_corpus,
)

from .support import PROJECT, base_rows, write_source_repository


def test_minimal_exact_join_preserves_source_chronology_and_identity(
    tmp_path: Path,
) -> None:
    write_source_repository(tmp_path)
    corpus = load_animal_sample_chronology_corpus(tmp_path)

    assert len(corpus.nodes) == 1
    node = corpus.nodes[0]
    assert node.feature_id == "animal-source-chronology:PRJTEST1:prjtest1:sample1"
    assert (node.younger_bp, node.mean_bp, node.older_bp) == (1000, 1100, 1200)
    assert node.chronology_text == "1000-1200 BP"
    assert node.chronology_provenance_locator == "Sheet1!A2"
    assert node.source_native_taxonomy_status == "available"
    assert dict(corpus.source_counts) == {
        "project_count": 1,
        "sample_master_row_count": 1,
        "sample_chronology_row_count": 1,
        "sample_site_row_count": 1,
        "admitted_node_count": 1,
        "refused_master_row_count": 0,
    }
    assert corpus.input_identity.as_dict()["artifact_count"] == 4


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("schema", "sample_chronology.json schema mismatch"),
        ("duplicate", "duplicate sample_master.json sample identity"),
        ("missing_companion", "biological sample master identities"),
        ("cross_identity", "cross-surface preferred_sample_label mismatch"),
        ("boolean_bp", "normalized chronology requires integer BP"),
        ("floating_bp", "normalized chronology requires integer BP"),
        ("inverted_bp", "invalid canonical BP interval"),
        ("invalid_coordinate", "mappable latitude is outside WGS84 bounds"),
    ],
)
def test_structural_tampering_fails_closed(
    tmp_path: Path, mutation: str, message: str
) -> None:
    master, chronology, site = (deepcopy(row) for row in base_rows())
    schemas: dict[str, str] = {}
    masters = [master]
    chronologies = [chronology]
    sites = [site]
    if mutation == "schema":
        schemas["sample_chronology.json"] = "foreign.v1"
    elif mutation == "duplicate":
        masters.append(deepcopy(master))
    elif mutation == "missing_companion":
        chronologies.clear()
        sites.clear()
    elif mutation == "cross_identity":
        chronology["preferred_sample_label"] = "different"
    elif mutation == "boolean_bp":
        chronology["time_start_bp"] = True
    elif mutation == "floating_bp":
        chronology["time_start_bp"] = 1000.0
    elif mutation == "inverted_bp":
        chronology["time_start_bp"] = 1300
    elif mutation == "invalid_coordinate":
        master["latitude_text"] = "91"
    write_source_repository(
        tmp_path,
        masters=masters,
        chronologies=chronologies,
        sites=sites,
        schema_overrides=schemas,
    )

    with pytest.raises(ValueError, match=message):
        load_animal_sample_chronology_corpus(tmp_path)


@pytest.mark.parametrize(
    ("surface", "field"),
    (
        ("master", "sample_evidence_status"),
        ("master", "source_native_identity_kind"),
        ("chronology", "sample_evidence_status"),
        ("chronology", "chronology_strength"),
        ("chronology", "chronology_evidence_class"),
        ("chronology", "chronology_precision_posture"),
        ("chronology", "chronology_normalization_status"),
        ("chronology", "dating_basis"),
        ("site", "coordinate_basis"),
        ("site", "coordinate_confidence"),
        ("site", "locality_resolution_status"),
    ),
)
def test_controlled_source_vocabulary_tampering_fails_closed(
    tmp_path: Path, surface: str, field: str
) -> None:
    master, chronology, site = (deepcopy(row) for row in base_rows())
    rows = {"master": master, "chronology": chronology, "site": site}
    rows[surface][field] = "fabricated_scientific_value"
    write_source_repository(
        tmp_path,
        masters=[master],
        chronologies=[chronology],
        sites=[site],
    )

    with pytest.raises(ValueError, match=rf"unsupported {field}"):
        load_animal_sample_chronology_corpus(tmp_path)


def test_missing_source_native_identity_kind_fails_closed(tmp_path: Path) -> None:
    master, chronology, site = (deepcopy(row) for row in base_rows())
    master.pop("source_native_identity_kind")
    write_source_repository(
        tmp_path,
        masters=[master],
        chronologies=[chronology],
        sites=[site],
    )

    with pytest.raises(ValueError, match="source_native_identity_kind must be nonempty"):
        load_animal_sample_chronology_corpus(tmp_path)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        (
            "chronology_precision_posture",
            "unresolved",
            "numeric chronology has incompatible precision",
        ),
        (
            "chronology_precision_posture",
            "broad_period_only",
            "numeric chronology has incompatible precision",
        ),
        (
            "chronology_normalization_status",
            "normalized_point",
            "normalized point chronology is not a point",
        ),
    ),
)
def test_numeric_chronology_rejects_incompatible_controlled_combinations(
    tmp_path: Path, field: str, value: str, message: str
) -> None:
    master, chronology, site = (deepcopy(row) for row in base_rows())
    chronology[field] = value
    write_source_repository(
        tmp_path,
        masters=[master],
        chronologies=[chronology],
        sites=[site],
    )

    with pytest.raises(ValueError, match=message):
        load_animal_sample_chronology_corpus(tmp_path)


@pytest.mark.parametrize(
    ("status", "precision", "message"),
    (
        (
            "normalized_point",
            "sample_precise_interval",
            "normalized point has interval precision",
        ),
        (
            "normalized_interval",
            "sample_precise_point",
            "normalized interval has point precision",
        ),
    ),
)
def test_precise_chronology_posture_matches_normalization_shape(
    tmp_path: Path, status: str, precision: str, message: str
) -> None:
    master, chronology, site = (deepcopy(row) for row in base_rows())
    chronology["chronology_normalization_status"] = status
    chronology["chronology_precision_posture"] = precision
    if status == "normalized_point":
        chronology["time_start_bp"] = 1100
        chronology["time_end_bp"] = 1100
    write_source_repository(
        tmp_path,
        masters=[master],
        chronologies=[chronology],
        sites=[site],
    )

    with pytest.raises(ValueError, match=message):
        load_animal_sample_chronology_corpus(tmp_path)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        (
            "coordinate_basis",
            "unresolved_location_state",
            "mappable coordinate has incompatible basis",
        ),
        (
            "coordinate_basis",
            "region_centroid_fallback",
            "mappable coordinate has incompatible basis",
        ),
        (
            "coordinate_confidence",
            "withheld",
            "mappable coordinate has incompatible confidence",
        ),
        (
            "coordinate_confidence",
            "unknown",
            "mappable coordinate has incompatible confidence",
        ),
    ),
)
def test_mappable_coordinates_reject_nonlocating_controlled_values(
    tmp_path: Path, field: str, value: str, message: str
) -> None:
    master, chronology, site = (deepcopy(row) for row in base_rows())
    site[field] = value
    write_source_repository(
        tmp_path,
        masters=[master],
        chronologies=[chronology],
        sites=[site],
    )

    with pytest.raises(ValueError, match=message):
        load_animal_sample_chronology_corpus(tmp_path)


def test_valid_content_change_changes_path_and_byte_identity(tmp_path: Path) -> None:
    write_source_repository(tmp_path)
    before = load_animal_sample_chronology_corpus(tmp_path).input_identity
    registry_path = (
        tmp_path / "adna" / "governance" / "source_library" / "project_registry.json"
    )
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["rows"][0]["primary_paper_url"] = "https://doi.org/10.1000/changed"
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    after = load_animal_sample_chronology_corpus(tmp_path).input_identity

    assert before.combined_sha256 != after.combined_sha256
    assert before.artifacts[0].logical_path == after.artifacts[0].logical_path
    assert before.artifacts[0].sha256 != after.artifacts[0].sha256


def test_parsed_rows_and_input_identity_use_the_same_captured_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_source_repository(tmp_path)
    baseline = load_animal_sample_chronology_corpus(tmp_path)
    chronology_path = (
        tmp_path
        / "adna"
        / "governance"
        / "source_library"
        / "projects"
        / PROJECT
        / "sample_chronology.json"
    )
    changed = json.loads(chronology_path.read_text(encoding="utf-8"))
    changed["rows"][0].update(
        {
            "chronology_text": "2000-2200 BP",
            "time_start_bp": 2000,
            "time_end_bp": 2200,
            "time_mean_bp": 2100,
        }
    )
    changed_bytes = json.dumps(changed, indent=2).encode("utf-8")
    original_read_bytes = Path.read_bytes
    reads: Counter[Path] = Counter()

    def mutate_after_read(path: Path) -> bytes:
        content = original_read_bytes(path)
        reads[path] += 1
        if path == chronology_path and reads[path] == 1:
            path.write_bytes(changed_bytes)
        return content

    monkeypatch.setattr(Path, "read_bytes", mutate_after_read)
    raced = load_animal_sample_chronology_corpus(tmp_path)

    assert reads[chronology_path] == 1
    assert (raced.nodes[0].younger_bp, raced.nodes[0].older_bp) == (1000, 1200)
    assert raced.input_identity == baseline.input_identity
    assert chronology_path.read_bytes() == changed_bytes


def test_boolean_declared_count_fails_closed(tmp_path: Path) -> None:
    write_source_repository(tmp_path)
    master_path = (
        tmp_path
        / "adna"
        / "governance"
        / "source_library"
        / "projects"
        / PROJECT
        / "sample_master.json"
    )
    payload = json.loads(master_path.read_text(encoding="utf-8"))
    payload["recovered_sample_count"] = True
    master_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with pytest.raises(ValueError, match="master recovered mismatch"):
        load_animal_sample_chronology_corpus(tmp_path)


def test_symlinked_project_directory_fails_closed(tmp_path: Path) -> None:
    write_source_repository(tmp_path)
    project_root = tmp_path / "adna" / "governance" / "source_library" / "projects"
    project_path = project_root / PROJECT
    target = tmp_path / "project-source"
    project_path.rename(target)
    project_path.symlink_to(target, target_is_directory=True)

    with pytest.raises(ValueError, match="project inventory does not reconcile"):
        load_animal_sample_chronology_corpus(tmp_path)


def test_exclusive_refusals_do_not_leak_lower_priority_reasons(tmp_path: Path) -> None:
    masters: list[dict[str, object]] = []
    chronologies: list[dict[str, object]] = []
    sites: list[dict[str, object]] = []
    for suffix in (
        "nonfinal",
        "chronology",
        "coordinate",
        "sampleprov",
        "chronprov",
        "siteprov",
    ):
        master, chronology, site = (deepcopy(row) for row in base_rows(f"x:{suffix}"))
        if suffix == "nonfinal":
            for row in (master, chronology, site):
                row["sample_identity_resolution"] = "ambiguous"
                row["sample_ambiguity_note"] = "identity conflict"
            chronology["chronology_normalization_status"] = "unresolved"
            chronology["time_start_bp"] = None
            chronology["time_end_bp"] = None
            chronology["time_mean_bp"] = None
        elif suffix == "chronology":
            chronology["chronology_normalization_status"] = "unresolved"
            chronology["time_start_bp"] = None
            chronology["time_end_bp"] = None
            chronology["time_mean_bp"] = None
        elif suffix == "coordinate":
            site["coordinate_mapping_posture"] = ""
            site["coordinate_basis"] = ""
            site["coordinate_confidence"] = ""
        elif suffix == "sampleprov":
            master["sample_lineage_path"] = ""
        elif suffix == "chronprov":
            chronology["chronology_provenance_path"] = ""
        elif suffix == "siteprov":
            site["location_evidence_artifact_path"] = ""
        masters.append(master)
        chronologies.append(chronology)
        sites.append(site)
    experiment, _chronology, _site = (
        deepcopy(row) for row in base_rows("x:experiment")
    )
    experiment["sample_identity_resolution"] = "provisional"
    experiment["source_native_identity_kind"] = "sequencing_experiment_accession"
    masters.append(experiment)
    write_source_repository(
        tmp_path,
        masters=masters,
        chronologies=chronologies,
        sites=sites,
    )

    corpus = load_animal_sample_chronology_corpus(tmp_path)

    assert len(corpus.nodes) == 0
    assert dict(corpus.refusal_counts) == {
        "sequencing_experiment_identity": 1,
        "sample_identity_not_final": 1,
        "source_chronology_not_comparable": 1,
        "source_coordinate_not_mappable": 1,
        "sample_provenance_unavailable": 1,
        "chronology_provenance_unavailable": 1,
        "site_provenance_unavailable": 1,
    }
    assert len({row.repo_stable_sample_id for row in corpus.refusals}) == 7


@pytest.mark.parametrize(
    ("posture", "basis", "confidence"),
    [
        ("refused_region_only", "region_centroid_fallback", "approximate"),
        ("refused_unresolved_location", "unresolved_location_state", "unknown"),
    ],
)
def test_explicit_coordinate_refusal_postures_reach_the_refusal_ledger(
    tmp_path: Path,
    posture: str,
    basis: str,
    confidence: str,
) -> None:
    master, chronology, site = (deepcopy(row) for row in base_rows())
    master["latitude_text"] = ""
    master["longitude_text"] = ""
    site["coordinate_mapping_posture"] = posture
    site["coordinate_basis"] = basis
    site["coordinate_confidence"] = confidence
    write_source_repository(
        tmp_path,
        masters=[master],
        chronologies=[chronology],
        sites=[site],
    )

    corpus = load_animal_sample_chronology_corpus(tmp_path)

    assert corpus.nodes == ()
    assert [(row.repo_stable_sample_id, row.reason_code) for row in corpus.refusals] == [
        ("prjtest1:sample1", "source_coordinate_not_mappable")
    ]


def test_symlinked_governed_input_is_refused(tmp_path: Path) -> None:
    write_source_repository(tmp_path)
    chronology_path = (
        tmp_path
        / "adna"
        / "governance"
        / "source_library"
        / "projects"
        / PROJECT
        / "sample_chronology.json"
    )
    target = tmp_path / "chronology-source.json"
    chronology_path.rename(target)
    chronology_path.symlink_to(target)

    with pytest.raises(ValueError, match="input is unavailable"):
        load_animal_sample_chronology_corpus(tmp_path)
