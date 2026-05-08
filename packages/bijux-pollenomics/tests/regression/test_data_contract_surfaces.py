from __future__ import annotations

import json
from pathlib import Path
import unittest

from bijux_pollenomics.adna.governance_contracts import (
    validate_source_library_project_surfaces,
)
from bijux_pollenomics.data_downloader.collection_summary_schema import (
    validate_collection_summary_file,
)


REPO_ROOT = Path(__file__).resolve().parents[4]


class DataContractSurfaceRegressionTests(unittest.TestCase):
    def test_checked_in_collection_summary_validates_against_current_schema(
        self,
    ) -> None:
        payload = validate_collection_summary_file(
            REPO_ROOT / "data" / "collection_summary.json"
        )

        self.assertIn("contract_artifacts", payload)
        self.assertIn("source_family_state_rows", payload)
        for artifact_path in payload["contract_artifacts"].values():
            self.assertTrue((REPO_ROOT / artifact_path).is_file())

    def test_source_family_contracts_and_stage_matrix_stay_in_sync(self) -> None:
        contract_payload = json.loads(
            (REPO_ROOT / "data" / "source_family_contracts.json").read_text(
                encoding="utf-8"
            )
        )
        matrix_payload = json.loads(
            (
                REPO_ROOT / "data" / "source_family_evidence_stage_matrix.json"
            ).read_text(encoding="utf-8")
        )

        contract_keys = {row["source_key"] for row in contract_payload["rows"]}
        matrix_keys = {row["source_key"] for row in matrix_payload["rows"]}

        self.assertEqual(
            contract_payload["schema_version"], "source-family-contracts.v1"
        )
        self.assertEqual(
            matrix_payload["schema_version"],
            "source-family-evidence-stage-matrix.v1",
        )
        self.assertEqual(contract_keys, matrix_keys)
        self.assertEqual(contract_payload["row_count"], matrix_payload["row_count"])

    def test_fact_and_artifact_contract_registries_keep_durable_keys(self) -> None:
        fact_payload = json.loads(
            (REPO_ROOT / "data" / "source_fact_ownership_registry.json").read_text(
                encoding="utf-8"
            )
        )
        artifact_payload = json.loads(
            (REPO_ROOT / "data" / "evidence_artifact_contracts.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            fact_payload["schema_version"], "source-fact-ownership-registry.v1"
        )
        self.assertEqual(
            artifact_payload["schema_version"], "evidence-artifact-contracts.v1"
        )
        self.assertGreaterEqual(fact_payload["row_count"], 10)
        self.assertEqual(
            {row["artifact_scope"] for row in artifact_payload["rows"]},
            {"country", "paper", "project", "region", "sample", "site"},
        )

    def test_checked_in_project_tree_satisfies_shared_surface_contract(self) -> None:
        validate_source_library_project_surfaces(REPO_ROOT / "data")

    def test_governance_role_registry_stays_reader_facing(self) -> None:
        registry_payload = json.loads(
            (
                REPO_ROOT / "data" / "adna" / "governance" / "surface_role_registry.json"
            ).read_text(encoding="utf-8")
        )
        registry_markdown = (
            REPO_ROOT / "data" / "adna" / "governance" / "surface_role_registry.md"
        ).read_text(encoding="utf-8")

        self.assertEqual(
            registry_payload["schema_version"], "adna-governance-role-registry.v1"
        )
        self.assertIn("cross-species review", registry_markdown.lower())
        self.assertIn("publication accounting", registry_markdown.lower())


if __name__ == "__main__":
    unittest.main()
