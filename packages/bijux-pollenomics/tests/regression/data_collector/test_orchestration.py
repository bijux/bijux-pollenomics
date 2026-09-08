"""Regression coverage for data-collector orchestration."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pytest

from bijux_pollenomics.collection.workflow.collection import (
    AVAILABLE_SOURCES,
    build_staging_output_dir,
    collect_data,
)

pytestmark = pytest.mark.generated_artifacts


class CollectionOrchestrationTests(unittest.TestCase):
    def test_collect_data_runs_only_requested_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"

            with (
                patch(
                    "bijux_pollenomics.collection.workflow.collection.download_aadr_anno_files"
                ) as download_aadr,
                patch(
                    "bijux_pollenomics.collection.workflow.collection.fetch_country_boundaries"
                ) as fetch_boundaries,
                patch(
                    "bijux_pollenomics.collection.workflow.collection.collect_boundaries_data"
                ) as collect_boundaries,
                patch(
                    "bijux_pollenomics.collection.workflow.collection.collect_landclim_data"
                ) as collect_landclim,
                patch(
                    "bijux_pollenomics.collection.workflow.collection.collect_neotoma_data"
                ) as collect_neotoma,
                patch(
                    "bijux_pollenomics.collection.workflow.collection.collect_sead_data"
                ) as collect_sead,
                patch(
                    "bijux_pollenomics.collection.workflow.collection.collect_raa_data"
                ) as collect_raa,
                patch(
                    "bijux_pollenomics.collection.workflow.collection.collect_svar_data"
                ) as collect_svar,
                patch(
                    "socket.socket.connect",
                    side_effect=AssertionError(
                        "Orchestration tests must remain offline"
                    ),
                ),
            ):
                download_aadr.return_value.downloaded_files = (Path("a"), Path("b"))
                fetch_boundaries.return_value = {"Sweden": {"features": []}}
                collect_landclim.return_value.site_count = 4
                collect_landclim.return_value.grid_cell_count = 2
                collect_neotoma.return_value.point_count = 6
                collect_sead.return_value.point_count = 1937
                collect_raa.return_value.total_site_count = 761786
                collect_raa.return_value.heritage_site_count = 318230

                report = collect_data(
                    output_root=output_root, sources=("aadr", "raa"), version="v62.0"
                )

            self.assertEqual(report.collected_sources, ("aadr", "raa"))
            download_aadr.assert_called_once_with(
                output_root=build_staging_output_dir(output_root / "aadr"),
                version="v62.0",
            )
            fetch_boundaries.assert_called_once()
            collect_boundaries.assert_not_called()
            collect_landclim.assert_not_called()
            collect_neotoma.assert_not_called()
            collect_sead.assert_not_called()
            collect_svar.assert_not_called()
            collect_raa.assert_called_once_with(
                output_root=build_staging_output_dir(output_root / "raa"),
                country_boundaries={"Sweden": {"features": []}},
            )
            self.assertTrue((output_root / "README.md").exists())
            self.assertTrue((output_root / "source_family_contracts.json").is_file())
            self.assertTrue(
                (output_root / "source_family_evidence_stage_matrix.json").is_file()
            )
            self.assertTrue(
                (output_root / "source_fact_ownership_registry.json").is_file()
            )
            self.assertTrue(
                (output_root / "evidence_artifact_contracts.json").is_file()
            )
            self.assertTrue(
                (
                    output_root / "adna" / "species" / "equus_caballus" / "review"
                ).is_dir()
            )
            self.assertTrue(
                (output_root / "adna" / "species" / "bos_taurus" / "manifests").is_dir()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "species"
                    / "equus_caballus"
                    / "manifests"
                    / "curation_manifest.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "species"
                    / "equus_caballus"
                    / "review"
                    / "species_review.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "species"
                    / "equus_caballus"
                    / "raw"
                    / "source_snapshot.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "species"
                    / "equus_caballus"
                    / "normalized"
                    / "sample_records.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "species"
                    / "equus_caballus"
                    / "normalized"
                    / "coordinate_provenance.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "species"
                    / "equus_caballus"
                    / "normalized"
                    / "site_evidence.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "species"
                    / "equus_caballus"
                    / "normalized"
                    / "project_summaries.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "species"
                    / "equus_caballus"
                    / "normalized"
                    / "locality_summaries.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "cross_species_bibliography.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "cross_species_archive_inventory.csv"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "cross_species_coverage_dashboard.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "cross_species_map_readiness.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root / "adna" / "governance" / "coordinate_caveat_surface.md"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "coordinate_confidence_scale.md"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root / "adna" / "governance" / "shipped_product_audit.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root / "adna" / "governance" / "surface_role_registry.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "project_registry.json"
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
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "governance"
                    / "source_library"
                    / "projects"
                    / "PRJEB22390"
                    / "bundle_manifest.json"
                ).is_file()
            )
            self.assertEqual(report.boundary_source, "network")
            self.assertTrue(report.summary_path.exists())
            self.assertIn("aadr", report.source_provenance)
            self.assertIn("raa", report.source_provenance)
            self.assertEqual(report.source_provenance["aadr"].version, "v62.0")
            self.assertTrue(report.source_replacement_rules["aadr"].destructive_refresh)
            self.assertTrue(
                report.source_replacement_rules["raa"].preserves_previous_on_failure
            )
            self.assertEqual(report.source_traceability["aadr"].source_version, "v62.0")
            self.assertIn("source_family_contracts", report.contract_artifacts)
            self.assertTrue(report.source_family_state_rows)
            self.assertTrue(
                report.source_traceability["aadr"].dispute_token.startswith(
                    "aadr@v62.0:"
                )
            )

    def test_collect_data_all_collects_everything(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"

            with (
                patch(
                    "bijux_pollenomics.collection.workflow.collection.download_aadr_anno_files"
                ) as download_aadr,
                patch(
                    "bijux_pollenomics.collection.workflow.collection.collect_boundaries_data"
                ) as collect_boundaries,
                patch(
                    "bijux_pollenomics.collection.workflow.collection.collect_landclim_data"
                ) as collect_landclim,
                patch(
                    "bijux_pollenomics.collection.workflow.collection.collect_neotoma_data"
                ) as collect_neotoma,
                patch(
                    "bijux_pollenomics.collection.workflow.collection.collect_sead_data"
                ) as collect_sead,
                patch(
                    "bijux_pollenomics.collection.workflow.collection.collect_raa_data"
                ) as collect_raa,
                patch(
                    "bijux_pollenomics.collection.workflow.collection.collect_svar_data"
                ) as collect_svar,
                patch(
                    "socket.socket.connect",
                    side_effect=AssertionError(
                        "Orchestration tests must remain offline"
                    ),
                ),
            ):
                download_aadr.return_value.downloaded_files = (Path("a"), Path("b"))
                collect_boundaries.return_value = (
                    {"Sweden": {"features": []}},
                    object(),
                )
                collect_landclim.return_value.site_count = 4
                collect_landclim.return_value.grid_cell_count = 2
                collect_neotoma.return_value.point_count = 6
                collect_sead.return_value.point_count = 1937
                collect_raa.return_value.total_site_count = 761786
                collect_raa.return_value.heritage_site_count = 318230
                collect_svar.return_value.lake_count = 7

                report = collect_data(
                    output_root=output_root, sources=("all",), version="v62.0"
                )

            self.assertEqual(report.collected_sources, AVAILABLE_SOURCES)
            download_aadr.assert_called_once()
            collect_boundaries.assert_called_once_with(
                build_staging_output_dir(output_root / "boundaries")
            )
            collect_landclim.assert_called_once()
            collect_neotoma.assert_called_once()
            collect_sead.assert_called_once()
            collect_raa.assert_called_once()
            collect_svar.assert_called_once_with(
                output_root=build_staging_output_dir(output_root / "svar"),
                country_boundaries={"Sweden": {"features": []}},
            )
            self.assertEqual(report.svar_lake_count, 7)
            self.assertEqual(report.boundary_source, "collected")
            self.assertTrue(
                (output_root / "adna" / "species" / "equus_asinus" / "raw").is_dir()
            )
            self.assertTrue(
                (
                    output_root
                    / "adna"
                    / "species"
                    / "equus_asinus"
                    / "raw"
                    / "archive_inventory.json"
                ).is_file()
            )
