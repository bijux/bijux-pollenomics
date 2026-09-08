"""Immutable source identity and admitted OpenLand member vocabulary."""

ARCHIVE_SHA256 = "7ed602f3b480a995cd2e1ff6dc445e994442100b1f626a953185849305e2434b"
ARCHIVE_MEMBER_COUNT = 51
ARCHIVE_EXPANDED_BYTES = 204_016_242
MODELED_CELL_COUNT = 45_212
SOURCE_DATASET_ID = "spatiocompo-entire-holocene-eu-open-land"
SOURCE_REPOSITORY = "https://github.com/BehnazP/SpatioCompo_entireHolocene_EU"
SOURCE_COMMIT = "894d44d58f66bb5c273491d98c3ec23a35e6a796"
SOURCE_CITATION_DOI = "https://doi.org/10.3389/fevo.2022.795794"
SOURCE_DATA_LICENSE = "CC-BY-SA-4.0"
SOURCE_ATTRIBUTION = (
    "Behnaz Pirzamanbein; Pirzamanbein et al. (2022), doi:10.3389/fevo.2022.795794"
)
SOURCE_MODEL_KIND = "spatially_interpolated_compositional_land_cover_model"
SOURCE_SPATIAL_RESOLUTION_DEGREES = 1

# These are the source publication's temporal bins. The filename labels are not
# interval midpoints and therefore must never be expanded mechanically as ±250 BP.
SOURCE_WINDOWS_BP = (
    (50, 0, 100),
    (225, 100, 350),
    (550, 350, 700),
    (1000, 700, 1200),
    *((label, label - 300, label + 200) for label in range(1500, 11501, 500)),
)
SOURCE_TIME_SLICES_BP = tuple(label for label, _, _ in SOURCE_WINDOWS_BP)
SOURCE_INTERVAL_BY_SLICE_BP = {
    label: (younger_bp, older_bp) for label, younger_bp, older_bp in SOURCE_WINDOWS_BP
}

SOURCE_ROW_COUNT_BY_SLICE_BP = {
    **dict.fromkeys((50, 225, 550, 1000), 1859),
    **dict.fromkeys(range(1500, 9501, 500), 1863),
    10000: 1_440,
    **dict.fromkeys((10500, 11000, 11500), 1555),
}

_GRID_DIGEST_1859 = "fee4aa7e9af60ffcceeac707f8391c8da1260547fda299411f9a15836e3a6fb9"
_GRID_DIGEST_1863 = "27e695ba2b4c7a16a11feb5ec75fb095d451c4859a8ad8cdfd7af4f8f7ce9bca"
_GRID_DIGEST_1440 = "6acaf3ddc634978d844e957ac004b958b038f8fab5a9db2b441a89dd59d2e2db"
_GRID_DIGEST_1555 = "0c69d6d177c5a1def6bf7470a12f80a84eb5dec1b3b84360b4ad7e7f1de1b764"
SOURCE_GRID_SHA256_BY_SLICE_BP = {
    **dict.fromkeys((50, 225, 550, 1000), _GRID_DIGEST_1859),
    **dict.fromkeys(range(1500, 9501, 500), _GRID_DIGEST_1863),
    10000: _GRID_DIGEST_1440,
    **dict.fromkeys((10500, 11000, 11500), _GRID_DIGEST_1555),
}
CSV_HEADERS = (
    "Lon",
    "Lat",
    "C_KK10LonLatElev",
    "B_KK10LonLatElev",
    "U_KK10LonLatElev",
)


def csv_member_path(time_slice_bp: int) -> str:
    """Return the sole admitted archive member for a source time slice."""
    return f"LandCover_OpenLand/Data/Land_Cover_{time_slice_bp}.csv"


ADMITTED_CSV_MEMBERS = tuple(csv_member_path(age) for age in SOURCE_TIME_SLICES_BP)
