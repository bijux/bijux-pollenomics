"""Pinned PANGAEA 937075 presentation vocabulary and source windows."""

from __future__ import annotations

from typing import Final

LANDCLIM_TEMPORAL_LAYER_KEY: Final = "landclim-reveals-temporal-grid"
PANGAEA_DATASET_ID: Final = "937075"
PANGAEA_DATASET_DOI: Final = "https://doi.org/10.1594/PANGAEA.937075"
GITHUMBI_METHOD_DOI: Final = "https://doi.org/10.5194/essd-14-1581-2022"
GITHUMBI_CITATION: Final = (
    "Githumbi et al. (2022), European pollen-based REVEALS land-cover "
    "reconstructions for the Holocene"
)
OPEN_LAND_METRIC_KEY: Final = "OL"
OPEN_LAND_METRIC_LABEL: Final = "Open land"
OPEN_LAND_VALUE_UNIT: Final = "percentage_cover"

# The source publishes these discrete estimates. Their adjacency does not authorize
# interpolation or conversion into a continuous chronology.
PANGAEA_WINDOWS_PRESENT_TO_OLDEST: Final = (
    ("0-100 BP", 0, 100),
    ("100-350 BP", 100, 350),
    ("350-700 BP", 350, 700),
    ("700-1200 BP", 700, 1200),
    ("1200-1700 BP", 1200, 1700),
    ("1700-2200 BP", 1700, 2200),
    ("2200-2700 BP", 2200, 2700),
    ("2700-3200 BP", 2700, 3200),
    ("3200-3700 BP", 3200, 3700),
    ("3700-4200 BP", 3700, 4200),
    ("4200-4700 BP", 4200, 4700),
    ("4700-5200 BP", 4700, 5200),
    ("5200-5700 BP", 5200, 5700),
    ("5700-6200 BP", 5700, 6200),
    ("6200-6700 BP", 6200, 6700),
    ("6700-7200 BP", 6700, 7200),
    ("7200-7700 BP", 7200, 7700),
    ("7700-8200 BP", 7700, 8200),
    ("8200-8700 BP", 8200, 8700),
    ("8700-9200 BP", 8700, 9200),
    ("9200-9700 BP", 9200, 9700),
    ("9700-10200 BP", 9700, 10200),
    ("10200-10700 BP", 10200, 10700),
    ("10700-11200 BP", 10700, 11200),
    ("11200-11700 BP", 11200, 11700),
)

PANGAEA_COUNTRY_CELL_COUNTS: Final = {
    "Denmark": 6,
    "Finland": 19,
    "Norway": 24,
    "Sweden": 26,
}

# Sequential, color-blind-friendly bins for percentage cover. The upper bound is
# inclusive; null and refused values never receive a modeled color.
OPEN_LAND_PALETTE: Final = (
    (20, "#1b4332"),
    (40, "#52796f"),
    (60, "#a7c957"),
    (80, "#f2cc8f"),
    (100, "#d97706"),
)

__all__ = [
    "GITHUMBI_CITATION",
    "GITHUMBI_METHOD_DOI",
    "LANDCLIM_TEMPORAL_LAYER_KEY",
    "OPEN_LAND_METRIC_KEY",
    "OPEN_LAND_METRIC_LABEL",
    "OPEN_LAND_PALETTE",
    "OPEN_LAND_VALUE_UNIT",
    "PANGAEA_COUNTRY_CELL_COUNTS",
    "PANGAEA_DATASET_DOI",
    "PANGAEA_DATASET_ID",
    "PANGAEA_WINDOWS_PRESENT_TO_OLDEST",
]
