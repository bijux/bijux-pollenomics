from __future__ import annotations

from bijux_pollenomics.collection.sources.spatiocompo_human_land_use.authority import (
    FILE_AUTHORITIES,
    MODEL_VARIANTS,
    SOURCE_COMMIT,
    SOURCE_DATA_LICENSE,
    SOURCE_PERIODS,
    SOURCE_REPOSITORY,
)


def test_source_identity_period_order_and_variants_are_immutable() -> None:
    assert SOURCE_REPOSITORY == "https://github.com/BehnazP/SpatioCompoMixed"
    assert SOURCE_COMMIT == "ff8ed3c2365b54d319df29f8fc776b269b0273c3"
    assert SOURCE_DATA_LICENSE == "CC-BY-SA-4.0"
    assert [period.label for period in SOURCE_PERIODS] == [
        "4000 BCE",
        "1000 BCE",
        "1425 CE",
        "1725 CE",
        "1900 CE",
    ]
    assert [(variant.key, variant.covariate_posture) for variant in MODEL_VARIANTS] == [
        ("all", "elevation_and_lpj_guess_covariates"),
        ("elevation", "elevation_only_covariates"),
    ]


def test_exact_upstream_file_digests_are_pinned() -> None:
    assert {
        authority.relative_path: authority.sha256 for authority in FILE_AUTHORITIES
    } == {
        "Human land-use and Land cover Maps/Human-land-use_land-cover-maps_all_4000BCE,.csv": "88343dcefda2d08187426444f42bf64d24265ed9e2ded58ab1d75b0838c3e469",
        "Human land-use and Land cover Maps/Human-land-use_land-cover-maps_elevation_4000BCE,.csv": "a1dbda64d75d0680efc709085c8a7b3d9082e40d6eef53a150fc7adc0136b0fd",
        "Human land-use and Land cover Maps/Human-land-use_land-cover-maps_all_1000BCE,.csv": "4b61d5b0f3ec4dcab28dbe88294b8b0d2c391c000afd2e12555e5fc608e8c46c",
        "Human land-use and Land cover Maps/Human-land-use_land-cover-maps_elevation_1000BCE,.csv": "ef13ffad624837606458caa31a26cea24240d7a3276266931ff70bdb2b467f02",
        "Human land-use and Land cover Maps/Human-land-use_land-cover-maps_all_1425CE,.csv": "a882c02449114fdff510b12d1f998be6cc6c823524b4aae65956cde7184df867",
        "Human land-use and Land cover Maps/Human-land-use_land-cover-maps_elevation_1425CE,.csv": "af14cd52cff7b8da5ae22f9976d8b5cdb041fe99b11336aede9bb5f2a0ea451e",
        "Human land-use and Land cover Maps/Human-land-use_land-cover-maps_all_1725CE,.csv": "b08b9f1496b198517a47c7c36f9d7214149659f8775678502288a90b26124114",
        "Human land-use and Land cover Maps/Human-land-use_land-cover-maps_elevation_1725CE,.csv": "983ddb0a386957b6f1b317fad4b06e9852c03558c34455981804b57dd592f9b8",
        "Human land-use and Land cover Maps/Human-land-use_land-cover-maps_all_1900CE,.csv": "e60e428605c2ab16c020aa4a8449e6d04319e71ea7a7a416f2055367712c56f1",
        "Human land-use and Land cover Maps/Human-land-use_land-cover-maps_elevation_1900CE,.csv": "e030f71b0ce285814847232c3553a41e3ec55fab1f90111c5ff2a7ddcfce2e53",
    }
    corrupt = next(
        authority
        for authority in FILE_AUTHORITIES
        if authority.variant.key == "all" and authority.period.key == "1000_bce"
    )
    assert corrupt.upstream_status == "known_corrupt_refused"
    assert corrupt.observed_valid_row_count == 437
    assert corrupt.observed_malformed_row_count == 1
