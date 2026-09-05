from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

from bijux_pollenomics.data_downloader import source_capabilities as capabilities_module
from bijux_pollenomics.data_downloader.source_capabilities import (
    CAPABILITY_DIMENSIONS,
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
from bijux_pollenomics.data_downloader.source_family_contracts import (
    build_source_family_contract_payload,
    build_source_family_contracts,
    build_source_family_state_matrix_payload,
)
from bijux_pollenomics.data_downloader.sources.sead.archive import (
    SEAD_FULL_EVIDENCE_SOURCE_TABLES,
)

REPO_ROOT = Path(__file__).resolve().parents[4]


def _write_full_sead_admission_fixture(
    output_root: Path, payload_bytes: bytes
) -> tuple[Path, Path]:
    admission_path = output_root / SEAD_ADMITTED_ACQUISITION_ADMISSION.removeprefix(
        "data/"
    )
    acquisition_root = admission_path.parent
    payload_path = acquisition_root / "payloads/tbl_sites.json"
    payload_path.parent.mkdir(parents=True)
    payload_path.write_bytes(payload_bytes)
    manifest_path = acquisition_root / "manifest.json"
    manifest_path.write_bytes(b'#{"acquisition":"fixture"}')
    expected_paths = {
        "country-decisions.json",
        "manifest.json",
        "parent-admission.json",
        "reconciliation/countries.json",
        "reconciliation/joins.json",
        *(f"payloads/{table}.json" for table in SEAD_FULL_EVIDENCE_SOURCE_TABLES),
        *(f"receipts/{table}.json" for table in SEAD_FULL_EVIDENCE_SOURCE_TABLES),
    }
    copied_files = [
        {"path": path, "byte_count": 0, "sha256": "0" * 64}
        for path in sorted(expected_paths)
    ]
    for record in copied_files:
        if record["path"] == "manifest.json":
            record["byte_count"] = manifest_path.stat().st_size
            record["sha256"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        elif record["path"] == "payloads/tbl_sites.json":
            record["byte_count"] = len(payload_bytes)
            record["sha256"] = hashlib.sha256(payload_bytes).hexdigest()
    admission_path.write_text(
        json.dumps(
            {
                "schema_version": "sead-acquisition-admission.v1",
                "source_family": "sead",
                "run_id": acquisition_root.name,
                "acquisition_manifest_sha256": hashlib.sha256(
                    manifest_path.read_bytes()
                ).hexdigest(),
                "declared_scope": {
                    "scope_key": "full_evidence_relations",
                    "status": "complete_for_declared_relations",
                    "table_count": 61,
                    "join_count": 86,
                    "tables": list(SEAD_FULL_EVIDENCE_SOURCE_TABLES),
                    "wp01_complete": False,
                },
                "release_status": "refused",
                "copied_files": copied_files,
            }
        ),
        encoding="utf-8",
    )
    return admission_path, payload_path


def test_capability_contract_covers_every_source_and_dimension_exactly() -> None:
    payload = build_source_capability_contract_payload()

    assert payload["schema_version"] == "source-capability-contract.v1"
    assert payload["dimension_count"] == 17
    assert payload["dimensions"] == list(CAPABILITY_DIMENSIONS)
    assert payload["source_count"] == 8
    sources = payload["sources"]
    assert isinstance(sources, list)
    assert {source["source_key"] for source in sources} == {
        "aadr",
        "animal_adna",
        "boundaries",
        "landclim",
        "neotoma",
        "raa",
        "sead",
        "svar",
    }
    for source in sources:
        assert set(source["support_by_dimension"]) == set(CAPABILITY_DIMENSIONS)
        assert set(source["evidence_paths_by_dimension"]) == set(CAPABILITY_DIMENSIONS)
        assert set(source["support_by_dimension"].values()) <= {
            "supported",
            "partial",
            "unsupported",
        }


def test_normative_support_map_and_repository_extension_are_explicit() -> None:
    payload = build_source_capability_contract_payload()
    sources = {source["source_key"]: source for source in payload["sources"]}
    partial = {
        "neotoma": {
            "four_country_coverage",
            "chronology_uncertainty",
            "relative_chronology",
            "derived_pollen_group",
            "derived_ecological_role",
        },
        "sead": {
            "four_country_coverage",
            "chronology_uncertainty",
            "derived_pollen_group",
            "derived_ecological_role",
            "crop_cereal_resolution",
            "pollen_propagation_event",
        },
        "landclim": {
            "four_country_coverage",
            "within_site_hierarchy",
            "chronology_uncertainty",
            "taxon_identity",
            "derived_pollen_group",
            "derived_ecological_role",
            "crop_cereal_resolution",
            "dataset_provenance",
            "pollen_propagation_event",
        },
        "raa": {
            "within_site_hierarchy",
            "numeric_chronology",
            "chronology_uncertainty",
            "quantitative_observation",
            "observation_unit",
        },
        "svar": {"within_site_hierarchy", "dataset_provenance"},
        "animal_adna": {
            "four_country_coverage",
            "chronology_uncertainty",
            "relative_chronology",
            "native_ecological_class",
            "quantitative_observation",
            "observation_unit",
        },
        "boundaries": set(),
    }
    unsupported = {
        "neotoma": set(),
        "sead": set(),
        "landclim": {"relative_chronology"},
        "raa": {
            "four_country_coverage",
            "taxon_identity",
            "native_ecological_class",
            "derived_pollen_group",
            "derived_ecological_role",
            "crop_cereal_resolution",
            "pollen_propagation_event",
        },
        "svar": {
            "four_country_coverage",
            "numeric_chronology",
            "chronology_uncertainty",
            "relative_chronology",
            "taxon_identity",
            "native_ecological_class",
            "derived_pollen_group",
            "derived_ecological_role",
            "crop_cereal_resolution",
            "pollen_propagation_event",
        },
        "animal_adna": {
            "derived_pollen_group",
            "derived_ecological_role",
            "crop_cereal_resolution",
            "pollen_propagation_event",
        },
        "boundaries": {
            "within_site_hierarchy",
            "numeric_chronology",
            "chronology_uncertainty",
            "relative_chronology",
            "taxon_identity",
            "native_ecological_class",
            "derived_pollen_group",
            "derived_ecological_role",
            "crop_cereal_resolution",
            "quantitative_observation",
            "observation_unit",
            "pollen_propagation_event",
        },
    }
    for source_key in partial:
        expected = {
            dimension: (
                "unsupported"
                if dimension in unsupported[source_key]
                else "partial"
                if dimension in partial[source_key]
                else "supported"
            )
            for dimension in CAPABILITY_DIMENSIONS
        }
        assert sources[source_key]["support_by_dimension"] == expected

    assert payload["normative_contract"] == {
        "contract_id": "bijux-pollenomics-source-capability-matrix",
        "schema_version": "1.0.0",
        "source_count": 7,
        "source_keys": sorted(partial),
    }
    assert payload["extension_sources"] == ["aadr"]
    assert sources["neotoma"]["evidence_class"] == "observed_paleoecological"
    assert (
        sources["animal_adna"]["evidence_class"]
        == "observed_genetic_or_zooarchaeological"
    )


def test_contract_registry_keeps_capability_separate_from_materialization() -> None:
    payload = build_source_family_contract_payload()
    capability = payload["capability_contract"]

    assert capability["schema_version"] == "source-capability-contract.v1"
    assert all("materialization" not in source for source in capability["sources"])
    assert payload["schema_version"] == "source-family-contracts.v1"


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


def test_aadr_receipt_rejects_same_size_artifact_substitution() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        output_root = Path(temporary_directory) / "data"
        release_root = output_root / "aadr/v66"
        first_path = release_root / "1240k/example.anno"
        second_path = release_root / "ho/example-ho.anno"
        first_path.parent.mkdir(parents=True)
        second_path.parent.mkdir(parents=True)
        first_path.write_bytes(b"id\tvalue\none\talpha\n")
        second_path.write_bytes(b"id\tvalue\ntwo\tbeta\n")
        manifest_path = release_root / "release_manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "source": "AADR",
                    "downloaded_files": [
                        "1240k/example.anno",
                        "ho/example-ho.anno",
                    ],
                    "anno_files": [
                        {
                            "filename": first_path.name,
                            "filesize": first_path.stat().st_size,
                            "md5": hashlib.md5(
                                first_path.read_bytes(), usedforsecurity=False
                            ).hexdigest(),
                        },
                        {
                            "filename": second_path.name,
                            "filesize": second_path.stat().st_size,
                            "md5": hashlib.md5(
                                second_path.read_bytes(), usedforsecurity=False
                            ).hexdigest(),
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

        before = build_source_capability_audit_payload(
            output_root,
            coverage_metrics_by_source={},
            source_blockers={},
        )
        first_path.write_bytes(b"id\tvalue\none\tomega\n")
        after = build_source_capability_audit_payload(
            output_root,
            coverage_metrics_by_source={},
            source_blockers={},
        )

    before_rows = {(row["source_key"], row["dimension"]): row for row in before["rows"]}
    after_rows = {(row["source_key"], row["dimension"]): row for row in after["rows"]}
    assert before_rows[("aadr", "dataset_provenance")]["materialization"] == (
        "complete"
    )
    assert after_rows[("aadr", "dataset_provenance")]["materialization"] == ("missing")


def test_sead_admission_rejects_same_size_payload_substitution(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        output_root = Path(temporary_directory) / "data"
        payload_bytes = json.dumps(
            {
                "schema_version": "sead-table-payload.v1",
                "table": "tbl_sites",
                "rows": [{"site_id": 1}],
            },
            separators=(",", ":"),
        ).encode()
        _, payload_path = _write_full_sead_admission_fixture(output_root, payload_bytes)
        monkeypatch.setattr(
            capabilities_module, "_valid_sead_admission", lambda _path: True
        )

        before = build_source_capability_audit_payload(
            output_root,
            coverage_metrics_by_source={},
            source_blockers={},
        )
        payload_path.write_bytes(payload_bytes.replace(b'"site_id":1', b'"site_id":2'))
        after = build_source_capability_audit_payload(
            output_root,
            coverage_metrics_by_source={},
            source_blockers={},
        )

    before_rows = {(row["source_key"], row["dimension"]): row for row in before["rows"]}
    after_rows = {(row["source_key"], row["dimension"]): row for row in after["rows"]}
    assert before_rows[("sead", "site_identity")]["materialization"] == "complete"
    assert after_rows[("sead", "site_identity")]["materialization"] == "partial"
    assert any(
        path.endswith("/payloads/tbl_sites.json")
        for path in after_rows[("sead", "site_identity")]["missing_evidence_paths"]
    )


def test_sead_admission_rejects_incomplete_declared_file_set() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        output_root = Path(temporary_directory) / "data"
        payload_bytes = json.dumps(
            {
                "schema_version": "sead-table-payload.v1",
                "table": "tbl_sites",
                "rows": [{"site_id": 1}],
            },
            separators=(",", ":"),
        ).encode()
        admission_path, _ = _write_full_sead_admission_fixture(
            output_root, payload_bytes
        )

        audit = build_source_capability_audit_payload(
            output_root,
            coverage_metrics_by_source={},
            source_blockers={},
        )

        row = next(
            row
            for row in audit["rows"]
            if row["source_key"] == "sead" and row["dimension"] == "site_identity"
        )
        assert not capabilities_module._valid_sead_admission(admission_path)
        assert row["materialization"] != "complete"
        assert SEAD_ADMITTED_ACQUISITION_ADMISSION in row["missing_evidence_paths"]


def test_sead_admission_rejects_payload_and_admission_rewrite() -> None:
    source_root = (REPO_ROOT / SEAD_ADMITTED_ACQUISITION_ADMISSION).parent
    with tempfile.TemporaryDirectory(dir=REPO_ROOT / "artifacts") as temporary:
        destination = Path(temporary) / source_root.name
        shutil.copytree(source_root, destination, copy_function=os.link)
        admission_path = destination / "admission.json"
        payload_path = destination / "payloads/tbl_sites.json"
        assert capabilities_module._valid_sead_admission(admission_path)

        payload_bytes = payload_path.read_bytes()
        changed_bytes = payload_bytes.replace(b'"site_id":1,', b'"site_id":2,', 1)
        assert changed_bytes != payload_bytes
        payload_path.unlink()
        payload_path.write_bytes(changed_bytes)
        admission = json.loads(admission_path.read_text(encoding="utf-8"))
        record = next(
            item
            for item in admission["copied_files"]
            if item["path"] == "payloads/tbl_sites.json"
        )
        record["byte_count"] = len(changed_bytes)
        record["sha256"] = hashlib.sha256(changed_bytes).hexdigest()
        admission_path.unlink()
        admission_path.write_text(
            json.dumps(admission, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

        assert not capabilities_module._valid_sead_admission(admission_path)


def test_sead_normalized_evidence_rejects_raw_digest_divergence() -> None:
    normalized_source = REPO_ROOT / SEAD_NORMALIZED_EVIDENCE_MANIFEST
    raw_source = REPO_ROOT / SEAD_ADMITTED_ACQUISITION_ADMISSION
    with tempfile.TemporaryDirectory(dir=REPO_ROOT / "artifacts") as temporary:
        data_root = Path(temporary) / "data"
        normalized_root = (
            data_root / SEAD_NORMALIZED_EVIDENCE_MANIFEST.removeprefix("data/")
        ).parent
        raw_root = (
            data_root / SEAD_ADMITTED_ACQUISITION_ADMISSION.removeprefix("data/")
        ).parent
        shutil.copytree(
            normalized_source.parent, normalized_root, copy_function=os.link
        )
        shutil.copytree(raw_source.parent, raw_root, copy_function=os.link)
        manifest_path = normalized_root / "evidence_materialization_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert capabilities_module._valid_sead_normalized_admission_link(
            manifest_path, manifest
        )

        relation_path = normalized_root / "observation_relation_index.json"
        relations = json.loads(relation_path.read_text(encoding="utf-8"))
        relations["source_table_sha256"]["tbl_sites"] = "0" * 64
        relation_path.unlink()
        relation_path.write_text(
            json.dumps(relations, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

        assert not capabilities_module._valid_sead_normalized_admission_link(
            manifest_path, manifest
        )


def test_sead_admission_rejects_the_obsolete_19_table_25_join_scope() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        output_root = Path(temporary_directory) / "data"
        payload_bytes = json.dumps(
            {
                "schema_version": "sead-table-payload.v1",
                "table": "tbl_sites",
                "rows": [{"site_id": 1}],
            },
            separators=(",", ":"),
        ).encode()
        admission_path, _ = _write_full_sead_admission_fixture(
            output_root, payload_bytes
        )
        admission = json.loads(admission_path.read_text(encoding="utf-8"))
        admission["declared_scope"].update(
            {
                "scope_key": "declared_chronology_relations",
                "table_count": 19,
                "join_count": 25,
                "tables": list(SEAD_FULL_EVIDENCE_SOURCE_TABLES[:19]),
            }
        )
        admission_path.write_text(json.dumps(admission), encoding="utf-8")

        assert not capabilities_module._valid_sead_admission(admission_path)


def test_receipt_validators_reject_traversal_and_symlink_artifacts() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        outside = root / "outside.bin"
        outside.write_bytes(b"governed bytes")

        landclim_root = root / "landclim"
        landclim_root.mkdir()
        linked_asset = landclim_root / "linked.bin"
        linked_asset.symlink_to(outside)
        landclim_payload = {
            "schema_version": "landclim-raw-receipt.v1",
            "source": "LandClim",
            "asset_count": 1,
            "assets": [
                {
                    "filename": linked_asset.name,
                    "size_bytes": outside.stat().st_size,
                    "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
                }
            ],
        }
        assert not capabilities_module._valid_landclim_receipt(
            landclim_root / "receipt.json", landclim_payload
        )

        boundary_root = root / "boundaries/raw"
        boundary_root.mkdir(parents=True)
        boundary_payload = {
            "schema_version": "natural-earth-boundary-receipt.v1",
            "source": "Natural Earth",
            "country_artifacts": {
                country: {
                    "path": "../../outside.bin",
                    "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
                    "feature_count": 1,
                }
                for country in ("Sweden", "Denmark", "Norway", "Finland")
            },
            "normalized_artifact": {
                "path": "../../outside.bin",
                "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
                "feature_count": 4,
            },
        }
        assert not capabilities_module._valid_boundary_receipt(
            boundary_root / "receipt.json", boundary_payload
        )

        aadr_root = root / "aadr"
        (aadr_root / "1240k").mkdir(parents=True)
        aadr_link = aadr_root / "1240k/linked.anno"
        aadr_link.symlink_to(outside)
        aadr_payload = {
            "source": "AADR",
            "downloaded_files": ["1240k/linked.anno"],
            "anno_files": [
                {
                    "filename": aadr_link.name,
                    "filesize": outside.stat().st_size,
                    "md5": hashlib.md5(
                        outside.read_bytes(), usedforsecurity=False
                    ).hexdigest(),
                }
            ],
        }
        assert not capabilities_module._valid_aadr_receipt(
            aadr_root / "release_manifest.json", aadr_payload
        )


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
