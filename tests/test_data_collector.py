from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bijux_pollen.data_downloader.collector import AVAILABLE_SOURCES, collect_data, normalize_requested_sources


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

            with patch("bijux_pollen.data_downloader.collector.download_aadr_anno_files") as download_aadr, \
                patch("bijux_pollen.data_downloader.collector.fetch_country_boundaries") as fetch_boundaries, \
                patch("bijux_pollen.data_downloader.collector.collect_boundaries_data") as collect_boundaries, \
                patch("bijux_pollen.data_downloader.collector.collect_neotoma_data") as collect_neotoma, \
                patch("bijux_pollen.data_downloader.collector.collect_sead_data") as collect_sead, \
                patch("bijux_pollen.data_downloader.collector.collect_raa_data") as collect_raa:
                download_aadr.return_value.downloaded_files = (Path("a"), Path("b"))
                fetch_boundaries.return_value = {"Sweden": {"features": []}}
                collect_neotoma.return_value.point_count = 6
                collect_sead.return_value.point_count = 1937
                collect_raa.return_value.total_site_count = 761786
                collect_raa.return_value.heritage_site_count = 318230

                report = collect_data(output_root=output_root, sources=("aadr", "raa"), version="v62.0")

            self.assertEqual(report.collected_sources, ("aadr", "raa"))
            download_aadr.assert_called_once_with(output_root=output_root / "aadr", version="v62.0")
            fetch_boundaries.assert_called_once()
            collect_boundaries.assert_not_called()
            collect_neotoma.assert_not_called()
            collect_sead.assert_not_called()
            collect_raa.assert_called_once_with(
                output_root=output_root / "raa",
                country_boundaries={"Sweden": {"features": []}},
            )
            self.assertTrue((output_root / "README.md").exists())

    def test_collect_data_all_collects_everything(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"

            with patch("bijux_pollen.data_downloader.collector.download_aadr_anno_files") as download_aadr, \
                patch("bijux_pollen.data_downloader.collector.collect_boundaries_data") as collect_boundaries, \
                patch("bijux_pollen.data_downloader.collector.collect_neotoma_data") as collect_neotoma, \
                patch("bijux_pollen.data_downloader.collector.collect_sead_data") as collect_sead, \
                patch("bijux_pollen.data_downloader.collector.collect_raa_data") as collect_raa:
                download_aadr.return_value.downloaded_files = (Path("a"), Path("b"))
                collect_boundaries.return_value = ({"Sweden": {"features": []}}, object())
                collect_neotoma.return_value.point_count = 6
                collect_sead.return_value.point_count = 1937
                collect_raa.return_value.total_site_count = 761786
                collect_raa.return_value.heritage_site_count = 318230

                report = collect_data(output_root=output_root, sources=("all",), version="v62.0")

            self.assertEqual(report.collected_sources, AVAILABLE_SOURCES)
            download_aadr.assert_called_once()
            collect_boundaries.assert_called_once_with(output_root / "boundaries")
            collect_neotoma.assert_called_once()
            collect_sead.assert_called_once()
            collect_raa.assert_called_once()


if __name__ == "__main__":
    unittest.main()
