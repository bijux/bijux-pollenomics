from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.adna.species.homo_sapiens.materialization.reconciliation import (
    reconcile_aadr_panels,
)
from bijux_pollenomics.collection.contracts.families import (
    build_source_family_contract_payload,
    build_source_family_contracts,
    build_source_family_state_matrix_payload,
)
from bijux_pollenomics.collection.contracts.repository import (
    build_contract_artifact_paths,
)
from bijux_pollenomics.collection.sources.aadr.materialization.accountability import (
    AadrReleaseManifestIdentity,
    build_aadr_source_accountability_receipt,
    canonical_aadr_source_accountability_bytes,
    validate_aadr_source_accountability_receipt,
)
from bijux_pollenomics.collection.sources.aadr.materialization.source_rows import (
    load_aadr_source_table,
)

_AADR_TEST_HEADER = "\t".join(
    (
        "Genetic ID",
        "Political Entity",
        "Method for Determining Date",
        "Date mean in BP",
        "Date standard deviation in BP",
        "Full Date",
        "Latitude",
        "Longitude",
    )
)


def _write_aadr_accountability_fixture(
    output_root: Path,
    *,
    source_release: str,
    receipt_version: str | None = None,
) -> tuple[Path, Path]:
    release_root = output_root / "aadr" / source_release
    manifest_path = release_root / "release_manifest.json"
    panel_path = release_root / "ho" / "ho.anno"
    panel_path.parent.mkdir(parents=True)
    manifest_bytes = (
        json.dumps({"source": "AADR", "requested_version": source_release}) + "\n"
    ).encode()
    panel_bytes = (_AADR_TEST_HEADER + "\n").encode()
    manifest_path.write_bytes(manifest_bytes)
    panel_path.write_bytes(panel_bytes)
    panel = load_aadr_source_table(
        panel_path,
        source_release=source_release,
        dataset_name="ho",
        logical_source_path=f"data/aadr/{source_release}/ho/ho.anno",
    )
    receipt = build_aadr_source_accountability_receipt(
        reconcile_aadr_panels((panel,)),
        release_manifest=AadrReleaseManifestIdentity(
            logical_path=f"data/aadr/{source_release}/release_manifest.json",
            source_release=source_release,
            sha256=hashlib.sha256(manifest_bytes).hexdigest(),
            byte_count=len(manifest_bytes),
        ),
    )
    receipt_path = (
        output_root
        / "adna/species/homo_sapiens/review"
        / f"aadr_{receipt_version or source_release}_source_accountability.json"
    )
    receipt_path.parent.mkdir(parents=True)
    receipt_path.write_bytes(canonical_aadr_source_accountability_bytes(receipt))
    return receipt_path, panel_path


class DataContractSurfaceUnitTests(unittest.TestCase):
    def test_source_family_contract_payload_names_every_tracked_family(self) -> None:
        payload = build_source_family_contract_payload()

        self.assertEqual(payload["schema_version"], "source-family-contracts.v1")
        source_keys = {row["source_key"] for row in payload["rows"]}
        self.assertEqual(
            source_keys,
            {
                "aadr",
                "animal_adna",
                "boundaries",
                "landclim",
                "neotoma",
                "raa",
                "sead",
                "svar",
            },
        )

    def test_adna_contracts_are_excluded_from_pollen_source_domain(self) -> None:
        contracts = {
            contract.source_key: contract
            for contract in build_source_family_contracts()
        }

        self.assertEqual(contracts["aadr"].domain_group, "human_ancient_dna")
        self.assertEqual(contracts["animal_adna"].domain_group, "animal_ancient_dna")
        self.assertNotEqual(contracts["aadr"].domain_group, "pollen_context")
        self.assertNotEqual(contracts["animal_adna"].domain_group, "pollen_context")
        self.assertEqual(
            contracts["aadr"].reviewed_layer.example_artifacts,
            (
                (
                    "data/adna/species/homo_sapiens/review/"
                    "aadr_v66_source_accountability.json"
                ),
            ),
        )

    def test_state_matrix_and_contract_registry_use_durable_surface_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            for relative_path in (
                "landclim/raw/landclim_sources.json",
                "landclim/normalized/nordic_pollen_site_sequences.geojson",
                "boundaries/normalized/nordic_country_boundaries.geojson",
                "adna/governance/source_library/project_registry.json",
                "adna/governance/animal_sample_foundation_truth.json",
            ):
                path = output_root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.suffix == ".geojson":
                    path.write_text('{"features": []}', encoding="utf-8")
                else:
                    path.write_text("{}", encoding="utf-8")

            matrix_payload = build_source_family_state_matrix_payload(
                output_root,
                counts={
                    "aadr_file_count": 2,
                    "landclim_site_count": 10,
                    "landclim_grid_cell_count": 20,
                    "landclim_temporal_grid_feature_count": 30,
                    "neotoma_point_count": 0,
                    "sead_point_count": 0,
                    "raa_total_site_count": 0,
                    "raa_heritage_site_count": 0,
                },
            )
            contract_paths = build_contract_artifact_paths(output_root)

        self.assertEqual(
            matrix_payload["schema_version"], "source-family-evidence-stage-matrix.v2"
        )
        self.assertIn("source_family_contracts", contract_paths)
        self.assertIn("source_fact_ownership_registry", contract_paths)
        self.assertNotIn(
            "tmp",
            " ".join(key for key in contract_paths),
        )

    def test_state_matrix_requires_named_artifacts_for_stage_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            normalized_root = output_root / "adna/species/homo_sapiens/normalized"
            normalized_root.mkdir(parents=True)
            (normalized_root / ".gitkeep").touch()
            (output_root / "svar/normalized").mkdir(parents=True)
            (output_root / "svar/normalized/svar_summary.json").write_text(
                '{"lake_count": 1}',
                encoding="utf-8",
            )

            payload = build_source_family_state_matrix_payload(
                output_root,
                counts={"aadr_file_count": 1, "svar_lake_count": 1},
            )

        rows = {row["source_key"]: row for row in payload["rows"]}
        self.assertEqual(rows["aadr"]["normalized_status"], "missing")
        self.assertEqual(rows["aadr"]["reviewed_status"], "missing")
        self.assertEqual(rows["aadr"]["authority_status"], "review_required")
        self.assertIn(
            "missing_or_invalid_aadr_source_accountability",
            rows["aadr"]["blocking_reasons"],
        )
        self.assertEqual(rows["svar"]["normalized_status"], "missing")
        self.assertIn(
            "missing_normalized_outputs",
            rows["svar"]["blocking_reasons"],
        )

    def test_malformed_aadr_accountability_is_not_source_authority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            receipt = (
                output_root / "adna/species/homo_sapiens/review/"
                "aadr_v66_source_accountability.json"
            )
            receipt.parent.mkdir(parents=True)
            receipt.write_text("{}", encoding="utf-8")

            payload = build_source_family_state_matrix_payload(
                output_root,
                counts={"aadr_file_count": 0},
            )

        row = next(row for row in payload["rows"] if row["source_key"] == "aadr")
        self.assertEqual(row["reviewed_status"], "present")
        self.assertEqual(row["authority_status"], "review_required")
        self.assertIn(
            "missing_or_invalid_aadr_source_accountability",
            row["blocking_reasons"],
        )

    def test_non_default_aadr_version_drives_contract_and_authority_paths(self) -> None:
        version = "v70"
        contracts = {
            contract.source_key: contract
            for contract in build_source_family_contracts(version)
        }
        self.assertEqual(
            contracts["aadr"].raw_layer.example_artifacts,
            ("data/aadr/v70",),
        )
        self.assertEqual(
            contracts["aadr"].reviewed_layer.example_artifacts,
            (
                (
                    "data/adna/species/homo_sapiens/review/"
                    "aadr_v70_source_accountability.json"
                ),
            ),
        )

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            _write_aadr_accountability_fixture(
                output_root,
                source_release=version,
            )
            payload = build_source_family_state_matrix_payload(
                output_root,
                counts={"aadr_file_count": 1},
                version=version,
            )

        row = next(row for row in payload["rows"] if row["source_key"] == "aadr")
        self.assertEqual(row["reviewed_status"], "present")
        self.assertEqual(row["authority_status"], "review_required")
        self.assertIn(
            "qualified_human_adna_source_review_missing",
            row["blocking_reasons"],
        )
        self.assertNotIn(
            "missing_or_invalid_aadr_source_accountability",
            row["blocking_reasons"],
        )

    def test_aadr_authority_refuses_receipt_from_another_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            _write_aadr_accountability_fixture(
                output_root,
                source_release="v66",
                receipt_version="v70",
            )
            payload = build_source_family_state_matrix_payload(
                output_root,
                counts={"aadr_file_count": 1},
                version="v70",
            )

        row = next(row for row in payload["rows"] if row["source_key"] == "aadr")
        self.assertEqual(row["authority_status"], "review_required")
        self.assertIn(
            "aadr_source_accountability_release_mismatch",
            row["blocking_reasons"],
        )
        self.assertNotIn(
            "qualified_human_adna_source_review_missing",
            row["blocking_reasons"],
        )

    def test_aadr_authority_refuses_structurally_valid_stale_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            receipt_path, panel_path = _write_aadr_accountability_fixture(
                output_root,
                source_release="v70",
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            panel_path.write_bytes(panel_path.read_bytes() + b"\n")
            validate_aadr_source_accountability_receipt(receipt)

            payload = build_source_family_state_matrix_payload(
                output_root,
                counts={"aadr_file_count": 1},
                version="v70",
            )

        row = next(row for row in payload["rows"] if row["source_key"] == "aadr")
        self.assertEqual(row["authority_status"], "review_required")
        self.assertIn(
            "stale_or_unverifiable_aadr_source_accountability_inputs",
            row["blocking_reasons"],
        )
        self.assertNotIn(
            "qualified_human_adna_source_review_missing",
            row["blocking_reasons"],
        )

    def test_aadr_authority_refuses_symlinked_input_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            physical_root = workspace / "physical-data"
            _receipt_path, _panel_path = _write_aadr_accountability_fixture(
                physical_root,
                source_release="v70",
            )
            output_root = workspace / "data"
            output_root.mkdir()
            (output_root / "aadr").symlink_to(
                physical_root / "aadr", target_is_directory=True
            )
            receipt_source = (
                physical_root / "adna/species/homo_sapiens/review/"
                "aadr_v70_source_accountability.json"
            )
            receipt_target = (
                output_root / "adna/species/homo_sapiens/review/"
                "aadr_v70_source_accountability.json"
            )
            receipt_target.parent.mkdir(parents=True)
            receipt_target.write_bytes(receipt_source.read_bytes())

            payload = build_source_family_state_matrix_payload(
                output_root,
                counts={"aadr_file_count": 1},
                version="v70",
            )

        row = next(row for row in payload["rows"] if row["source_key"] == "aadr")
        self.assertIn(
            "stale_or_unverifiable_aadr_source_accountability_inputs",
            row["blocking_reasons"],
        )
