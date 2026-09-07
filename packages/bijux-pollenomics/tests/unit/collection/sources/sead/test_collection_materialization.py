"""SEAD collection materialization coverage."""

from __future__ import annotations

import json
import tempfile
from contextlib import chdir
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import patch

import pytest
from bijux_pollenomics.collection.sources.sead import collection as sead_collection
from bijux_pollenomics.collection.sources.sead.collection import (
    collect_sead_data,
    materialize_sead_repository_surfaces,
)

from tests.support.context_data import NordicBoundaryTestCase

_SITE_UUID = "16fd2706-8baf-433b-82eb-8c7fada847da"


class SeadMaterializationTests(NordicBoundaryTestCase):
    def test_repository_materialization_root_refuses_missing_and_linked_paths(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            with pytest.raises(ValueError, match="must exist"):
                sead_collection._validated_repository_data_root(root / "missing")
            data_root = root / "data"
            data_root.mkdir()
            linked = root / "linked-data"
            linked.symlink_to(data_root, target_is_directory=True)
            with pytest.raises(ValueError, match="must not traverse a symlink"):
                sead_collection._validated_repository_data_root(linked)

            filesystem_root = Path(root.anchor)
            non_linked_directory = next(
                path
                for path in filesystem_root.iterdir()
                if path.is_dir() and not path.is_symlink()
            )
            root_alias = non_linked_directory / ".."
            with pytest.raises(ValueError, match="must not resolve"):
                sead_collection._validated_repository_data_root(root_alias)

    def test_source_snapshot_date_requires_matching_zoned_receipt(self) -> None:
        receipt = {"run_id": "sead-test-run", "started_at": "2026-05-08T23:59:59Z"}
        copied = {"receipts/tbl_sites.json": json.dumps(receipt).encode()}
        self.assertEqual(
            sead_collection._source_snapshot_date(
                copied, expected_run_id="sead-test-run"
            ).isoformat(),
            "2026-05-08",
        )
        receipt["started_at"] = "2026-05-08T23:59:59"
        with pytest.raises(ValueError, match="timezone"):
            sead_collection._source_snapshot_date(
                {"receipts/tbl_sites.json": json.dumps(receipt).encode()},
                expected_run_id="sead-test-run",
            )
        with pytest.raises(ValueError, match="run identity differs"):
            sead_collection._source_snapshot_date(copied, expected_run_id="another-run")

    def test_collect_sead_data_writes_inventory_summary(self) -> None:
        rows = [
            {
                "site_id": 6468,
                "site_name": "10412 Fjalkinge",
                "national_site_identifier": "10412",
                "latitude_dd": 56.05,
                "longitude_dd": 14.28,
                "altitude": 24,
                "site_description": "",
                "site_uuid": _SITE_UUID,
                "dataset_count": 1,
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "sead"
            with patch(
                "bijux_pollenomics.collection.sources.sead.collection.fetch_sead_site_inventory",
                return_value=type(
                    "FetchResult",
                    (),
                    {
                        "rows": rows,
                        "inventory_summary": {
                            "site_row_count": 1,
                            "sample_group_row_count": 2,
                            "physical_sample_row_count": 3,
                            "analysis_entity_row_count": 4,
                            "analysis_value_row_count": 5,
                            "dating_range_row_count": 6,
                            "age_type_row_count": 7,
                            "relative_date_row_count": 8,
                            "dataset_row_count": 9,
                            "site_reference_row_count": 10,
                        },
                    },
                )(),
            ):
                report = collect_sead_data(
                    output_root=output_root,
                    country_boundaries=self.country_boundaries,
                    bbox=(4.0, 54.0, 35.0, 72.0),
                )

            raw_payload = json.loads(report.raw_path.read_text(encoding="utf-8"))
            temporal_geojson_exists = (
                output_root / "normalized" / "nordic_temporal_evidence.geojson"
            ).exists()

        self.assertEqual(raw_payload["bbox"], [4.0, 54.0, 35.0, 72.0])
        self.assertEqual(raw_payload["inventory_summary"]["dataset_row_count"], 9)
        self.assertIn("tbl_analysis_dating_ranges", raw_payload["source_tables"])
        self.assertTrue(temporal_geojson_exists)

    def test_materialize_sead_repository_surfaces_rebuilds_review_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            (data_root / "sead" / "raw").mkdir(parents=True, exist_ok=True)
            (data_root / "boundaries" / "raw").mkdir(parents=True, exist_ok=True)
            (data_root / "sead" / "raw" / "nordic_sites.json").write_text(
                json.dumps(
                    {
                        "source": "SEAD",
                        "endpoint": "https://browser.sead.se/postgrest/tbl_sites",
                        "generated_on": "2026-05-09",
                        "row_count": 1,
                        "inventory_summary": {
                            "analysis_entity_row_count": 4,
                            "dataset_row_count": 9,
                        },
                        "rows": [
                            {
                                "site_id": 6468,
                                "site_name": "10412 Fjalkinge",
                                "national_site_identifier": "10412",
                                "latitude_dd": 56.05,
                                "longitude_dd": 14.28,
                                "altitude": 24,
                                "site_description": "",
                                "site_uuid": _SITE_UUID,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            for country in ("sweden", "denmark", "norway", "finland"):
                payload = (
                    self.country_boundaries["Sweden"]
                    if country == "sweden"
                    else {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": [
                                        [
                                            [0.0, 0.0],
                                            [1.0, 0.0],
                                            [1.0, 1.0],
                                            [0.0, 1.0],
                                            [0.0, 0.0],
                                        ]
                                    ],
                                },
                                "properties": {
                                    "ADM0_A3": {
                                        "denmark": "DNK",
                                        "norway": "NOR",
                                        "finland": "FIN",
                                    }[country]
                                },
                            }
                        ],
                    }
                )
                if country == "sweden":
                    sweden_features = cast(
                        list[dict[str, object]],
                        self.country_boundaries["Sweden"]["features"],
                    )
                    payload = {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "geometry": sweden_features[0]["geometry"],
                                "properties": {"ADM0_A3": "SWE"},
                            }
                        ],
                    }
                (data_root / "boundaries" / "raw" / f"{country}.geojson").write_text(
                    json.dumps(payload),
                    encoding="utf-8",
                )

            fixture_rows = json.loads(
                (data_root / "sead" / "raw" / "nordic_sites.json").read_text(
                    encoding="utf-8"
                )
            )["rows"]

            def write_claim_summary(_: object, path: Path) -> None:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}\n", encoding="utf-8")

            def write_classification_review(
                review_root: Path, _: object
            ) -> dict[str, Path]:
                review_root.mkdir(parents=True, exist_ok=True)
                paths = {
                    "json": review_root / "scientific_classification_review.json",
                    "markdown": review_root / "scientific_classification_review.md",
                    "csv": review_root / "scientific_classification_candidates.csv",
                }
                paths["json"].write_text('{"candidates": []}\n', encoding="utf-8")
                paths["markdown"].write_text("review\n", encoding="utf-8")
                paths["csv"].write_text("candidate_id\n", encoding="utf-8")
                return paths

            with (
                patch(
                    "bijux_pollenomics.collection.sources.sead.collection.repository_materialization.validate_governed_sead_admission",
                    return_value=SimpleNamespace(
                        admission={
                            "run_id": "sead-test-run",
                            "build_id": "sha256:" + "b" * 64,
                            "acquisition_manifest_sha256": "a" * 64,
                            "parent_admission_sha256": "p" * 64,
                        },
                        copied_files={
                            "receipts/tbl_sites.json": json.dumps(
                                {
                                    "run_id": "sead-test-run",
                                    "started_at": "2026-05-08T23:59:59Z",
                                }
                            ).encode()
                        },
                    ),
                ),
                patch(
                    "bijux_pollenomics.collection.sources.sead.collection.repository_materialization.load_sead_acquisition_rows",
                    return_value=[],
                ),
                patch(
                    "bijux_pollenomics.collection.sources.sead.collection.repository_materialization."
                    "build_sead_site_rows_from_acquisition_tables",
                    return_value=(fixture_rows, {}),
                ),
                patch(
                    "bijux_pollenomics.collection.sources.sead.collection.repository_materialization.attach_sead_country_decisions"
                ),
                patch(
                    "bijux_pollenomics.collection.sources.sead.collection.repository_materialization."
                    "write_sead_chronology_claim_bundle_from_snapshot",
                    side_effect=write_claim_summary,
                ),
                patch(
                    "bijux_pollenomics.collection.sources.sead.collection.repository_materialization."
                    "build_sead_scientific_classification_review",
                    return_value={},
                ) as classification_review,
                patch(
                    "bijux_pollenomics.collection.sources.sead.collection.repository_materialization."
                    "write_sead_scientific_classification_review",
                    side_effect=write_classification_review,
                ),
                patch(
                    "bijux_pollenomics.collection.sources.sead.collection.repository_materialization."
                    "require_source_snapshot_unchanged"
                ),
            ):
                with chdir(Path(tmp)):
                    report = materialize_sead_repository_surfaces(Path("data"))
                classification_review.assert_called_once_with(data_root.resolve())

            normalized_payload = json.loads(
                report.normalized_geojson_path.read_text(encoding="utf-8")
            )
            feature = normalized_payload["features"][0]
            evidence_review = json.loads(
                (
                    data_root / "sead" / "review" / "evidence_legibility_review.json"
                ).read_text(encoding="utf-8")
            )
            access_model = json.loads(
                (data_root / "sead" / "review" / "access_model.json").read_text(
                    encoding="utf-8"
                )
            )
            temporal_review = json.loads(
                (data_root / "sead" / "review" / "temporal_review.json").read_text(
                    encoding="utf-8"
                )
            )
            recovery_requirements = json.loads(
                (
                    data_root / "sead" / "review" / "recovery_requirements.json"
                ).read_text(encoding="utf-8")
            )
            temporal_geojson = json.loads(
                (
                    data_root
                    / "sead"
                    / "normalized"
                    / "nordic_temporal_evidence.geojson"
                ).read_text(encoding="utf-8")
            )

        self.assertEqual(report.point_count, 1)
        self.assertEqual(evidence_review["generated_on"], "2026-05-08")
        self.assertEqual(access_model["generated_on"], "2026-05-08")
        self.assertEqual(temporal_review["generated_on"], "2026-05-08")
        self.assertEqual(recovery_requirements["generated_on"], "2026-05-08")
        self.assertEqual(temporal_geojson["features"], [])
        self.assertEqual(feature["properties"]["country"], "Sweden")
        self.assertEqual(
            feature["properties"]["temporal_semantics"]["comparability_posture"],
            "unresolved",
        )
        self.assertEqual(
            evidence_review["normalization_risk_counts"]["high_thin_site_inventory"],
            1,
        )
        self.assertEqual(
            access_model["access_visibility_counts"]["site_page_only"],
            1,
        )
        self.assertEqual(
            temporal_review["inventory_summary"]["temporal_capture_posture"],
            "site_inventory_only",
        )
        self.assertEqual(
            temporal_review["inventory_summary"]["dating_range_row_count"],
            0,
        )
        self.assertEqual(
            temporal_review["inventory_summary"]["site_inventory_only_row_count"],
            1,
        )
        self.assertEqual(
            temporal_review["rows"][0]["raw_capture_posture"],
            "site_inventory_only",
        )
        self.assertEqual(
            recovery_requirements["schema_version"],
            "sead-recovery-requirements.v1",
        )
        self.assertEqual(
            recovery_requirements["rows"][0]["requirement_key"],
            "unresolved_chronology_boundary",
        )
        self.assertEqual(recovery_requirements["rows"][0]["evidence_gap_count"], 1)
        self.assertEqual(
            recovery_requirements["rows"][0]["affected_site_uuids"], [_SITE_UUID]
        )
        for payload in (
            evidence_review,
            access_model,
            temporal_review,
            recovery_requirements,
        ):
            lineage = payload["lineage"]
            self.assertEqual(lineage["source_run_id"], "sead-test-run")
            self.assertEqual(lineage["build_id"], "sha256:" + "b" * 64)
            self.assertEqual(lineage["acquisition_manifest_sha256"], "a" * 64)
            self.assertEqual(lineage["parent_admission_sha256"], "p" * 64)
        self.assertEqual(evidence_review["rows"][0]["site_uuid"], _SITE_UUID)
        self.assertEqual(access_model["rows"][0]["site_uuid"], _SITE_UUID)
        self.assertEqual(temporal_review["rows"][0]["site_uuid"], _SITE_UUID)
