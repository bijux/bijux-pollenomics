from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.data_downloader.repository_snapshot import (
    build_repository_collection_summary,
    build_repository_source_counts,
)


class RepositorySnapshotUnitTests(unittest.TestCase):
    def test_build_repository_source_counts_reads_existing_normalized_surfaces(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            (output_root / "aadr" / "v66").mkdir(parents=True, exist_ok=True)
            (output_root / "aadr" / "v66" / "release_manifest.json").write_text(
                "{}",
                encoding="utf-8",
            )
            (output_root / "landclim" / "normalized").mkdir(parents=True, exist_ok=True)
            (
                output_root / "landclim" / "normalized" / "landclim_summary.json"
            ).write_text(
                json.dumps({"site_count": 4, "grid_cell_count": 7}),
                encoding="utf-8",
            )
            (output_root / "neotoma" / "normalized").mkdir(parents=True, exist_ok=True)
            (
                output_root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson"
            ).write_text(
                json.dumps({"features": [{}, {}]}),
                encoding="utf-8",
            )
            (output_root / "sead" / "normalized").mkdir(parents=True, exist_ok=True)
            (
                output_root
                / "sead"
                / "normalized"
                / "nordic_environmental_sites.geojson"
            ).write_text(
                json.dumps({"features": [{}, {}, {}]}),
                encoding="utf-8",
            )
            (output_root / "raa" / "normalized").mkdir(parents=True, exist_ok=True)
            (
                output_root / "raa" / "normalized" / "sweden_archaeology_layer.json"
            ).write_text(
                json.dumps({"counts": {"all_published_sites": 11, "fornlamning": 5}}),
                encoding="utf-8",
            )

            counts = build_repository_source_counts(output_root)

        self.assertEqual(counts["aadr_file_count"], 1)
        self.assertEqual(counts["landclim_site_count"], 4)
        self.assertEqual(counts["landclim_grid_cell_count"], 7)
        self.assertEqual(counts["neotoma_point_count"], 2)
        self.assertEqual(counts["sead_point_count"], 3)
        self.assertEqual(counts["raa_total_site_count"], 11)
        self.assertEqual(counts["raa_heritage_site_count"], 5)

    def test_build_repository_collection_summary_adds_contract_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            for relative_path in (
                "aadr/v66/release_manifest.json",
                "boundaries/raw/sweden.geojson",
                "boundaries/raw/denmark.geojson",
                "boundaries/raw/norway.geojson",
                "boundaries/raw/finland.geojson",
                "boundaries/normalized/nordic_country_boundaries.geojson",
                "landclim/raw/landclim_sources.json",
                "landclim/normalized/landclim_summary.json",
                "landclim/normalized/nordic_pollen_site_sequences.geojson",
                "landclim/normalized/nordic_reveals_grid_cells.geojson",
                "neotoma/raw/neotoma_pollen_sites.json",
                "neotoma/normalized/nordic_pollen_sites.geojson",
                "raa/raw/fornsok_domains.json",
                "raa/normalized/sweden_archaeology_layer.json",
                "sead/raw/nordic_sites.json",
                "sead/normalized/nordic_environmental_sites.geojson",
                "adna/governance/source_library/project_registry.json",
                "adna/governance/animal_sample_foundation_truth.json",
                "adna/species/homo_sapiens/normalized/placeholder.json",
                "adna/species/homo_sapiens/review/placeholder.json",
                "adna/species/equus_caballus/normalized/sample_records.json",
                "adna/final/atlas/animal_atlas_point_candidates.json",
            ):
                path = output_root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.name == "landclim_summary.json":
                    path.write_text(
                        json.dumps({"site_count": 1, "grid_cell_count": 1}),
                        encoding="utf-8",
                    )
                elif path.suffix == ".geojson":
                    path.write_text(json.dumps({"features": []}), encoding="utf-8")
                elif path.name == "sweden_archaeology_layer.json":
                    path.write_text(
                        json.dumps(
                            {"counts": {"all_published_sites": 1, "fornlamning": 1}}
                        ),
                        encoding="utf-8",
                    )
                else:
                    path.write_text("{}", encoding="utf-8")

            summary = build_repository_collection_summary(output_root, version="v66")

        self.assertIn("source_family_contracts", summary.contract_artifacts)
        self.assertTrue(summary.source_family_state_rows)


if __name__ == "__main__":
    unittest.main()
