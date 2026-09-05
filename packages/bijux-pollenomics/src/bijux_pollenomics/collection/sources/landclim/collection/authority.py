"""Governed source identity for LandClim raw receipts."""

from __future__ import annotations

LANDCLIM_ASSET_DATASET_IDS = {
    "marquer_2017_reveals_taxa_grid_cells.xlsx": "900966",
    "landclim_i_land_cover_types.xlsx": "897303",
    "landclim_i_plant_functional_types.xlsx": "897303",
    "landclim_ii_reveals_results.zip": "937075",
    "landclim_ii_grid_cell_quality.xlsx": "937075",
    "landclim_ii_contributors.xlsx": "937075",
    "landclim_ii_site_metadata.xlsx": "937075",
    "landclim_ii_taxa_pft_ppe_fsp_values.csv": "937075",
}

LANDCLIM_ASSET_SOURCE_URLS = {
    "marquer_2017_reveals_taxa_grid_cells.xlsx": (
        "https://store.pangaea.de/Publications/Marquer-etal_2017/MARQUER_QSR2017.xlsx"
    ),
    "landclim_i_land_cover_types.xlsx": (
        "https://store.pangaea.de/Publications/Gaillard-Lemdahl_2019/LandClimILCTs.xlsx"
    ),
    "landclim_i_plant_functional_types.xlsx": (
        "https://store.pangaea.de/Publications/Gaillard-Lemdahl_2019/LandClimIPFTs.xlsx"
    ),
    "landclim_ii_reveals_results.zip": (
        "https://download.pangaea.de/dataset/937075/files/"
        "LANDCLIMII.RV.results.JUN2021.zip"
    ),
    "landclim_ii_grid_cell_quality.xlsx": (
        "https://download.pangaea.de/dataset/937075/files/GC_quality_by_TW.xlsx"
    ),
    "landclim_ii_contributors.xlsx": (
        "https://download.pangaea.de/dataset/937075/files/LandClimII_contributors.xlsx"
    ),
    "landclim_ii_site_metadata.xlsx": (
        "https://download.pangaea.de/dataset/937075/files/LandClimII_metadata.xlsx"
    ),
    "landclim_ii_taxa_pft_ppe_fsp_values.csv": (
        "https://download.pangaea.de/dataset/937075/files/"
        "Taxa_to_PFT_PPE_and_FSP_values.csv"
    ),
}

LANDCLIM_ARCHIVE_FILENAME = "landclim_ii_reveals_results.zip"
LANDCLIM_REQUIRED_ASSETS = frozenset(
    set(LANDCLIM_ASSET_DATASET_IDS) - {"landclim_ii_contributors.xlsx"}
)
