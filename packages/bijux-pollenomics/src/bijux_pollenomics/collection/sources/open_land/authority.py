"""Immutable source identity and admitted OpenLand member vocabulary."""

ARCHIVE_SHA256 = "7ed602f3b480a995cd2e1ff6dc445e994442100b1f626a953185849305e2434b"
ARCHIVE_MEMBER_COUNT = 51
ARCHIVE_EXPANDED_BYTES = 204_016_242
MODELED_CELL_COUNT = 45_212
SOURCE_REPOSITORY = "https://github.com/BehnazP/SpatioCompo_entireHolocene_EU"
SOURCE_COMMIT = "894d44d58f66bb5c273491d98c3ec23a35e6a796"
SOURCE_CITATION_DOI = "https://doi.org/10.3389/fevo.2022.795794"
SOURCE_DATA_LICENSE = "CC-BY-SA-4.0"
SOURCE_TIME_SLICES_BP = (
    50,
    225,
    550,
    1000,
    1500,
    2000,
    2500,
    3000,
    3500,
    4000,
    4500,
    5000,
    5500,
    6000,
    6500,
    7000,
    7500,
    8000,
    8500,
    9000,
    9500,
    10000,
    10500,
    11000,
    11500,
)
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
