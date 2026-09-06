from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bijux_pollenomics.collection.sources.landclim.collection import (
    build_landclim_raw_asset_summaries,
    download_landclim_raw_assets,
    resolve_landclim_marquer_asset_urls,
    resolve_landclim_tabular_asset_urls,
)


class LandClimRawAssetIoTests(unittest.TestCase):
    def test_resolve_landclim_asset_urls_reads_pangaea_record_formats(self) -> None:
        marquer_html = '<a id="static-download-link" href="https://store.pangaea.de/Publications/Marquer-etal_2017/MARQUER_QSR2017.xlsx">Download dataset</a>'
        self.assertEqual(
            resolve_landclim_marquer_asset_urls(marquer_html),
            {
                "marquer_2017_reveals_taxa_grid_cells.xlsx": "https://store.pangaea.de/Publications/Marquer-etal_2017/MARQUER_QSR2017.xlsx"
            },
        )

        landclim_i_text = """/* DATA DESCRIPTION: */\nContent\tFile name\tFile format\tFile size [kByte]\tURL file\nLCT\tLandClimILCTs\tXLSX\t216.697\thttps://store.pangaea.de/Publications/Gaillard-Lemdahl_2019/LandClimILCTs.xlsx\nPFT\tLandClimIPFTs\tXLSX\t344.248\thttps://store.pangaea.de/Publications/Gaillard-Lemdahl_2019/LandClimIPFTs.xlsx\n"""
        self.assertEqual(
            resolve_landclim_tabular_asset_urls(landclim_i_text),
            {
                "landclim_i_land_cover_types.xlsx": "https://store.pangaea.de/Publications/Gaillard-Lemdahl_2019/LandClimILCTs.xlsx",
                "landclim_i_plant_functional_types.xlsx": "https://store.pangaea.de/Publications/Gaillard-Lemdahl_2019/LandClimIPFTs.xlsx",
            },
        )

        landclim_ii_text = """/* DATA DESCRIPTION: */\nContent\tBinary\nREVEALS\tLANDCLIMII.RV.results.JUN2021.zip\nQuality\tGC_quality_by_TW.xlsx\nContributors\tLandClimII_contributors.xlsx\nMetadata\tLandClimII_metadata.xlsx\nTaxa\tTaxa_to_PFT_PPE_and_FSP_values.csv\n"""
        self.assertEqual(
            resolve_landclim_tabular_asset_urls(landclim_ii_text),
            {
                "landclim_ii_reveals_results.zip": "https://download.pangaea.de/dataset/937075/files/LANDCLIMII.RV.results.JUN2021.zip",
                "landclim_ii_grid_cell_quality.xlsx": "https://download.pangaea.de/dataset/937075/files/GC_quality_by_TW.xlsx",
                "landclim_ii_contributors.xlsx": "https://download.pangaea.de/dataset/937075/files/LandClimII_contributors.xlsx",
                "landclim_ii_site_metadata.xlsx": "https://download.pangaea.de/dataset/937075/files/LandClimII_metadata.xlsx",
                "landclim_ii_taxa_pft_ppe_fsp_values.csv": "https://download.pangaea.de/dataset/937075/files/Taxa_to_PFT_PPE_and_FSP_values.csv",
            },
        )

    def test_download_landclim_raw_assets_rejects_empty_payloads(self) -> None:
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch(
                "bijux_pollenomics.collection.sources.landclim.collection.resolve_landclim_asset_urls",
                return_value={
                    "landclim_i_land_cover_types.xlsx": "https://example.test/lct.xlsx"
                },
            ),
            patch(
                "bijux_pollenomics.collection.sources.landclim.collection.fetch_binary",
                return_value=b"",
            ),
            self.assertRaisesRegex(
                ValueError, "empty for landclim_i_land_cover_types.xlsx"
            ),
        ):
            download_landclim_raw_assets(Path(tmp))

    def test_build_landclim_raw_asset_summaries_records_source_urls_and_digests(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "landclim_i_land_cover_types.xlsx"
            path.write_bytes(b"landclim")

            summaries = build_landclim_raw_asset_summaries(
                {"landclim_i_land_cover_types.xlsx": path},
                {"landclim_i_land_cover_types.xlsx": "https://example.test/lct.xlsx"},
            )

        self.assertEqual(summaries[0]["source_url"], "https://example.test/lct.xlsx")
        self.assertEqual(summaries[0]["size_bytes"], 8)
        self.assertEqual(
            summaries[0]["sha256"],
            "f2865d4bfbd5fa4f19f5336385ef80d21ea03711c748736d3124f804dc1c2e14",
        )


if __name__ == "__main__":
    unittest.main()
