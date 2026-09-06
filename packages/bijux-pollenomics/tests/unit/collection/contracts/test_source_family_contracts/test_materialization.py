from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from bijux_pollenomics.collection.contracts.capabilities import (
    NEOTOMA_CLASSIFICATION_EVIDENCE,
    NEOTOMA_PROPAGATION_EVIDENCE,
    SEAD_ADMITTED_ACQUISITION_ADMISSION,
    SEAD_NORMALIZED_EVIDENCE_EVENTS,
    SEAD_NORMALIZED_EVIDENCE_MANIFEST,
    SEAD_NORMALIZED_OBSERVATIONS,
    SEAD_NORMALIZED_RELATIONS,
    build_source_capability_audit_payload,
    build_source_capability_contract_payload,
)
from bijux_pollenomics.collection.contracts.families import (
    build_source_family_contracts,
    build_source_family_state_matrix_payload,
)

from .support import REPO_ROOT


def test_relative_and_absolute_data_roots_produce_identical_capability_audits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    absolute = build_source_capability_audit_payload(
        REPO_ROOT / "data", coverage_metrics_by_source={}, source_blockers={}
    )
    relative = build_source_capability_audit_payload(
        Path("data"), coverage_metrics_by_source={}, source_blockers={}
    )

    assert relative == absolute
    for row in relative["rows"]:
        if (
            row["source_key"] == "sead"
            and SEAD_NORMALIZED_EVIDENCE_MANIFEST in row["evidence_paths"]
        ):
            assert SEAD_NORMALIZED_EVIDENCE_MANIFEST in row["present_evidence_paths"]


def test_sead_provenance_binds_admitted_acquisition_not_legacy_inventory() -> None:
    payload = build_source_capability_contract_payload()
    sources = {source["source_key"]: source for source in payload["sources"]}
    provenance_paths = sources["sead"]["evidence_paths_by_dimension"][
        "dataset_provenance"
    ]

    assert provenance_paths == (
        SEAD_ADMITTED_ACQUISITION_ADMISSION,
        SEAD_NORMALIZED_EVIDENCE_MANIFEST,
    )
    assert "data/sead/raw/nordic_sites.json" not in provenance_paths
    assert (REPO_ROOT / SEAD_ADMITTED_ACQUISITION_ADMISSION).is_file()

    audit = build_source_capability_audit_payload(
        REPO_ROOT / "data",
        coverage_metrics_by_source={},
        source_blockers={},
    )
    row = next(
        row
        for row in audit["rows"]
        if row["source_key"] == "sead" and row["dimension"] == "dataset_provenance"
    )
    assert row["present_evidence_paths"] == provenance_paths
    assert row["materialization"] == "complete"


def test_family_layers_bind_admitted_sead_and_governed_boundary_review() -> None:
    contracts = {
        contract.source_key: contract for contract in build_source_family_contracts()
    }

    sead_raw = contracts["sead"].raw_layer.example_artifacts
    assert sead_raw == (
        SEAD_ADMITTED_ACQUISITION_ADMISSION,
        SEAD_ADMITTED_ACQUISITION_ADMISSION.replace(
            "admission.json", "payloads/tbl_sites.json"
        ),
    )
    assert "data/sead/raw/nordic_sites.json" not in sead_raw

    sead_published = contracts["sead"].published_layer.example_artifacts
    assert sead_published == (
        "docs/report/regions/nordic/nordic_environmental_sites.geojson",
    )
    assert all("nordic_temporal_evidence" not in path for path in sead_published)

    boundary_review = contracts["boundaries"].reviewed_layer.example_artifacts
    assert boundary_review == (
        "data/boundaries/review/boundary_review.json",
        "data/boundaries/review/manifest.json",
        "data/boundaries/review/country-decisions/animal_adna.json",
        "data/boundaries/review/country-decisions/landclim.json",
        "data/boundaries/review/country-decisions/neotoma.json",
        "data/boundaries/review/country-decisions/sead.json",
    )
    assert all((REPO_ROOT / path).is_file() for path in boundary_review)


def test_sead_provenance_refuses_unbound_admission_bytes() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        output_root = Path(temporary_directory) / "data"
        admission_path = output_root / SEAD_ADMITTED_ACQUISITION_ADMISSION.removeprefix(
            "data/"
        )
        admission_path.parent.mkdir(parents=True)
        admission_path.write_text(
            '{"schema_version":"sead-acquisition-admission.v1"}',
            encoding="utf-8",
        )
        (admission_path.parent / "manifest.json").write_text("{}", encoding="utf-8")
        audit = build_source_capability_audit_payload(
            output_root,
            coverage_metrics_by_source={},
            source_blockers={},
        )

    row = next(
        row
        for row in audit["rows"]
        if row["source_key"] == "sead" and row["dimension"] == "dataset_provenance"
    )
    assert row["present_evidence_paths"] == ()
    assert row["materialization"] == "missing"


def test_sead_observation_dimensions_bind_the_full_graph_and_review_refusals() -> None:
    contract = build_source_capability_contract_payload()
    sources = {source["source_key"]: source for source in contract["sources"]}
    evidence = sources["sead"]["evidence_paths_by_dimension"]

    assert any(
        path.endswith("/tbl_taxa_tree_master.json")
        for path in evidence["taxon_identity"]
    )
    assert any(
        path.endswith("/tbl_ecocodes.json")
        for path in evidence["native_ecological_class"]
    )
    assert any(
        path.endswith("/tbl_abundances.json")
        for path in evidence["quantitative_observation"]
    )
    assert any(
        path.endswith("/tbl_units.json") for path in evidence["observation_unit"]
    )
    assert all(
        "tbl_analysis_entities.json" not in path for path in evidence["taxon_identity"]
    )
    assert all(
        "tbl_methods.json" not in path for path in evidence["native_ecological_class"]
    )
    assert all(
        "tbl_analysis_values.json" not in path
        for path in evidence["quantitative_observation"]
    )
    assert SEAD_NORMALIZED_EVIDENCE_MANIFEST in evidence["quantitative_observation"]
    assert SEAD_NORMALIZED_OBSERVATIONS in evidence["quantitative_observation"]
    assert SEAD_NORMALIZED_RELATIONS in evidence["taxon_identity"]
    assert SEAD_NORMALIZED_RELATIONS in evidence["observation_unit"]
    assert SEAD_NORMALIZED_EVIDENCE_EVENTS in evidence["pollen_propagation_event"]

    audit = build_source_capability_audit_payload(
        REPO_ROOT / "data",
        coverage_metrics_by_source={},
        source_blockers={},
    )
    rows = {(row["source_key"], row["dimension"]): row for row in audit["rows"]}
    for dimension in (
        "taxon_identity",
        "native_ecological_class",
        "quantitative_observation",
        "observation_unit",
    ):
        assert rows[("sead", dimension)]["materialization"] == "complete"
        assert (
            "qualified_sead_ecological_classification_review_missing"
            in rows[("sead", dimension)]["reason_codes"]
        )
    for dimension in (
        "derived_pollen_group",
        "derived_ecological_role",
        "crop_cereal_resolution",
        "pollen_propagation_event",
    ):
        assert rows[("sead", dimension)]["materialization"] == "partial"


def test_relative_chronology_and_taxon_evidence_require_explicit_surfaces() -> None:
    audit = build_source_capability_audit_payload(
        REPO_ROOT / "data",
        coverage_metrics_by_source={},
        source_blockers={},
    )
    rows = {(row["source_key"], row["dimension"]): row for row in audit["rows"]}

    assert rows[("neotoma", "relative_chronology")]["materialization"] == "missing"
    assert rows[("aadr", "relative_chronology")]["materialization"] == "missing"
    assert rows[("aadr", "taxon_identity")]["materialization"] == "missing"
    assert (
        rows[("animal_adna", "native_ecological_class")]["materialization"] == "missing"
    )
    assert rows[("landclim", "taxon_identity")]["present_evidence_paths"] == (
        "data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv",
    )


def test_empty_repository_audit_is_fail_closed_without_changing_support() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        payload = build_source_capability_audit_payload(
            Path(temporary_directory) / "data",
            coverage_metrics_by_source={},
            source_blockers={},
        )

    assert payload["row_count"] == 8 * 17
    rows = {(row["source_key"], row["dimension"]): row for row in payload["rows"]}
    assert rows[("neotoma", "site_identity")]["support"] == "supported"
    assert rows[("neotoma", "site_identity")]["materialization"] == "missing"
    assert rows[("boundaries", "numeric_chronology")]["support"] == "unsupported"
    assert (
        rows[("boundaries", "numeric_chronology")]["materialization"]
        == "not_applicable"
    )
    assert rows[("boundaries", "numeric_chronology")]["evidence_file_count"] == 0
    assert rows[("boundaries", "numeric_chronology")]["human_review_required"] is False
    assert rows[("boundaries", "numeric_chronology")]["reason_codes"] == (
        "source_dimension_unsupported",
    )


def test_repository_audit_records_paths_counts_and_unclosed_human_review() -> None:
    payload = build_source_family_state_matrix_payload(
        REPO_ROOT / "data",
        counts={
            "aadr_file_count": 3,
            "landclim_site_count": 490,
            "landclim_grid_cell_count": 77,
            "landclim_temporal_grid_feature_count": 2515,
            "neotoma_point_count": 200,
            "sead_point_count": 2195,
            "raa_total_site_count": 0,
            "raa_heritage_site_count": 0,
            "svar_lake_count": 0,
        },
    )
    audit = payload["capability_materialization_audit"]
    rows = {(row["source_key"], row["dimension"]): row for row in audit["rows"]}

    landclim = rows[("landclim", "numeric_chronology")]
    assert landclim["support"] == "supported"
    assert landclim["materialization"] == "complete"
    assert landclim["evidence_file_count"] == landclim["required_evidence_count"]
    assert landclim["coverage_metrics"] == {
        "landclim_site_count": 490,
        "landclim_grid_cell_count": 77,
        "landclim_temporal_grid_feature_count": 2515,
    }
    assert "qualified_model_semantics_review_missing" in landclim["reason_codes"]

    animal = next(row for row in payload["rows"] if row["source_key"] == "animal_adna")
    assert animal["authority_status"] == "review_required"
    assert "animal_source_recovery_guard_failed" not in animal["blocking_reasons"]
    assert (
        "experiment_to_biological_sample_mapping_unavailable"
        in animal["blocking_reasons"]
    )
    assert "qualified_animal_source_review_missing" in animal["blocking_reasons"]


def test_dimension_evidence_does_not_reuse_unrelated_generic_files() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        output_root = Path(temporary_directory) / "data"
        generic_path = (
            output_root
            / "landclim"
            / "normalized"
            / "nordic_pollen_site_sequences.geojson"
        )
        generic_path.parent.mkdir(parents=True)
        generic_path.write_text(
            '{"type":"FeatureCollection","features":['
            '{"type":"Feature","geometry":{"type":"Point","coordinates":[1,2]},'
            '"properties":{"source_id":"one"}}]}',
            encoding="utf-8",
        )
        payload = build_source_capability_audit_payload(
            output_root,
            coverage_metrics_by_source={},
            source_blockers={},
        )

    rows = {(row["source_key"], row["dimension"]): row for row in payload["rows"]}
    assert rows[("landclim", "site_identity")]["materialization"] == "complete"
    assert rows[("landclim", "derived_pollen_group")]["materialization"] == "missing"
    assert rows[("landclim", "derived_ecological_role")]["materialization"] == "missing"
    assert (
        rows[("landclim", "pollen_propagation_event")]["materialization"] == "missing"
    )


def test_ignored_release_bundles_do_not_overstate_clean_root_materialization() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        repository_root = Path(temporary_directory)
        output_root = repository_root / "data"
        for relative_path in (
            "artifacts/execution-control/classification/"
            "neotoma-audit-f0e5a830/manifest.json",
            "artifacts/execution-control/propagation/"
            "neotoma-pollen-release-refusal-87ac6d28/manifest.json",
        ):
            path = repository_root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}", encoding="utf-8")

        payload = build_source_capability_audit_payload(
            output_root,
            coverage_metrics_by_source={},
            source_blockers={},
        )

    rows = {(row["source_key"], row["dimension"]): row for row in payload["rows"]}
    for dimension in (
        "native_ecological_class",
        "derived_pollen_group",
        "derived_ecological_role",
        "crop_cereal_resolution",
    ):
        row = rows[("neotoma", dimension)]
        assert row["materialization"] == "missing"
        assert row["evidence_paths"] == (NEOTOMA_CLASSIFICATION_EVIDENCE,)
    propagation = rows[("neotoma", "pollen_propagation_event")]
    assert propagation["materialization"] == "missing"
    assert propagation["evidence_paths"] == (NEOTOMA_PROPAGATION_EVIDENCE,)


def test_exact_filenames_require_governed_structure_and_lineage() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        output_root = Path(temporary_directory) / "data"
        fixtures = {
            "landclim/normalized/nordic_pollen_site_sequences.geojson": (
                '{"type":"FeatureCollection","features":[{}]}'
            ),
            "adna/governance/source_library/project_registry.json": (
                '{"schema_version":"adna-source-library.v1","row_count":2,'
                '"rows":[{"project_accession":"one"}]}'
            ),
            "neotoma/relational/surfaces/sites/part-00001.json": (
                '{"schema_version":"neotoma-relational-part.v1",'
                '"source_family":"neotoma","surface":"sites","row_count":1,'
                '"rows":[{"site_id":"one"}]}'
            ),
        }
        for relative_path, content in fixtures.items():
            path = output_root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        payload = build_source_capability_audit_payload(
            output_root,
            coverage_metrics_by_source={},
            source_blockers={},
        )

    rows = {(row["source_key"], row["dimension"]): row for row in payload["rows"]}
    assert rows[("landclim", "site_identity")]["materialization"] == "missing"
    assert rows[("animal_adna", "taxon_identity")]["materialization"] == "missing"
    assert rows[("neotoma", "site_identity")]["materialization"] == "missing"


def test_materialization_is_partial_only_when_an_exact_inventory_is_incomplete() -> (
    None
):
    with tempfile.TemporaryDirectory() as temporary_directory:
        output_root = Path(temporary_directory) / "data"
        sites_path = (
            output_root
            / "landclim"
            / "normalized"
            / "nordic_reveals_temporal_grid_cells.geojson"
        )
        sites_path.parent.mkdir(parents=True)
        sites_path.write_text(
            '{"type":"FeatureCollection","features":['
            '{"type":"Feature","geometry":{"type":"Point","coordinates":[1,2]},'
            '"properties":{"time_bp":100}}]}',
            encoding="utf-8",
        )
        payload = build_source_capability_audit_payload(
            output_root,
            coverage_metrics_by_source={},
            source_blockers={},
        )

    row = next(
        row
        for row in payload["rows"]
        if row["source_key"] == "landclim" and row["dimension"] == "numeric_chronology"
    )
    assert row["materialization"] == "partial"
    assert row["evidence_file_count"] == 1
    assert row["required_evidence_count"] == 2


def test_state_matrix_embeds_exact_capability_audit_cardinality() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        payload = build_source_family_state_matrix_payload(
            Path(temporary_directory) / "data",
            counts={},
        )

    audit = payload["capability_materialization_audit"]
    assert audit["source_count"] == payload["row_count"] == 8
    assert audit["dimension_count"] == 17
    assert audit["row_count"] == 136
