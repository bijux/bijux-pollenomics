"""Atlas evidence projection reconciliation and refusal tests."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import cast
import pytest
from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
)
from bijux_pollenomics.reporting.map_document.evidence_projection import (
    build_map_evidence_projection,
)
from .fixtures.common import _decode_dictionary_table, _decode_sead_claim_table
from .fixtures.neotoma import _neotoma_fixture
from tests.support.sead_evidence import (
    install_sead_projection_fixture,
    sead_projection_layers,
)


def test_projection_is_fixed_point_lossless_and_four_country_reconciled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.absolute()
    _neotoma_fixture(root, monkeypatch)
    install_sead_projection_fixture(root, monkeypatch)
    first_layers = sead_projection_layers()
    second_layers = sead_projection_layers()

    first = build_map_evidence_projection(root, first_layers)
    second = build_map_evidence_projection(root, second_layers)

    assert first == second
    assert first_layers == second_layers
    assert first.reconciliation["schema_version"] == "atlas-evidence-projection.v2"
    assert [str(row["record_id"]) for row in first.detail_records] == sorted(
        str(row["record_id"]) for row in first.detail_records
    )
    assert first.reconciliation["source_feature_count"] == 6
    assert first.reconciliation["detail_record_count"] == 5
    assert first.reconciliation["repeated_feature_reference_count"] == 1
    sources = cast(dict[str, object], first.reconciliation["sources"])
    neotoma = cast(dict[str, object], sources["neotoma"])
    assert cast(dict[str, int], neotoma["detail_row_counts"])["variables"] == 1
    sead = cast(dict[str, object], sources["sead"])
    assert sead["country_site_counts"] == {
        "Denmark": 1,
        "Finland": 1,
        "Norway": 1,
        "Sweden": 1,
    }
    assert sead["bbox_site_denominator"] == 4
    assert sead["assigned_site_count"] == 4
    assert sead["excluded_site_count"] == 0
    assert sead["source_claim_denominator"] == 1
    assert sead["source_observation_denominator"] == 2
    assert sead["source_taxon_relation_denominator"] == 1
    assert sead["source_dimension_relation_denominator"] == 1
    assert sead["source_event_refusal_denominator"] == 2
    assert sead["projected_site_observation_count"] == 2
    assert sead["projected_unique_taxon_relation_count"] == 1
    assert sead["projected_dimension_relation_count"] == 1
    assert sead["unprojected_dimension_relation_count"] == 0
    assert sead["eligible_event_count"] == 0
    assert sead["claim_country_counts"] == {"DK": 1}
    assert sead["observation_country_counts"] == {"DK": 2}
    assert sead["eligible_event_country_counts"] == {"DK": 0}
    assert sead["propagation_status"] == "refused"
    assert sead["propagation_reason_code"] == "source_classification_not_accepted"
    details = {str(row["record_id"]): row for row in first.detail_records}
    neotoma_tabs = cast(dict[str, object], details["neotoma:site:10"]["tabs"])
    samples = cast(dict[str, object], neotoma_tabs["samples"])
    sample_table = cast(dict[str, object], samples["samples"])
    assert sample_table["record_count"] == 1
    sample_row = dict(
        zip(
            cast(list[str], sample_table["fields"]),
            cast(list[list[object]], sample_table["records"])[0],
            strict=True,
        )
    )
    assert sample_row["source_analysis_unit_name"] == "12 cm"
    assert sample_row["source_depth"] == 12
    assert sample_row["source_thickness"] is None
    assert sample_row["source_sample_analysts"] == [{"contactid": 42}]
    chronology = cast(dict[str, object], neotoma_tabs["chronology"])
    assert chronology["interval_semantics"] == "[younger_bp, older_bp]"
    age_row = dict(
        zip(
            cast(list[str], chronology["fields"]),
            cast(list[list[object]], chronology["records"])[0],
            strict=True,
        )
    )
    assert age_row["source_age_younger"] is None
    assert age_row["source_age_older"] is None
    assert age_row["younger_bp"] == age_row["older_bp"] == 125.5
    age_prefixes = cast(dict[str, str], chronology["identifier_prefixes"])
    assert (
        age_prefixes["collection_unit_id"] + str(age_row["collection_unit_id"])
        == "neotoma:collection-unit:20"
    )
    assert age_prefixes["dataset_id"] + str(age_row["dataset_id"]) == (
        "neotoma:dataset:30"
    )
    assert age_row["provenance_record_id"] == "sha256:" + "s" * 64
    composition = cast(dict[str, object], neotoma_tabs["pollen_composition"])
    assert composition["record_count"] == 1
    assert composition["aggregation_posture"] == (
        "source rows retained without cross-unit summing"
    )
    observation_row = dict(
        zip(
            cast(list[str], composition["fields"]),
            cast(list[list[object]], composition["records"])[0],
            strict=True,
        )
    )
    assert observation_row["source_unit"] == "NISP"
    assert observation_row["source_denominator"] is None
    assert observation_row["denominator_status"] == "not_provided_by_source"
    assert observation_row["source_part_number"] == 1
    variable_table = cast(dict[str, object], composition["variables"])
    variable_row = dict(
        zip(
            cast(list[str], variable_table["fields"]),
            cast(list[list[object]], variable_table["records"])[0],
            strict=True,
        )
    )
    assert variable_row["source_reported_name"] == "Triticum"
    assert variable_row["source_taxon_id"] == 50
    assert cast(dict[str, object], neotoma_tabs["classification"]) == {
        "status": "unavailable",
        "reason_code": "accepted_scientific_classification_not_available",
    }
    sead_tabs = cast(dict[str, object], details["sead:site:2"]["tabs"])
    sead_chronology = cast(dict[str, object], sead_tabs["chronology"])
    assert sead_chronology["chronology_claim_count"] == 1
    assert sead_chronology["record_count"] == 1
    assert sead_chronology["encoding"] == "sead-chronology-claim-table.v1"
    decoded_claim = _decode_sead_claim_table(sead_chronology)[0]
    assert decoded_claim["chronology_claim_id"] == "sead:site-2:dating_range:9"
    assert decoded_claim["source_record_id"] == "9"
    assert decoded_claim["source_native_record_id"] == "9"
    assert decoded_claim["site_uuid"] == "site-2"
    assert decoded_claim["source_age_type"] == "AD"
    assert decoded_claim["source_age_unit"] == "calendar_year"
    assert decoded_claim["source_age_value"] == {
        "age_type": "AD",
        "age_type_description": "Anno Domini",
        "age_type_id": 1,
        "analysis_dating_range_id": 9,
        "analysis_entity_id": 90,
        "analysis_value_id": 91,
        "dataset_id": 30,
        "dating_uncertainty_id": None,
        "high_is_uncertain": False,
        "high_qualifier": "",
        "high_value": None,
        "low_is_uncertain": False,
        "low_qualifier": "",
        "low_value": 1850,
        "physical_sample_id": 21,
        "sample_group_id": 20,
        "time_end_bp": 100,
        "time_start_bp": 100,
        "uncertainty_description": "",
        "uncertainty_label": "",
    }
    assert decoded_claim["younger_bp"] == decoded_claim["older_bp"] == 100
    assert decoded_claim["original_interval_orientation"] == "point"
    assert decoded_claim["propagation_eligibility"] == "refused"
    assert decoded_claim["propagation_reason_codes"] == [
        "source_classification_not_accepted"
    ]
    assert decoded_claim["observation_link_status"] == "linked_at_analysis_entity"
    assert decoded_claim["observation_relation_id"] == "sead-analysis-entity:90"
    assert decoded_claim["linked_source_native_observation_count"] == 2
    assert decoded_claim["selection_rule_version"] == (
        "sead-retain-all-source-chronologies-v1"
    )
    assert decoded_claim["provenance_record_id"] == (
        "sead-acquisition-manifest:fixture"
    )
    source_relation_path = cast(
        list[dict[str, object]], decoded_claim["source_relation_path"]
    )
    assert source_relation_path[-1] == {
        "table": "tbl_analysis_dating_ranges",
        "key": "analysis_dating_range_id",
        "value": "9",
    }
    assert decoded_claim["source_payload_sha256"] == "e" * 64
    assert decoded_claim["build_id"] == "sha256:" + "c" * 64
    assert (
        decoded_claim["acquisition_manifest_sha256"]
        == hashlib.sha256(b'{"status":"complete"}\n').hexdigest()
    )
    assert (
        cast(dict[str, object], sead_tabs["provenance"])["acquisition_release_status"]
        == "refused"
    )
    sead_composition = cast(dict[str, object], sead_tabs["pollen_composition"])
    assert sead_composition["record_count"] == 2
    assert sead_composition["encoding"] == "sead-source-native-observation-table.v1"
    observation_rows = _decode_dictionary_table(sead_composition)
    values_by_id = {
        cast(str, row["observation_id"]): (
            row["source_value"],
            row["source_value_state"],
        )
        for row in observation_rows
    }
    assert values_by_id == {
        "sead-observation:null": (None, "source_null"),
        "sead-observation:zero": (0, "reported"),
    }
    zero = next(
        row
        for row in observation_rows
        if row["observation_id"] == "sead-observation:zero"
    )
    assert zero["analysis_entity_id"] == 90
    assert zero["physical_sample_id"] == 21
    assert zero["sample_group_id"] == 20
    assert zero["dataset_id"] == 30
    assert zero["taxon_relation_id"] == "sead-taxon:5"
    assert zero["dimension_relation_ids"] == ["sead-dimension-relation:fixture"]
    assert "source_classification_not_accepted" in cast(
        list[str], zero["event_refusal_reason_codes"]
    )
    taxa = cast(dict[str, object], sead_composition["taxa"])
    taxon_row = dict(
        zip(
            cast(list[str], taxa["fields"]),
            cast(list[list[object]], taxa["records"])[0],
            strict=True,
        )
    )
    assert taxon_row["genus_name"] == "Triticum"
    assert taxon_row["source_ecocodes"] == [
        {
            "ecocode_definition_id": 10,
            "abbreviation": "CR",
            "name": "cultivated resource",
        }
    ]
    dimensions = cast(dict[str, object], sead_composition["dimensions"])
    dimension_row = dict(
        zip(
            cast(list[str], dimensions["fields"]),
            cast(list[list[object]], dimensions["records"])[0],
            strict=True,
        )
    )
    assert dimension_row["dimension_value"] == 0.0
    value_semantics = cast(dict[str, object], sead_composition["value_semantics"])
    assert value_semantics["record_count"] == 1
    relation = cast(dict[str, object], sead_tabs["relation"])
    assert relation["status"] == "refused"
    assert relation["reason_code"] == "source_classification_not_accepted"
    assert relation["eligible_event_count"] == 0
    assert relation["refused_observation_count"] == 2
    provenance = cast(dict[str, object], sead_tabs["provenance"])
    assert provenance["evidence_bundle_path"] == (
        "data/sead/normalized/acquisitions/" + SEAD_GOVERNED_EVIDENCE_RUN_ID
    )
    assert len(cast(str, provenance["evidence_file_set_sha256"])) == 64


def test_projection_refuses_changed_governed_surface_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.absolute()
    _neotoma_fixture(root, monkeypatch)
    install_sead_projection_fixture(root, monkeypatch)
    path = root / "neotoma" / "relational" / "surfaces" / "sites" / "part-00001.json"
    path.write_text(path.read_text() + " ", encoding="utf-8")

    with pytest.raises(ValueError, match="surface digest changed"):
        build_map_evidence_projection(root, sead_projection_layers())


def test_projection_refuses_tampered_sead_multipart_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.absolute()
    _neotoma_fixture(root, monkeypatch)
    install_sead_projection_fixture(root, monkeypatch)
    path = (
        root
        / "sead"
        / "normalized"
        / "acquisitions"
        / SEAD_GOVERNED_EVIDENCE_RUN_ID
        / "chronology_claims"
        / "claims-00001.json"
    )
    path.write_text(path.read_text(encoding="utf-8") + " ", encoding="utf-8")

    with pytest.raises(ValueError, match="evidence (byte count|digest) changed"):
        build_map_evidence_projection(root, sead_projection_layers())


def test_projection_refuses_self_consistent_evidence_with_unknown_entity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.absolute()
    _neotoma_fixture(root, monkeypatch)
    install_sead_projection_fixture(
        root,
        monkeypatch,
        observation_entity_id="sead-analysis-entity:forged",
    )

    with pytest.raises(ValueError, match="unknown entity relation"):
        build_map_evidence_projection(root, sead_projection_layers())
