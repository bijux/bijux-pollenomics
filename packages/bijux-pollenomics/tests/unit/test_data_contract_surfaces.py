from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.adna.governance_contracts import (
    build_adna_governance_role_registry,
    build_source_library_project_surface_contract,
    materialize_adna_governance_contracts,
)
from bijux_pollenomics.data_downloader.data_contracts import (
    build_contract_artifact_paths,
    build_evidence_artifact_contract_payload,
    build_source_fact_ownership_payload,
)
from bijux_pollenomics.data_downloader.source_family_contracts import (
    build_source_family_contract_payload,
    build_source_family_state_matrix_payload,
)


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
            },
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
                    "neotoma_point_count": 0,
                    "sead_point_count": 0,
                    "raa_total_site_count": 0,
                    "raa_heritage_site_count": 0,
                },
            )
            contract_paths = build_contract_artifact_paths(output_root)

        self.assertEqual(
            matrix_payload["schema_version"], "source-family-evidence-stage-matrix.v1"
        )
        self.assertIn("source_family_contracts", contract_paths)
        self.assertIn("source_fact_ownership_registry", contract_paths)
        self.assertNotIn(
            "tmp",
            " ".join(
                key
                for key in contract_paths
            ),
        )

    def test_fact_and_artifact_contract_payloads_choose_governing_surfaces(self) -> None:
        fact_payload = build_source_fact_ownership_payload()
        artifact_payload = build_evidence_artifact_contract_payload()

        self.assertEqual(
            fact_payload["schema_version"], "source-fact-ownership-registry.v1"
        )
        self.assertEqual(
            artifact_payload["schema_version"], "evidence-artifact-contracts.v1"
        )
        fact_keys = {row["fact_key"] for row in fact_payload["rows"]}
        artifact_keys = {row["artifact_key"] for row in artifact_payload["rows"]}
        self.assertIn("animal_sample_identity", fact_keys)
        self.assertIn("country_publication_bundle", artifact_keys)

    def test_materialize_adna_governance_contracts_writes_role_and_project_contracts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            project_root = (
                output_root
                / "adna"
                / "governance"
                / "source_library"
                / "projects"
                / "PRJTEST"
            )
            project_root.mkdir(parents=True, exist_ok=True)
            for filename in (
                "bundle_manifest.json",
                "intake_dossier.json",
                "curation_note.md",
                "sample_master.json",
                "sample_master.csv",
                "sample_sites.json",
                "sample_sites.csv",
                "locality_worksheet.json",
                "locality_worksheet.csv",
                "sample_locality_evidence.json",
                "sample_locality_evidence.csv",
                "sample_chronology.json",
                "sample_chronology.csv",
                "sample_chronology_evidence.json",
                "sample_chronology_evidence.csv",
                "sample_chronology_provenance.json",
                "sample_chronology_provenance.csv",
            ):
                (project_root / filename).write_text("{}", encoding="utf-8")

            materialize_adna_governance_contracts(output_root)

            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "surface_role_registry.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "project_surface_contract.json"
                ).is_file()
            )
            role_payload = build_adna_governance_role_registry()
            project_contract = build_source_library_project_surface_contract()

        self.assertEqual(
            role_payload["schema_version"], "adna-governance-role-registry.v1"
        )
        self.assertEqual(
            project_contract["schema_version"],
            "source-library-project-surface-contract.v1",
        )


if __name__ == "__main__":
    unittest.main()
