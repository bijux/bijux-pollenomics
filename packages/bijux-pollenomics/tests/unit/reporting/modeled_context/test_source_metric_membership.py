from __future__ import annotations

import csv
from io import TextIOWrapper
from typing import cast
from zipfile import ZipFile

from bijux_pollenomics.reporting.modeled_context.metric_families import (
    METRIC_FAMILIES,
    PANGAEA_METRIC_KEYS,
)
from tests.support.repository import REPOSITORY_ROOT


def _families() -> dict[str, dict[str, object]]:
    return {family.key: family.as_dict() for family in METRIC_FAMILIES}


def test_family_union_equals_exact_published_result_header() -> None:
    archive_path = REPOSITORY_ROOT / "data/landclim/raw/landclim_ii_reveals_results.zip"
    with ZipFile(archive_path) as archive:
        result_members = sorted(
            member
            for member in archive.namelist()
            if member.endswith(".csv")
            and (
                member.startswith("LANDCLIMII.RV.means.JUN2021/")
                or member.startswith("LANDCLIMII.RV.standarderrors.JUN2021/")
            )
        )
        headers = []
        for member in result_members:
            with archive.open(member) as handle:
                headers.append(
                    next(csv.reader(TextIOWrapper(handle, encoding="utf-8-sig")))
                )

    assert len(result_members) == 50
    assert all(
        tuple(header[:3]) == ("LCGRID_ID", "lonDD", "latDD") for header in headers
    )
    assert all(tuple(header[3:]) == PANGAEA_METRIC_KEYS for header in headers)
    assert len(PANGAEA_METRIC_KEYS) == len(set(PANGAEA_METRIC_KEYS)) == 47


def test_companion_mapping_preserves_source_labels_and_family_denominators() -> None:
    mapping_path = (
        REPOSITORY_ROOT / "data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv"
    )
    with mapping_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    families = _families()
    taxa = cast(list[dict[str, object]], families["exact_taxa"]["metrics"])
    pfts = cast(list[dict[str, object]], families["source_pft_codes"]["metrics"])
    land_cover_types = cast(
        list[dict[str, object]], families["source_land_cover_types"]["metrics"]
    )

    assert {metric["source_label"] for metric in taxa} == {row[4] for row in rows[1:]}
    mapped_pft_codes = [row[1] for row in rows[1:] if row[1]]
    assert [metric["key"] for metric in pfts if metric["key"] != "ISTS"] == (
        mapped_pft_codes
    )
    ists = next(metric for metric in pfts if metric["key"] == "ISTS")
    assert ists["definition"] is None
    assert str(ists["membership_evidence"]).endswith(
        "TW1.RV.estimates.jun21.csv#header"
    )
    mapped_lct_codes = [
        row[0].rsplit("(", 1)[1].removesuffix(")") for row in rows[1:] if row[0]
    ]
    assert [metric["key"] for metric in land_cover_types] == mapped_lct_codes
    assert [len(taxa), len(pfts), len(land_cover_types)] == [31, 13, 3]
