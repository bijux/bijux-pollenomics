from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.adna import (
    build_animal_sample_aggregation_warnings,
    build_animal_sample_foundation_truth,
    build_animal_sample_product_contract,
    build_project_locality_count_drift,
    build_species_sample_count_drift,
)
from bijux_pollenomics.adna.tracked_data import materialize_tracked_species_adna


class AdnaSampleTruthUnitTests(unittest.TestCase):
    def test_animal_sample_product_contract_defines_mandatory_sample_fields(self) -> None:
        payload = build_animal_sample_product_contract()

        self.assertEqual(payload["schema_version"], "animal-sample-product-contract.v1")
        self.assertEqual(payload["primary_durable_unit"], "sample_record")
        required_fields = {row["field"] for row in payload["required_fields"]}
        self.assertIn("identity.stable_token", required_fields)
        self.assertIn("species_latin_name", required_fields)
        self.assertIn("project_accession", required_fields)
        self.assertIn("chronology.original_text", required_fields)
        self.assertIn("coordinates.confidence", required_fields)
        self.assertIn("inclusion_status", required_fields)

    def test_animal_sample_foundation_truth_counts_current_species_and_projects(self) -> None:
        repo_root = Path(__file__).resolve().parents[4]
        payload = build_animal_sample_foundation_truth(repo_root / "data")

        self.assertEqual(payload["schema_version"], "animal-sample-foundation-truth.v1")
        self.assertEqual(payload["summary"]["tracked_species_count"], 10)
        self.assertGreater(payload["summary"]["tracked_project_count"], 0)
        self.assertGreater(payload["summary"]["sample_row_count"], 0)
        self.assertGreater(
            payload["summary"]["blocked_missing_location_detail_count"],
            0,
        )
        sheep_row = next(
            row
            for row in payload["species_rows"]
            if row["species_latin_name"] == "Ovis aries"
        )
        self.assertGreaterEqual(sheep_row["sample_row_count"], 1)
        self.assertTrue(sheep_row["uses_project_level_sample_anchor"])

    def test_species_summary_drift_is_clean_for_materialized_species_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            materialize_tracked_species_adna(data_root)

            drift_rows = build_species_sample_count_drift(data_root)

        self.assertEqual(drift_rows, ())

    def test_project_locality_drift_detects_sample_site_disagreement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            species_root = data_root / "adna" / "ovis_aries"
            normalized_root = species_root / "normalized"
            normalized_root.mkdir(parents=True, exist_ok=True)
            (species_root / "README.md").write_text(
                "# sheep\n\n- Curated sample rows: `2`\n",
                encoding="utf-8",
            )
            _write_json(
                normalized_root / "sample_records.json",
                {
                    "samples": [
                        _sample_row(
                            stable_token="ovis_aries:sample:one",
                            locality_token="ovis_aries:sample-site:one",
                            locality_text="Site One",
                            project_accession="PRJTEST",
                        ),
                        _sample_row(
                            stable_token="ovis_aries:sample:two",
                            locality_token="ovis_aries:sample-site:two",
                            locality_text="Site Two",
                            project_accession="PRJTEST",
                        ),
                    ]
                },
            )
            _write_json(
                normalized_root / "locality_summaries.json",
                {
                    "localities": [
                        {
                            "identity": {
                                "stable_token": "ovis_aries:project-locality:prjtest",
                            },
                            "project_accessions": ["PRJTEST"],
                            "sample_namespace": "ovis_aries:project_locality",
                        }
                    ]
                },
            )

            drift_rows = build_project_locality_count_drift(data_root)

        self.assertEqual(len(drift_rows), 1)
        self.assertEqual(drift_rows[0]["project_accession"], "PRJTEST")
        self.assertEqual(drift_rows[0]["sample_backed_site_count"], 2)
        self.assertEqual(drift_rows[0]["project_locality_summary_count"], 1)

    def test_sample_aggregation_warnings_count_project_level_dependence(self) -> None:
        repo_root = Path(__file__).resolve().parents[4]
        payload = build_animal_sample_aggregation_warnings(
            repo_root / "data",
            repo_root / "docs" / "report",
        )

        self.assertEqual(
            payload["schema_version"],
            "animal-sample-aggregation-warnings.v1",
        )
        self.assertGreater(payload["summary"]["project_accession_anchor_count"], 0)
        self.assertGreater(
            payload["summary"]["projects_with_project_level_sample_anchors"],
            0,
        )
        warning_classes = {row["warning_class"] for row in payload["warning_rows"]}
        self.assertIn("project_level_sample_anchors", warning_classes)
        self.assertIn("project_locality_summary_rows", warning_classes)


def _sample_row(
    *,
    stable_token: str,
    locality_token: str,
    locality_text: str,
    project_accession: str,
) -> dict[str, object]:
    return {
        "identity": {"stable_token": stable_token},
        "locality_identity": {
            "stable_token": locality_token,
            "locality_text": locality_text,
        },
        "project_accession": project_accession,
        "paper_doi": "10.1000/test",
        "paper_url": "https://doi.org/10.1000/test",
        "supplementary_source": "supplementary/test.csv",
        "sample_basis": "project_accession_anchor",
        "inclusion_status": "site_curated",
        "chronology": {
            "original_text": "1000-1200 BP",
            "time_start_bp": 1000,
            "time_end_bp": 1200,
        },
        "coordinates": {
            "latitude_text": "59.0",
            "longitude_text": "18.0",
            "confidence": "approximate",
        },
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
