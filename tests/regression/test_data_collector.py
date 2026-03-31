from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import json
from unittest.mock import patch

from bijux_pollenomics.data_downloader.collector import (
    AVAILABLE_SOURCES,
    build_staging_output_dir,
    collect_data,
    normalize_requested_sources,
)


class DataCollectorTests(unittest.TestCase):
    def test_normalize_requested_sources_expands_all(self) -> None:
        self.assertEqual(normalize_requested_sources(["all"]), AVAILABLE_SOURCES)

    def test_normalize_requested_sources_deduplicates_preserving_order(self) -> None:
        self.assertEqual(
            normalize_requested_sources(["raa", "aadr", "raa"]),
            ("raa", "aadr"),
        )

    def test_collect_data_runs_only_requested_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"

            with patch("bijux_pollenomics.data_downloader.collector.download_aadr_anno_files") as download_aadr, \
                patch("bijux_pollenomics.data_downloader.collector.fetch_country_boundaries") as fetch_boundaries, \
                patch("bijux_pollenomics.data_downloader.collector.collect_boundaries_data") as collect_boundaries, \
                patch("bijux_pollenomics.data_downloader.collector.collect_landclim_data") as collect_landclim, \
                patch("bijux_pollenomics.data_downloader.collector.collect_neotoma_data") as collect_neotoma, \
                patch("bijux_pollenomics.data_downloader.collector.collect_sead_data") as collect_sead, \
                patch("bijux_pollenomics.data_downloader.collector.collect_raa_data") as collect_raa:
                download_aadr.return_value.downloaded_files = (Path("a"), Path("b"))
                fetch_boundaries.return_value = {"Sweden": {"features": []}}
                collect_landclim.return_value.site_count = 4
                collect_landclim.return_value.grid_cell_count = 2
                collect_neotoma.return_value.point_count = 6
                collect_sead.return_value.point_count = 1937
                collect_raa.return_value.total_site_count = 761786
                collect_raa.return_value.heritage_site_count = 318230

                report = collect_data(output_root=output_root, sources=("aadr", "raa"), version="v62.0")

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
            collect_raa.assert_called_once_with(
                output_root=build_staging_output_dir(output_root / "raa"),
                country_boundaries={"Sweden": {"features": []}},
            )
            self.assertTrue((output_root / "README.md").exists())
            self.assertEqual(report.boundary_source, "network")
            self.assertTrue(report.summary_path.exists())

    def test_collect_data_all_collects_everything(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"

            with patch("bijux_pollenomics.data_downloader.collector.download_aadr_anno_files") as download_aadr, \
                patch("bijux_pollenomics.data_downloader.collector.collect_boundaries_data") as collect_boundaries, \
                patch("bijux_pollenomics.data_downloader.collector.collect_landclim_data") as collect_landclim, \
                patch("bijux_pollenomics.data_downloader.collector.collect_neotoma_data") as collect_neotoma, \
                patch("bijux_pollenomics.data_downloader.collector.collect_sead_data") as collect_sead, \
                patch("bijux_pollenomics.data_downloader.collector.collect_raa_data") as collect_raa:
                download_aadr.return_value.downloaded_files = (Path("a"), Path("b"))
                collect_boundaries.return_value = ({"Sweden": {"features": []}}, object())
                collect_landclim.return_value.site_count = 4
                collect_landclim.return_value.grid_cell_count = 2
                collect_neotoma.return_value.point_count = 6
                collect_sead.return_value.point_count = 1937
                collect_raa.return_value.total_site_count = 761786
                collect_raa.return_value.heritage_site_count = 318230

                report = collect_data(output_root=output_root, sources=("all",), version="v62.0")

            self.assertEqual(report.collected_sources, AVAILABLE_SOURCES)
            download_aadr.assert_called_once()
            collect_boundaries.assert_called_once_with(build_staging_output_dir(output_root / "boundaries"))
            collect_landclim.assert_called_once()
            collect_neotoma.assert_called_once()
            collect_sead.assert_called_once()
            collect_raa.assert_called_once()
            self.assertEqual(report.boundary_source, "collected")

    def test_collect_data_replaces_selected_source_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "custom-data"
            stale_file = output_root / "neotoma" / "stale.txt"
            stale_file.parent.mkdir(parents=True, exist_ok=True)
            stale_file.write_text("stale", encoding="utf-8")

            with patch("bijux_pollenomics.data_downloader.collector.fetch_country_boundaries") as fetch_boundaries, \
                patch("bijux_pollenomics.data_downloader.collector.collect_neotoma_data") as collect_neotoma:
                fetch_boundaries.return_value = {"Sweden": {"features": []}}

                def write_fresh_dataset(*, output_root: Path, country_boundaries: dict[str, object], bbox: tuple[float, ...]):
                    normalized_dir = output_root / "normalized"
                    normalized_dir.mkdir(parents=True, exist_ok=True)
                    (normalized_dir / "fresh.csv").write_text("fresh", encoding="utf-8")
                    class Report:
                        point_count = 1
                    return Report()

                collect_neotoma.side_effect = write_fresh_dataset
                collect_data(output_root=output_root, sources=("neotoma",), version="v62.0")

            self.assertFalse(stale_file.exists())
            self.assertTrue((output_root / "neotoma" / "normalized" / "fresh.csv").exists())

    def test_collect_data_preserves_previous_source_dir_when_recollection_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            preserved_file = output_root / "neotoma" / "normalized" / "kept.csv"
            preserved_file.parent.mkdir(parents=True, exist_ok=True)
            preserved_file.write_text("kept", encoding="utf-8")

            with patch("bijux_pollenomics.data_downloader.collector.fetch_country_boundaries") as fetch_boundaries, \
                patch("bijux_pollenomics.data_downloader.collector.collect_neotoma_data") as collect_neotoma:
                fetch_boundaries.return_value = {"Sweden": {"features": []}}

                def fail_after_partial_write(*, output_root: Path, country_boundaries: dict[str, object], bbox: tuple[float, ...]):
                    normalized_dir = output_root / "normalized"
                    normalized_dir.mkdir(parents=True, exist_ok=True)
                    (normalized_dir / "partial.csv").write_text("partial", encoding="utf-8")
                    raise RuntimeError("upstream failure")

                collect_neotoma.side_effect = fail_after_partial_write
                with self.assertRaisesRegex(RuntimeError, "upstream failure"):
                    collect_data(output_root=output_root, sources=("neotoma",), version="v62.0")

            self.assertTrue(preserved_file.exists())
            self.assertFalse((output_root / ".neotoma.tmp").exists())

    def test_collect_data_writes_output_root_specific_readme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "custom-data"

            with patch("bijux_pollenomics.data_downloader.collector.download_aadr_anno_files") as download_aadr:
                download_aadr.return_value.downloaded_files = ()
                collect_data(output_root=output_root, sources=("aadr",), version="v62.0")

            readme_text = (output_root / "README.md").read_text(encoding="utf-8")
            self.assertIn("Tracked source data lives directly under `custom-data/`", readme_text)
            self.assertIn("\ncustom-data\n", readme_text)
            self.assertIn("│   └── v62.0", readme_text)
            summary = json.loads((output_root / "collection_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["collected_sources"], ["aadr"])
            self.assertEqual(summary["source_output_roots"]["aadr"], str(output_root / "aadr"))
            self.assertEqual(summary["source_output_roots"]["aadr_version_dir"], str(output_root / "aadr" / "v62.0"))
            self.assertIsNone(summary["boundary_source"])
            self.assertEqual(summary["landclim_site_count"], 0)
            self.assertEqual(summary["landclim_grid_cell_count"], 0)

    def test_collect_data_uses_local_boundaries_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            raw_dir = output_root / "boundaries" / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            boundary_payload = {"type": "FeatureCollection", "features": []}
            for filename in ("sweden.geojson", "norway.geojson", "finland.geojson", "denmark.geojson"):
                (raw_dir / filename).write_text(json.dumps(boundary_payload), encoding="utf-8")

            with patch("bijux_pollenomics.data_downloader.collector.fetch_country_boundaries") as fetch_boundaries, \
                patch("bijux_pollenomics.data_downloader.collector.collect_neotoma_data") as collect_neotoma:
                collect_neotoma.return_value.point_count = 6
                report = collect_data(output_root=output_root, sources=("neotoma",), version="v62.0")

            fetch_boundaries.assert_not_called()
            collect_neotoma.assert_called_once()
            self.assertEqual(report.boundary_source, "local")

    def test_collect_data_rejects_invalid_local_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            raw_dir = output_root / "boundaries" / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            invalid_payload = {"type": "Polygon"}
            for filename in ("sweden.geojson", "norway.geojson", "finland.geojson", "denmark.geojson"):
                (raw_dir / filename).write_text(json.dumps(invalid_payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "FeatureCollection"):
                collect_data(output_root=output_root, sources=("neotoma",), version="v62.0")

    def test_collect_data_collects_landclim_with_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"

            with patch("bijux_pollenomics.data_downloader.collector.fetch_country_boundaries") as fetch_boundaries, \
                patch("bijux_pollenomics.data_downloader.collector.collect_landclim_data") as collect_landclim:
                fetch_boundaries.return_value = {"Sweden": {"features": []}}
                collect_landclim.return_value.site_count = 11
                collect_landclim.return_value.grid_cell_count = 7

                report = collect_data(output_root=output_root, sources=("landclim",), version="v62.0")

            fetch_boundaries.assert_called_once()
            collect_landclim.assert_called_once_with(
                output_root=build_staging_output_dir(output_root / "landclim"),
                country_boundaries={"Sweden": {"features": []}},
                bbox=(4.0, 54.0, 35.0, 72.0),
            )
            self.assertEqual(report.landclim_site_count, 11)
            self.assertEqual(report.landclim_grid_cell_count, 7)


if __name__ == "__main__":
    unittest.main()
