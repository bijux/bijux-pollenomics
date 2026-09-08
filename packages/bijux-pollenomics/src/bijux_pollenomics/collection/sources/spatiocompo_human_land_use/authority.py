"""Pinned source identity for the ten SpatioCompoMixed CSV exports."""

from __future__ import annotations

from .models import CategoricalPeriod, ExportFileAuthority, ModelVariant

SOURCE_REPOSITORY = "https://github.com/BehnazP/SpatioCompoMixed"
SOURCE_COMMIT = "ff8ed3c2365b54d319df29f8fc776b269b0273c3"
SOURCE_CITATION_DOI = "https://doi.org/10.1002/env.2743"
SOURCE_DATA_LICENSE = "CC-BY-SA-4.0"
SOURCE_ATTRIBUTION = (
    "Behnaz Pirzamanbein; Pirzamanbein and Lindström (2022), doi:10.1002/env.2743"
)
SOURCE_DIRECTORY = "Human land-use and Land cover Maps"
EXPECTED_ROWS_PER_SLICE = 679

SOURCE_PERIODS = (
    CategoricalPeriod("4000_bce", "4000 BCE", "BC4000", 0),
    CategoricalPeriod("1000_bce", "1000 BCE", "BC1000", 1),
    CategoricalPeriod("1425_ce", "1425 CE", "AD1425", 2),
    CategoricalPeriod("1725_ce", "1725 CE", "AD1725", 3),
    CategoricalPeriod("1900_ce", "1900 CE", "AD1900", 4),
)
MODEL_VARIANTS = (
    ModelVariant("all", "all", "elevation_and_lpj_guess_covariates"),
    ModelVariant("elevation", "elev", "elevation_only_covariates"),
)
_PERIOD_BY_KEY = {period.key: period for period in SOURCE_PERIODS}
_VARIANT_BY_KEY = {variant.key: variant for variant in MODEL_VARIANTS}


def expected_header(authority: ExportFileAuthority) -> tuple[str, ...]:
    prefix = f"{authority.variant.header_token}_{authority.period.header_token}"
    return (
        "Lon",
        "Lat",
        f"LCC_{prefix}_C",
        f"LCC_{prefix}_B",
        f"LCC_{prefix}_U",
        f"NLC_{prefix}_C",
        f"NLC_{prefix}_B",
        f"NLC_{prefix}_O",
        f"HLU_{prefix}",
    )


def _authority(
    filename: str,
    size_bytes: int,
    sha256: str,
    git_blob_sha: str,
    period_key: str,
    variant_key: str,
    *,
    upstream_status: str = "available",
    observed_valid_row_count: int = EXPECTED_ROWS_PER_SLICE,
    observed_malformed_row_count: int = 0,
) -> ExportFileAuthority:
    return ExportFileAuthority(
        relative_path=f"{SOURCE_DIRECTORY}/{filename}",
        size_bytes=size_bytes,
        sha256=sha256,
        git_blob_sha=git_blob_sha,
        period=_PERIOD_BY_KEY[period_key],
        variant=_VARIANT_BY_KEY[variant_key],
        upstream_status=upstream_status,
        observed_valid_row_count=observed_valid_row_count,
        observed_malformed_row_count=observed_malformed_row_count,
    )


FILE_AUTHORITIES = (
    _authority(
        "Human-land-use_land-cover-maps_all_4000BCE,.csv",
        80_803,
        "88343dcefda2d08187426444f42bf64d24265ed9e2ded58ab1d75b0838c3e469",
        "7521742b16c7f03d6d7f7562101f36ce95a17254",
        "4000_bce",
        "all",
    ),
    _authority(
        "Human-land-use_land-cover-maps_elevation_4000BCE,.csv",
        80_810,
        "a1dbda64d75d0680efc709085c8a7b3d9082e40d6eef53a150fc7adc0136b0fd",
        "aa02af757c12725c8f8fc2b34309fb6339a20f71",
        "4000_bce",
        "elevation",
    ),
    _authority(
        "Human-land-use_land-cover-maps_all_1000BCE,.csv",
        52_131,
        "4b61d5b0f3ec4dcab28dbe88294b8b0d2c391c000afd2e12555e5fc608e8c46c",
        "33f1faae61feba0fd59d2598cdcfbc62067536c3",
        "1000_bce",
        "all",
        upstream_status="known_corrupt_refused",
        observed_valid_row_count=437,
        observed_malformed_row_count=1,
    ),
    _authority(
        "Human-land-use_land-cover-maps_elevation_1000BCE,.csv",
        80_810,
        "ef13ffad624837606458caa31a26cea24240d7a3276266931ff70bdb2b467f02",
        "31da087620df9d359f8aa68003bffbc8f1e8348b",
        "1000_bce",
        "elevation",
    ),
    _authority(
        "Human-land-use_land-cover-maps_all_1425CE,.csv",
        80_803,
        "a882c02449114fdff510b12d1f998be6cc6c823524b4aae65956cde7184df867",
        "d907a74a15045d24feeecd22c848b03f02217050",
        "1425_ce",
        "all",
    ),
    _authority(
        "Human-land-use_land-cover-maps_elevation_1425CE,.csv",
        80_810,
        "af14cd52cff7b8da5ae22f9976d8b5cdb041fe99b11336aede9bb5f2a0ea451e",
        "537705a56a3efd87a84fcc3434eb1ac48de0fe46",
        "1425_ce",
        "elevation",
    ),
    _authority(
        "Human-land-use_land-cover-maps_all_1725CE,.csv",
        80_803,
        "b08b9f1496b198517a47c7c36f9d7214149659f8775678502288a90b26124114",
        "6b4cbf8d968456267bcb7cf220a114a95020a790",
        "1725_ce",
        "all",
    ),
    _authority(
        "Human-land-use_land-cover-maps_elevation_1725CE,.csv",
        80_810,
        "983ddb0a386957b6f1b317fad4b06e9852c03558c34455981804b57dd592f9b8",
        "6ec54e4c7dee49b7c6fa5e93b2f508a1deac3269",
        "1725_ce",
        "elevation",
    ),
    _authority(
        "Human-land-use_land-cover-maps_all_1900CE,.csv",
        80_803,
        "e60e428605c2ab16c020aa4a8449e6d04319e71ea7a7a416f2055367712c56f1",
        "3c88f87328d87ce818a49ac664cc4c696c54816d",
        "1900_ce",
        "all",
    ),
    _authority(
        "Human-land-use_land-cover-maps_elevation_1900CE,.csv",
        80_810,
        "e030f71b0ce285814847232c3553a41e3ec55fab1f90111c5ff2a7ddcfce2e53",
        "8c913775b5f94199727ee3b945a2d3917089d286",
        "1900_ce",
        "elevation",
    ),
)
KNOWN_REFUSED_RELATIVE_PATH = FILE_AUTHORITIES[2].relative_path


__all__ = [
    "EXPECTED_ROWS_PER_SLICE",
    "FILE_AUTHORITIES",
    "KNOWN_REFUSED_RELATIVE_PATH",
    "MODEL_VARIANTS",
    "SOURCE_ATTRIBUTION",
    "SOURCE_CITATION_DOI",
    "SOURCE_COMMIT",
    "SOURCE_DATA_LICENSE",
    "SOURCE_DIRECTORY",
    "SOURCE_PERIODS",
    "SOURCE_REPOSITORY",
    "expected_header",
]
